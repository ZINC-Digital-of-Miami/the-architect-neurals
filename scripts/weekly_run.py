#!/usr/bin/env python3
"""Durable weekly publication state; dispatch is never successful coverage."""
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import uuid
from zoneinfo import ZoneInfo

from repository import git, live_main, pull
from release import LIVE, file_hashes, public_bytes, utcnow
from preservation import digest

ZONE = ZoneInfo("America/Chicago")


def latest_due(now=None):
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(ZONE)
    sunday = now.date() - dt.timedelta(days=(now.weekday() + 1) % 7)
    due = dt.datetime.combine(sunday, dt.time(7), ZONE)
    if now < due:
        sunday -= dt.timedelta(days=7)
    return sunday


def pending(through, now=None):
    previous = dt.date.fromisoformat(through)
    if previous.weekday() != 6:
        raise ValueError("publication coverage must end on Sunday")
    result, due = [], latest_due(now)
    if previous > due:
        raise ValueError("publication coverage ends after the latest due Sunday")
    previous += dt.timedelta(days=7)
    while previous <= due:
        result.append(previous.isoformat())
        previous += dt.timedelta(days=7)
    return result


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("w") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    sync_directory(path.parent)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def remove_active(private):
    (private / "active.json").unlink()
    sync_directory(private)


