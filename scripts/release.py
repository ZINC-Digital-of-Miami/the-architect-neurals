#!/usr/bin/env python3
"""Publish an isolated artifact from live GitHub main, then verify every public byte."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.parse import quote

from repository import extract_archive, git, live_main
from check_artifact import artifact_hashes

LIVE = "https://the-architecture-neurals.vercel.app"
TEAM = "zincdigitalofmiamis-projects"
PROJECT = "the-architecture"


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run(args, cwd=None):
    try:
        return subprocess.check_output(args, cwd=cwd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        token = os.environ.get("VERCEL_TOKEN")
        if token:
            detail = detail.replace(token, "[redacted]")
        raise RuntimeError(f"{args[0]} exited {exc.returncode}: {detail[:2000]}") from exc


def vc(args, cwd):
    # CLI reads its existing credential/session. Never serialize a credential.
    return run(["vercel", "--scope", TEAM, *args], cwd)


def file_hashes(site):
    return artifact_hashes(site, public_only=True)


def public_bytes(url):
    return run(["curl", "--fail", "--silent", "--show-error", "--location",
                "--max-time", "30", "--retry", "2", url])


def verify_files(site, base=LIVE, deployment=False):
    verified = {}
    for name, expected in file_hashes(site).items():
        path = "/" if name == "index.html" else "/" + quote(name, safe="/")
        raw = (vc(["curl", path, "--deployment", base, "--", "--fail", "--silent",
                   "--show-error", "--location", "--max-time", "30"], site)
               if deployment else public_bytes(base.rstrip("/") + path))
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"served bytes differ for {path}: expected {expected}, received {actual}")
        verified[name] = actual
    return verified


def validate_main(root):
    sha = live_main(root)
    if git(root, "rev-parse", "HEAD") != sha:
        raise ValueError("HEAD is not live GitHub main; land the reviewed change through the repository release path first")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("working tree has uncommitted/untracked files; never deploy unseen local changes")
    subprocess.run(["bash", "check.sh"], cwd=root, check=True)
    return sha


def validate_reviewed_artifact(site, owned_run):
    """Check committed upload bytes against the owner's staged weekly candidate."""
    if owned_run.get("status") != "ready_for_review" or not owned_run.get("staged_files"):
        raise ValueError("weekly publication requires a staged, reviewed candidate")
    if file_hashes(site) != owned_run["staged_files"]:
        raise ValueError("committed upload differs from the reviewed weekly candidate; restage and review before release")
    if json.loads((site / "src/MANIFEST.json").read_text())["current_through"] != owned_run["week_ending"]:
        raise ValueError("committed upload coverage differs from the owned weekly interval")


def publish(root, production, run_token=None):
    private = root / ".architecture"
    private.mkdir(exist_ok=True)
    with (private / "transaction.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active_path = private / "active.json"
        owned_run = json.loads(active_path.read_text()) if active_path.exists() else None
        if owned_run and owned_run["token"] != run_token:
            raise ValueError("another weekly run owns the single-writer lock; supply its exact --run-token only if you own it")
        if run_token and not owned_run:
            raise ValueError("no active weekly run owns this token")
        sha = validate_main(root)
        identity = vc(["whoami"], root).decode().strip()
        if identity != "zincdigitalofmiami":
            raise ValueError("Vercel CLI identity is not zincdigitalofmiami")
        receipt = {"version": 1, "source_commit": sha, "started_at": utcnow(),
                   "production": production, "status": "started"}
        receipts = private / "releases"
        receipts.mkdir(exist_ok=True)
        receipt_path = receipts / (dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
        try:
            with tempfile.TemporaryDirectory(prefix="architecture-release-") as temp:
                tree = Path(temp) / "artifact"
                extract_archive(root, sha, tree, "site")
                site = tree / "site"
                if owned_run:
                    validate_reviewed_artifact(site, owned_run)
                manifest = json.loads((site / "src/MANIFEST.json").read_text())
                receipt["current_through"] = manifest["current_through"]
                # This provenance is generated AFTER main exists, outside the tracked tree.
                (site / "release.json").write_text(json.dumps({"source_commit": sha,
                    "current_through": manifest["current_through"]}, sort_keys=True) + "\n")
                vc(["link", "--project", PROJECT, "--yes"], site)
                if live_main(root) != sha:
                    raise ValueError("live main moved before deployment; build a new reviewed release")
                args = ["deploy", "--yes", "--format=json", "--meta", f"gitCommitSha={sha}",
                        "--meta", f"architectureMainSha={sha}"]
                if production:
                    args += ["--prod", "--skip-domain"]
                response = json.loads(vc(args, site))
                deployment = response.get("deployment", response)
                url = deployment["url"]
                if not url.startswith("https://"):
                    url = "https://" + url
                receipt.update({"deployment_url": url, "deployment_id": deployment.get("id")})
                verified = verify_files(site, url, deployment=True)
                if live_main(root) != sha:
                    raise ValueError("live main moved after upload; unpromoted deployment retained for diagnosis")
                if production:
                    vc(["promote", url, "--yes"], site)
                    # A failed alias check never records successful publication.
                    for attempt in range(5):
                        try:
                            verified = verify_files(site)
                            break
                        except (ValueError, RuntimeError):
                            if attempt == 4:
                                raise
                            time.sleep(5)
                    if live_main(root) != sha:
                        raise ValueError("live main moved during publication verification; receipt requires reconciliation")
                receipt.update({"status": "verified", "verified_at": utcnow(), "files": verified})
        except Exception as exc:
            receipt.update({"status": "failed", "failed_at": utcnow(), "error": str(exc)})
            raise
        finally:
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
            print(f"RELEASE_RECEIPT={receipt_path}")
        return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prod", action="store_true")
    p.add_argument("--preview", action="store_true")
    p.add_argument("--no-build", action="store_true", help="compatibility: releases always upload committed output without rebuilding")
    p.add_argument("--run-token")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    if a.prod and a.preview:
        p.error("choose production or preview")
    print(json.dumps(publish(a.root, a.prod, a.run_token), indent=2))
