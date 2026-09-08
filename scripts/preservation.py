#!/usr/bin/env python3
"""Content preservation gates. Only Python's standard library is required."""
import argparse
import collections
import datetime as dt
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CorrectionBlocks(HTMLParser):
    """Keep original HTML bytes, including nested divs and entity spelling."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text, self.blocks, self.depth, self.start = text, [], 0, None
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.feed(text)
        if self.depth:
            raise ValueError("unclosed correction block")

    def position(self):
        line, col = self.getpos()
        return self.offsets[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif "correction" in dict(attrs).get("class", "").split():
                self.depth, self.start = 1, self.position()

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1
            if not self.depth:
                end = self.text.index(">", self.position()) + 1
                self.blocks.append(self.text[self.start:end])


def corrections(root):
    text = (root / "src/update_part2.html").read_bytes().decode("utf-8")
    start = text.index('id="u-corrections"')
    end = text.index('id="u-silence"', start)
    return CorrectionBlocks(text[start:end]).blocks


def snapshot(root, source_ref, verify_git=True):
    paths = ["src/master_report.md", "src/sources_manifest.md"]
    paths += sorted(str(p.relative_to(root)) for p in (root / "src/briefs").glob("[0-9]*.html"))
    immutable = {}
    for name in paths:
        raw = (root / name).read_bytes()
        # The frozen edition must be traceable to this exact repository commit.
        original = subprocess.check_output(["git", "show", f"{source_ref}:{name}"], cwd=root) if verify_git else raw
        if raw != original:
            raise ValueError(f"cannot freeze modified protected source: {name}")
        immutable[name] = {"sha256": digest(raw), "bytes": len(raw)}
    for name in ("src/update_part2.html", "src/map_source.json"):
        if verify_git and (root / name).read_bytes() != subprocess.check_output(["git", "show", f"{source_ref}:{name}"], cwd=root):
            raise ValueError(f"cannot freeze modified protected source: {name}")
    return {"version": 1, "source_commit": source_ref,
            "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "immutable_files": immutable, "corrections": corrections(root),
            "map": json.loads((root / "src/map_source.json").read_text())}


def validate(root, baseline):
    errors = []
    for name, original in baseline["immutable_files"].items():
        path = root / name
        if not path.is_file() or digest(path.read_bytes()) != original["sha256"]:
            errors.append(f"protected source changed or missing: {name}")
    try:
        current = corrections(root)
        old = baseline["corrections"]
        if current[:len(old)] != old:
            errors.append("existing correction HTML changed, removed, reordered or inserted before existing entries")
        seen = {re.search(r"\bC-\d{3,}\b", block).group() for block in old}
        for block in current[len(old):]:
            stamp = re.search(r"\b\d{4}-\d{2}-\d{2}\b", block)
            identity = re.search(r"\bC-\d{3,}\b", block)
            if not stamp or not identity:
                errors.append("new correction/context needs an ISO date and correction ID")
                continue
            try:
                dt.date.fromisoformat(stamp.group())
            except ValueError:
                errors.append("new correction/context has an invalid date")
            label = identity.group()
            if label in seen and "context added" not in block.lower():
                errors.append(f"duplicate correction {label} must be a separately dated context added block")
            if label not in seen and int(label[2:]) != max(int(x[2:]) for x in seen) + 1:
                errors.append(f"new correction {label} is not the next sequential ID")
            seen.add(label)
    except (ValueError, OSError) as exc:
        errors.append(f"corrections invalid: {exc}")
    try:
        now = json.loads((root / "src/map_source.json").read_text())
        old = baseline["map"]
        for identity, record in old["nodes"].items():
            if now["nodes"].get(identity) != record:
                errors.append(f"historical map node changed or missing: {identity}; add a versioned registry record instead")
        key = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"))
        before = collections.Counter(map(key, old["edges"]))
        after = collections.Counter(map(key, now["edges"]))
        for edge, count in before.items():
            if after[edge] < count:
                errors.append(f"historical map edge/grade changed or missing: {edge}")
        for edge in now["edges"]:
            if len(edge) != 4 or edge[0] not in now["nodes"] or edge[1] not in now["nodes"] or edge[2] not in {"A", "B", "C", "O"}:
                errors.append(f"invalid map edge: {edge}")
        if now["current"] < old["current"]:
            errors.append("map evidence date moved backward")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(f"map invalid: {exc}")
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["check", "freeze"])
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--baseline", type=Path)
    p.add_argument("--source-ref")
    a = p.parse_args()
    target = a.baseline or a.root / "preservation/baseline.json"
    if a.action == "freeze":
        if not a.source_ref or not re.fullmatch(r"[a-f0-9]{40}", a.source_ref):
            p.error("freeze requires an explicit full --source-ref; never replace an existing baseline")
        data = snapshot(a.root, a.source_ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x") as out:
            json.dump(data, out, indent=2, ensure_ascii=False)
            out.write("\n")
        print(f"Frozen {len(data['immutable_files'])} files, {len(data['corrections'])} corrections, "
              f"{len(data['map']['nodes'])} nodes and {len(data['map']['edges'])} edges")
    else:
        data = json.loads(target.read_text())
        errors = validate(a.root, data)
        if errors:
            raise SystemExit("PRESERVATION FAILED:\n" + "\n".join(errors))
        print(f"PRESERVED: {len(data['immutable_files'])} files; {len(data['corrections'])} original correction blocks; "
              f"{len(data['map']['nodes'])} nodes; {len(data['map']['edges'])} edges")


if __name__ == "__main__":
    main()
