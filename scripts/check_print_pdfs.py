#!/usr/bin/env python3
"""Validate that every printable route has a current, intact static PDF."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote


CANONICAL_ORIGIN = "https://the-architecture-neurals.vercel.app"
MANIFEST_PATH = Path("site/print/manifest.json")
ARTIFACT_KEYS = {"kind", "route", "url", "canonicalUrl", "output", "title", "pages", "sha256", "bytes"}
ROUTE_KEYS = {"url", "title", "pages", "kind", "sha256", "bytes"}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def source_fingerprint(root):
    inputs = []
    site = root / "site"
    for path in sorted(site.rglob("*")):
        if path.name == ".DS_Store" or path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "site/print" or relative.startswith("site/print/"):
            continue
        raw = path.read_bytes()
        inputs.append({"path": relative, "sha256": sha256(raw), "bytes": len(raw)})
    builder = root / "scripts/build_print_pdfs.cjs"
    if builder.is_file() and not builder.is_symlink():
        raw = builder.read_bytes()
        inputs.append({"path": "scripts/build_print_pdfs.cjs", "sha256": sha256(raw), "bytes": len(raw)})
    inputs.sort(key=lambda item: item["path"])
    aggregate = "".join(f'{item["path"]}\0{item["sha256"]}\0{item["bytes"]}\n' for item in inputs).encode()
    return {"algorithm": "sha256", "value": sha256(aggregate), "inputs": inputs}


def _encode(value):
    return quote(value, safe="-_.!~*'()")


def expected_routes(root):
    """Derive the routes that the shipped print control can request from rendered output."""
    site = root / "site"
    expected = {}
    for path in sorted(site.rglob("*.html")):
        if "print" in path.relative_to(site).parts or b'/site-ui.js' not in path.read_bytes():
            continue
        route = "/" + path.relative_to(site).as_posix()
        expected[route] = "page"

    map_data = json.loads((site / "map/data.json").read_text())
    for identity in sorted(map_data["nodes"]):
        expected[f"/neural.html?entity={_encode(identity)}"] = "map-entity"

    research = json.loads((site / "research/data.json").read_text())
    for topic in research["topics"]:
        expected[f'/neural.html?topic={_encode(topic["id"])}'] = "map-topic"

    synthesis = (site / "synthesis.html").read_text()
    views = re.findall(r'\bdata-view-tab="([^"]+)"', synthesis)
    for view in views:
        expected[f"/synthesis.html?view={_encode(view)}"] = "synthesis"
    return expected


def validate(root, required=True):
    root = Path(root)
    path = root / MANIFEST_PATH
    if not path.is_file():
        return ["print PDF manifest missing: site/print/manifest.json"] if required else []
    errors = []
    try:
        manifest = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"print PDF manifest unreadable: {exc}"]

    if manifest.get("schemaVersion") != 1:
        errors.append("print PDF manifest schemaVersion must be 1")
    if manifest.get("canonicalOrigin") != CANONICAL_ORIGIN:
        errors.append(f"print PDF canonicalOrigin must be {CANONICAL_ORIGIN}")
    if not isinstance(manifest.get("generatedAt"), str) or not manifest["generatedAt"]:
        errors.append("print PDF manifest generatedAt is missing")
    actual_fingerprint = source_fingerprint(root)
    if manifest.get("sourceFingerprint") != actual_fingerprint:
        errors.append("print PDFs are stale: rendered source fingerprint differs")

    try:
        expected = expected_routes(root)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"print route coverage could not be derived from rendered sources: {exc}")
        expected = {}
    routes = manifest.get("routes")
    artifacts = manifest.get("artifacts")
    if not isinstance(routes, dict):
        errors.append("print PDF manifest routes must be an object")
        routes = {}
    if not isinstance(artifacts, list):
        errors.append("print PDF manifest artifacts must be an array")
        artifacts = []

    expected_set, route_set = set(expected), set(routes)
    for route in sorted(expected_set - route_set):
        errors.append(f"print PDF route missing: {route}")
    for route in sorted(route_set - expected_set):
        errors.append(f"unexpected print PDF route: {route}")

    artifacts_by_route = {}
    expected_files = {path}
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict) or set(item) != ARTIFACT_KEYS:
            errors.append(f"print PDF artifact {index} has invalid fields")
            continue
        route = item["route"]
        if route in artifacts_by_route:
            errors.append(f"duplicate print PDF artifact route: {route}")
            continue
        artifacts_by_route[route] = item
        if expected.get(route) != item["kind"]:
            errors.append(f"print PDF kind differs from expected route: {route}")
        if item["canonicalUrl"] != CANONICAL_ORIGIN + route:
            errors.append(f"print PDF canonicalUrl differs from route: {route}")
        output = Path(item["output"])
        if output.is_absolute() or ".." in output.parts or len(output.parts) != 3 or output.parts[:2] != ("site", "print") or output.suffix != ".pdf":
            errors.append(f"unsafe print PDF output: {item['output']}")
            continue
        pdf = root / output
        expected_files.add(pdf)
        expected_url = "/" + output.relative_to("site").as_posix()
        if item["url"] != expected_url or not re.fullmatch(r"/print/[A-Za-z0-9._-]+\.pdf", item["url"]):
            errors.append(f"print PDF URL differs from output: {route}")
        if not isinstance(item["title"], str) or not item["title"].strip():
            errors.append(f"print PDF title missing: {route}")
        if not isinstance(item["pages"], int) or isinstance(item["pages"], bool) or item["pages"] < 1:
            errors.append(f"print PDF page count invalid: {route}")
        if not pdf.is_file() or pdf.is_symlink():
            errors.append(f"print PDF file missing: {item['output']}")
            continue
        raw = pdf.read_bytes()
        if not raw.startswith(b"%PDF-") or not raw.rstrip().endswith(b"%%EOF"):
            errors.append(f"print PDF file signature invalid: {item['output']}")
        if item["bytes"] != len(raw) or item["sha256"] != sha256(raw):
            errors.append(f"print PDF bytes/hash mismatch: {item['output']}")

    for route in sorted(expected_set - set(artifacts_by_route)):
        errors.append(f"print PDF artifact missing: {route}")
    for route, record in routes.items():
        item = artifacts_by_route.get(route)
        if not isinstance(record, dict) or set(record) != ROUTE_KEYS:
            errors.append(f"print PDF route record has invalid fields: {route}")
        elif item and record != {key: item[key] for key in ROUTE_KEYS}:
            errors.append(f"print PDF route record differs from artifact: {route}")

    print_root = root / "site/print"
    actual_files = {p for p in print_root.rglob("*") if p.is_file() or p.is_symlink()} if print_root.is_dir() else set()
    for extra in sorted(actual_files - expected_files):
        errors.append(f"unexpected print PDF asset: {extra.relative_to(root).as_posix()}")
    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    issues = validate(root, required=True)
    if issues:
        raise SystemExit("PRINT PDF FAILED:\n" + "\n".join(issues))
    print("PRINT PDF: current source fingerprint, route coverage, bytes and hashes passed")
