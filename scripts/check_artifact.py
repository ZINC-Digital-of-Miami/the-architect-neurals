#!/usr/bin/env python3
"""Compare the whole generated artifact with an isolated rebuild of current sources."""
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from check_print_pdfs import MANIFEST_PATH as PRINT_MANIFEST_PATH, validate as validate_print_pdfs

ROOT = Path(__file__).resolve().parents[1]
ROOT_INPUTS = ("AGENT_INSTRUCTIONS.md", "AUTOMATED_RUN_TASK.md", "check.sh", "deploy.sh", "pull_src.sh",
               "scripts/build_print_pdfs.cjs")


def artifact_hashes(site, public_only=False, exclude_print=False):
    """Only exact CLI-local metadata is exempt; unknown files/configuration must fail."""
    result = {}
    for path in sorted(site.rglob("*")):
        name = path.relative_to(site).as_posix()
        if exclude_print and (name == "print" or name.startswith("print/")):
            continue
        if name == ".vercel" or name.startswith(".vercel/"):
            continue
        if path.is_symlink():
            raise ValueError(f"artifact symlink is not permitted: {name}")
        if not path.is_file():
            continue
        if name == ".gitignore":
            if path.read_bytes().strip() != b".vercel":
                raise ValueError("site/.gitignore may contain only the Vercel CLI's .vercel exclusion")
            continue
        if public_only and name == "vercel.json":
            continue
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_inputs(root):
    """Snapshot build inputs from source, never from a possibly tampered output manifest."""
    inputs = {}
    for path in sorted((root / "src").rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"source symlink is not permitted: {path.relative_to(root)}")
        if path.is_file():
            inputs[path.relative_to(root).as_posix()] = path.read_bytes()
    for name in ROOT_INPUTS:
        path = root / name
        if path.is_symlink():
            raise ValueError(f"source symlink is not permitted: {name}")
        if path.is_file():
            inputs[name] = path.read_bytes()
    return inputs


def rebuild_hashes(inputs):
    """All builders write inside a temporary copy, including generated src intermediates."""
    with tempfile.TemporaryDirectory(prefix="architecture-artifact-check-") as temp:
        scratch = Path(temp)
        for name, raw in inputs.items():
            output = scratch / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)
        env = os.environ.copy()
        env.pop("ARCH_SITE_URL", None)
        env.update({"ARCH_ROOT": str(scratch / "src"), "ARCH_DIST": str(scratch / "site"),
                    "PYTHONDONTWRITEBYTECODE": "1"})
        for command in (["node", "src/build_neural_map.js"], [sys.executable, "src/build_site3.py"]):
            completed = subprocess.run(command, cwd=scratch, env=env, capture_output=True, text=True)
            if completed.returncode:
                raise ValueError(f"isolated {' '.join(command)} failed: {completed.stderr.strip()[-2000:]}")
        return artifact_hashes(scratch / "site")


def check_rebuild(root):
    inputs = source_inputs(root)
    all_actual = artifact_hashes(root / "site")
    print_manifest = root / PRINT_MANIFEST_PATH
    exclude_print = print_manifest.is_file() and not validate_print_pdfs(root, required=False)
    actual = artifact_hashes(root / "site", exclude_print=exclude_print)
    expected = rebuild_hashes(inputs)
    errors = []
    if source_inputs(root) != inputs:
        errors.append("source inputs changed during isolated rebuild; rerun after the writer finishes")
    if artifact_hashes(root / "site") != all_actual:
        errors.append("generated artifact changed during isolated rebuild; rerun after the writer finishes")
    errors += [f"generated artifact missing: {name}" for name in sorted(expected.keys() - actual.keys())]
    errors += [f"unexpected generated artifact: {name}" for name in sorted(actual.keys() - expected.keys())]
    errors += [f"generated artifact differs from current source rebuild: {name}"
               for name in sorted(actual.keys() & expected.keys()) if actual[name] != expected[name]]
    return errors


def check(root, require_print=False):
    errors = []
    site = root / "site"
    manifest = json.loads((site / "src/MANIFEST.json").read_text())
    for item in manifest["files"]:
        name = Path(item["path"])
        if name.is_absolute() or ".." in name.parts or ".architecture" in name.parts:
            errors.append(f"unsafe source export: {name}")
            continue
        exported = site / "src" / name
        original = root / "src" / name
        if not original.is_file():
            original = root / name
        if not exported.is_file() or not original.is_file():
            errors.append(f"source export/original missing: {name}")
            continue
        raw = original.read_bytes()
        if raw != exported.read_bytes() or hashlib.sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            errors.append(f"stale or altered source export: {name}")
    if (site / "styles.css").read_bytes() != (root / "src/final.css").read_bytes():
        errors.append("site/styles.css differs from src/final.css")
    source = json.loads((root / "src/map_source.json").read_text())
    data = json.loads((site / "map/data.json").read_text())
    if set(source["nodes"]) != set(data["nodes"]) or source["current"] != data["current"]:
        errors.append("rendered map identities/date differ from source")
    old_edges = collections.Counter(tuple(e) for e in source["edges"])
    rendered = collections.Counter((e["s"], e["t"], e["g"], e["l"]) for e in data["edges"])
    if old_edges != rendered:
        errors.append("rendered map edges/grades/labels differ from source")
    for identity, node in source["nodes"].items():
        target = data["nodes"].get(identity, {})
        if node.get("name", "") != target.get("name", "") or node.get("sub", "") != target.get("sub", ""):
            errors.append(f"rendered map dossier differs: {identity}")
    briefs = sorted(p.stem for p in (root / "src/briefs").glob("[0-9]*.html"))
    if not briefs or manifest["current_through"] != briefs[-1] or manifest["counts"]["briefs"] != len(briefs):
        errors.append("manifest coverage/count does not match source briefs")
    previous = root / ".architecture/base-manifest.json"
    if previous.is_file():
        before = json.loads(previous.read_text())
        for key in ("corrections", "clocks", "map_nodes", "map_edges", "briefs"):
            if manifest["counts"][key] < before["counts"][key]:
                errors.append(f"prior publication {key} count decreased")
        if manifest["counts"]["briefs"] > before["counts"]["briefs"] + 1:
            errors.append("a candidate cannot collapse multiple missed weekly briefs into one run")
        if manifest["current_through"] < before["current_through"]:
            errors.append("published coverage moved backward")
    errors.extend(validate_print_pdfs(root, required=require_print))
    errors.extend(check_rebuild(root))
    return errors


if __name__ == "__main__":
    issues = check(ROOT, require_print=True)
    if issues:
        raise SystemExit("ARTIFACT FAILED:\n" + "\n".join(issues))
    print("ARTIFACT: all generated paths/bytes match an isolated current-source rebuild; source/map/coverage checks passed")