@contextmanager
def transaction(root):
    private = root / ".architecture"
    private.mkdir(exist_ok=True)
    with (private / "transaction.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield private


def read(path):
    return json.loads(path.read_text())


def active(private, token):
    path = private / "active.json"
    if not path.exists():
        raise ValueError("no run owns the writer lock")
    data = read(path)
    if data["token"] != token:
        raise ValueError("writer token mismatch; do not alter another run")
    return data


def check_receipt(root, path, expected=None):
    receipt = read(path)
    if receipt.get("status") != "verified" or receipt.get("production") is not True:
        raise ValueError("only a verified production release can advance coverage")
    if live_main(root) != receipt["source_commit"]:
        raise ValueError("publication receipt is not current live main")
    files = receipt.get("files", {})
    if not files or "index.html" not in files or "src/MANIFEST.json" not in files or "release.json" not in files:
        raise ValueError("receipt lacks publication file proof")
    if expected is not None and {k: v for k, v in files.items() if k != "release.json"} != expected:
        raise ValueError("published artifact differs from the reviewed staged candidate")
    from urllib.parse import quote
    for name, sha in files.items():
        url = LIVE + ("/" if name == "index.html" else "/" + quote(name, safe="/"))
        if digest(public_bytes(url)) != sha:
            raise ValueError(f"live publication changed or missing: {name}")
    published = json.loads(public_bytes(LIVE + "/src/MANIFEST.json"))
    provenance = json.loads(public_bytes(LIVE + "/release.json"))
    if published["current_through"] != receipt["current_through"] or provenance["source_commit"] != receipt["source_commit"]:
        raise ValueError("manifest/provenance does not agree with receipt")
    if live_main(root) != receipt["source_commit"]:
        raise ValueError("live main changed during publication receipt verification")
    return receipt


def start(root):
    with transaction(root) as private:
        if (private / "active.json").exists():
            raise ValueError("exclusive writer lock already held; inspect status and resume the same run or explicitly fail it")
        if not (private / "publication.json").exists():
            raise ValueError("coverage uninitialized; bootstrap from a freshly verified production release receipt")
        published = read(private / "publication.json")
        queue = pending(published["current_through"])
        if not queue:
            return {"status": "current", "current_through": published["current_through"]}
        if git(root, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("repository has active edits; do not overwrite or start a competing publication")
        token = uuid.uuid4().hex
        attempt = private / "runs" / queue[0] / token
        data = {"version": 1, "token": token, "status": "acquiring", "started_at": utcnow(),
                "week_ending": queue[0], "window_after": published["current_through"],
                "candidate": str(attempt / "candidate"), "attempt": str(attempt), "events": []}
        save(private / "active.json", data)
        save(attempt / "run.json", data)
        try:
            data["source_commit"] = pull(root, attempt / "candidate")
            data["status"] = "researching"
        except Exception as exc:
            data.update({"status": "failed", "error": str(exc), "finished_at": utcnow()})
            save(attempt / "run.json", data)
            (private / "active.json").unlink()
            raise
        save(private / "active.json", data)
        save(attempt / "run.json", data)
        return data


def complete(root, private, data, receipt_path):
    """A persisted intent binds the token, exact receipt and before/after watermarks.

    Any interruption after intent creation is recovered by revalidating that same receipt
    and finishing the remaining writes. Advanced coverage alone is never treated as proof.
    """
    attempt = Path(data["attempt"])
    intent_path = attempt / "completion.json"
    try:
        if data["status"] not in {"ready_for_review", "completing", "published"} or not receipt_path:
            raise ValueError("stage and review a candidate before recording publication")
        previous = dt.date.fromisoformat(data["window_after"])
        ending = dt.date.fromisoformat(data["week_ending"])
        if previous.weekday() != 6 or ending != previous + dt.timedelta(days=7):
            raise ValueError("completion must cover exactly the next Sunday; intervals cannot be skipped")
        receipt = check_receipt(root, receipt_path, data["staged_files"])
        if receipt["current_through"] != data["week_ending"]:
            raise ValueError("receipt coverage differs from the owned weekly interval")
        receipt_digest = digest(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
        receipt_name = str(receipt_path.resolve())
        published = read(private / "publication.json")
        recovered = intent_path.exists()
        if recovered:
            intent = read(intent_path)
            if (intent["token"] != data["token"] or intent["receipt_digest"] != receipt_digest
                    or intent["receipt"] != receipt_name
                    or intent["completed_run"]["staged_files"] != data["staged_files"]
                    or intent["completed_run"]["week_ending"] != data["week_ending"]
                    or intent["completed_run"]["window_after"] != data["window_after"]):
                raise ValueError("completion recovery requires the same owner, staged artifact, interval and exact receipt")
        else:
            if data["status"] != "ready_for_review" or published["current_through"] != data["window_after"]:
                raise ValueError("coverage changed without this run's completion intent; reconciliation required")
            after = {"current_through": data["week_ending"], "source_commit": receipt["source_commit"],
                     "verified_at": utcnow(), "receipt": receipt_name, "token": data["token"],
                     "receipt_digest": receipt_digest}
            completed_run = {**data, "status": "published", "receipt": receipt_name,
                             "receipt_digest": receipt_digest, "finished_at": utcnow()}
            intent = {"version": 1, "token": data["token"], "receipt": receipt_name,
                      "receipt_digest": receipt_digest, "before": published, "after": after,
                      "completed_run": completed_run}
            save(intent_path, intent)
        if published != intent["before"] and published != intent["after"]:
            raise ValueError("publication state does not match this completion intent; do not overwrite another interval")
        active_path = private / "active.json"
        if active_path.exists():
            active(private, data["token"])
            save(active_path, {**data, "status": "completing", "completion_intent": str(intent_path)})
        elif published != intent["after"]:
            raise ValueError("writer ownership is missing before publication commit")
        if published == intent["before"]:
            save(private / "publication.json", intent["after"])
        save(attempt / "run.json", intent["completed_run"])
        if active_path.exists():
            remove_active(private)
        return {**intent["completed_run"], "idempotent_replay": recovered}
    except Exception as exc:
        # Retain recovery evidence even if writing run.json was the operation that failed.
        try:
            save(attempt / "completion-errors" / (uuid.uuid4().hex + ".json"),
                 {"at": utcnow(), "token": data["token"], "error": str(exc),
                  "receipt": str(receipt_path) if receipt_path else None})
        except OSError:
            pass
        raise


def mutate(root, action, token, note=None, receipt_path=None):
    with transaction(root) as private:
        if action == "complete" and not (private / "active.json").exists():
            attempts = list((private / "runs").glob(f"*/{token}/run.json")) if token and all(c in "0123456789abcdef" for c in token) else []
            if len(attempts) == 1 and read(attempts[0]).get("status") == "published":
                return complete(root, private, read(attempts[0]), receipt_path)
        data = active(private, token)
        if action == "complete":
            return complete(root, private, data, receipt_path)
        if (Path(data["attempt"]) / "completion.json").exists():
            raise ValueError("a pending verified completion must be recovered with complete before other mutations")
        candidate = Path(data["candidate"])
        if action == "ready":
            subprocess.run(["bash", "check.sh"], cwd=candidate, check=True)
            manifest = read(candidate / "site/src/MANIFEST.json")
            if manifest["current_through"] != data["week_ending"]:
                raise ValueError("candidate coverage must equal this oldest due Sunday, never a future date")
            if not (candidate / "src/briefs" / (data["week_ending"] + ".html")).is_file():
                raise ValueError("candidate lacks the dated brief")
            data.update({"status": "ready_for_review", "staged_files": file_hashes(candidate / "site"), "staged_at": utcnow()})
        elif action == "fail":
            if not note:
                raise ValueError("a failure/abandonment needs its exact reason")
            data.update({"status": "failed", "error": note, "finished_at": utcnow()})
        elif action == "record":
            if not note:
                raise ValueError("record needs a note")
            data["events"].append({"at": utcnow(), "note": note})
        save(Path(data["attempt"]) / "run.json", data)
        if action == "fail":
            remove_active(private)
        else:
            save(private / "active.json", data)
        return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["status", "bootstrap", "start", "ready", "record", "complete", "fail"])
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--token")
    p.add_argument("--note")
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    private = a.root / ".architecture"
    if a.action == "status":
        publication = read(private / "publication.json") if (private / "publication.json").exists() else None
        result = {"timezone": "America/Chicago", "due_time": "Sunday 07:00", "latest_due": latest_due().isoformat(),
                  "publication": publication, "pending": pending(publication["current_through"]) if publication else None,
                  "active": read(private / "active.json") if (private / "active.json").exists() else None}
    elif a.action == "bootstrap":
        if not a.receipt:
            p.error("bootstrap requires --receipt from the new verified production release")
        with transaction(a.root) as private:
            if (private / "publication.json").exists() or (private / "active.json").exists():
                raise ValueError("bootstrap cannot overwrite existing publication/run state")
            receipt = check_receipt(a.root, a.receipt)
            pending(receipt["current_through"])
            result = {"current_through": receipt["current_through"], "source_commit": receipt["source_commit"],
                      "verified_at": utcnow(), "receipt": str(a.receipt.resolve())}
            save(private / "publication.json", result)
    elif a.action == "start":
        result = start(a.root)
    else:
        if not a.token:
            p.error("mutating an existing run requires its --token")
        result = mutate(a.root, a.action, a.token, a.note, a.receipt)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
