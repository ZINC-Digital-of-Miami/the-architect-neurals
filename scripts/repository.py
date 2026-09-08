"""Exact-main acquisition; no alternate repository or deployment-as-source fallback."""
import io
import json
from pathlib import Path
import subprocess
import tarfile
from preservation import snapshot

ORIGINS = {"https://github.com/ZINC-Digital-of-Miami/the-architect-neurals.git",
           "https://github.com/ZINC-Digital-of-Miami/the-architect-neurals",
           "git@github.com:ZINC-Digital-of-Miami/the-architect-neurals.git"}


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def live_main(root):
    if git(root, "remote", "get-url", "origin") not in ORIGINS:
        raise ValueError("origin is not the authorized ZINC-Digital-of-Miami repository")
    rows = git(root, "ls-remote", "--exit-code", "origin", "refs/heads/main").splitlines()
    if len(rows) != 1:
        raise ValueError("live main did not resolve uniquely")
    sha, ref = rows[0].split()
    if ref != "refs/heads/main" or len(sha) != 40:
        raise ValueError("invalid live main response")
    return sha


def extract_archive(root, sha, destination, prefix=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    args = ["git", "archive", "--format=tar", sha]
    if prefix:
        args.append(prefix)
    raw = subprocess.check_output(args, cwd=root)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive.getmembers():
            name = Path(item.name)
            if name.is_absolute() or ".." in name.parts or item.issym() or item.islnk():
                raise ValueError(f"unsafe repository archive entry: {name}")
            if not (item.isdir() or item.isfile()):
                raise ValueError(f"unsupported archive entry: {name}")
        archive.extractall(destination, filter="data")


def pull(root, destination):
    sha = live_main(root)
    subprocess.run(["git", "fetch", "--no-tags", "origin", sha], cwd=root, check=True)
    if live_main(root) != sha:
        raise ValueError("live main changed during acquisition; retry in a new candidate directory")
    extract_archive(root, sha, destination)
    candidate = Path(destination)
    private = candidate / ".architecture"
    private.mkdir(exist_ok=True)
    baseline = snapshot(candidate, sha, verify_git=False)
    (private / "base-preservation.json").write_text(json.dumps(baseline, indent=2) + "\n")
    (private / "source.json").write_text(json.dumps({"source_commit": sha, "authority": "live GitHub main"}, indent=2) + "\n")
    registry = candidate / "src/research_registry.json"
    if registry.is_file():
        (private / "base-registry.json").write_bytes(registry.read_bytes())
    manifest = candidate / "site/src/MANIFEST.json"
    if manifest.is_file():
        (private / "base-manifest.json").write_bytes(manifest.read_bytes())
    return sha


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination", type=Path)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    print(json.dumps({"source_commit": pull(a.root, a.destination), "candidate": str(a.destination.resolve())}))
