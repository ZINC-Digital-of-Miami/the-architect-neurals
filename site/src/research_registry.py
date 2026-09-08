#!/usr/bin/env python3
"""Validate the public research registry and prepare reviewable retrieval candidates.

The local matcher learns terms from explicitly accepted/rejected topic-fit feedback. It does not
verify claims, change evidence grades or run a trained political forecasting model.
Semantic discovery and original-source review belong to the scheduled researcher.
"""
import argparse
import copy
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRIMARY = {"court", "official_record", "party_statement", "pool_report", "historical_reference", "corporate_filing"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    if path.exists():
        if read_json(path) == data:
            return
        raise ValueError(f"Candidate already exists: {path}; choose a new candidate path")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def valid_date(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field}: date must be YYYY-MM-DD")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError(value)
    except ValueError as exc:
        raise ValueError(f"{field}: invalid date {value!r}") from exc


def valid_source_url(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Source URL contains whitespace or invalid characters")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Source URL must use credential-free HTTPS")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Source URL has an invalid port") from exc
    return parsed


def validate(data, map_data=None):
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported research schema")
    valid_date(data.get("updatedAt"), "updatedAt")
    tables = {}
    for key in ("categories", "topics", "sources", "claims", "comparisons", "watchpoints", "feedback", "topicProposals", "revisions", "networkPaths"):
        rows = data.get(key, [] if key == "networkPaths" else None)
        if not isinstance(rows, list):
            raise ValueError(f"{key} must be an array")
        table = {}
        for row in rows:
            ident = row.get("id", "")
            if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in table:
                raise ValueError(f"Invalid or duplicate {key} id: {ident!r}")
            table[ident] = row
        tables[key] = table

    def refs(row, field, target, required=False):
        values = row.get(field, [])
        if not isinstance(values, list) or (required and not values):
            raise ValueError(f"{row['id']}: invalid {field}")
        if len(values) != len(set(values)) or any(x not in target for x in values):
            raise ValueError(f"{row['id']}: unknown or repeated {field}")

    map_nodes = set(map_data.get("nodes", {})) if map_data else None
    for topic in tables["topics"].values():
        for field in ("title", "description"):
            if not isinstance(topic.get(field), str) or not topic[field].strip():
                raise ValueError(f"{topic['id']}: missing {field}")
        refs(topic, "categoryIds", tables["categories"], True)
        if map_nodes is not None:
            refs(topic, "entityIds", map_nodes)
        if topic.get("status") not in {"active", "watching", "new", "dormant"}:
            raise ValueError(f"{topic['id']}: invalid topic status")
        valid_date(topic.get("createdAt"), topic["id"] + ".createdAt")
        valid_date(topic.get("updatedAt"), topic["id"] + ".updatedAt")
        if topic["updatedAt"] < topic["createdAt"]:
            raise ValueError(f"{topic['id']}: update precedes creation")
        for link in topic.get("reportLinks", []):
            href = link.get("href", "")
            if not href.startswith("/") or href.startswith("//") or "\\" in href or any(ord(c) < 32 for c in href):
                raise ValueError(f"{topic['id']}: invalid internal report link")
    for source in tables["sources"].values():
        valid_source_url(source.get("url", ""))
        for field in ("title", "publisher", "originId"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"{source['id']}: missing {field}")
        if source.get("sourceType") not in PRIMARY | {"reporting"}:
            raise ValueError(f"{source['id']}: invalid source type")
        valid_date(source.get("accessedAt"), source["id"] + ".accessedAt")
        if source.get("publishedAt"):
            valid_date(source["publishedAt"], source["id"] + ".publishedAt")
            if source["accessedAt"] < source["publishedAt"]:
                raise ValueError(f"{source['id']}: access precedes publication")
    for key in ("claims", "comparisons", "watchpoints"):
        for row in tables[key].values():
            refs(row, "topicIds", tables["topics"], True)
            refs(row, "sourceIds", tables["sources"], key == "claims")
            if map_nodes is not None and "entityIds" in row:
                refs(row, "entityIds", map_nodes)
            for field in ("eventDate", "reviewedAt", "lastCheckedAt", "createdAt"):
                if row.get(field):
                    valid_date(row[field], row["id"] + "." + field)
    for claim in tables["claims"].values():
        if claim.get("status") not in {"documented", "lead", "disputed", "superseded"}:
            raise ValueError(f"{claim['id']}: invalid claim status")
        if not claim.get("text") or not claim.get("context") or not claim.get("recordType"):
            raise ValueError(f"{claim['id']}: statement, context and record type are required")
        records = [tables["sources"][s] for s in claim["sourceIds"]]
        if claim["status"] == "documented" and not any(s["sourceType"] in PRIMARY for s in records):
            if len({s["originId"] for s in records}) < 2:
                raise ValueError(f"{claim['id']}: single-origin reporting remains a research lead")
        if claim.get("supersedes"):
            if claim["supersedes"] not in tables["claims"] or claim["supersedes"] == claim["id"]:
                raise ValueError(f"{claim['id']}: invalid superseded claim")
            chain, current = {claim["id"]}, claim
            while current.get("supersedes"):
                parent = current["supersedes"]
                if parent in chain:
                    raise ValueError(f"{claim['id']}: cyclic supersession")
                chain.add(parent)
                current = tables["claims"].get(parent, {})
    for feedback in tables["feedback"].values():
        if feedback.get("decision") not in {"accept", "reject"} or not feedback.get("reason"):
            raise ValueError(f"{feedback['id']}: feedback needs decision and reason")
        if feedback.get("purpose", "topic_fit") not in {"topic_fit", "source_route", "evidence_review"}:
            raise ValueError(f"{feedback['id']}: invalid feedback purpose")
        refs(feedback, "topicIds", tables["topics"], True)
        valid_date(feedback.get("date"), feedback["id"] + ".date")
    for revision in tables["revisions"].values():
        refs(revision, "claimIds", tables["claims"])
        refs(revision, "topicIds", tables["topics"])
        refs(revision, "pathIds", tables["networkPaths"])
        valid_date(revision.get("date"), revision["id"] + ".date")
    edge_indices = set()
    for relation in data.get("relationships", []):
        edge_index = relation.get("mapEdgeIndex")
        if type(edge_index) is not int or edge_index < 0 or edge_index in edge_indices or (map_data and edge_index >= len(map_data["edges"])):
            raise ValueError("Unknown map relationship index")
        edge_indices.add(edge_index)
        refs({"id": "map relationship", **relation}, "sourceIds", tables["sources"], True)
        refs({"id": "map relationship", **relation}, "claimIds", tables["claims"])
    mappings = {r["mapEdgeIndex"]: r for r in data.get("relationships", [])}
    for path in tables["networkPaths"].values():
        refs(path, "topicIds", tables["topics"], True)
        for field in ("title", "summary", "context", "nextCheck"):
            if not isinstance(path.get(field), str) or not path[field].strip():
                raise ValueError(f"{path['id']}: missing {field}")
        valid_date(path.get("reviewedAt"), path["id"] + ".reviewedAt")
        nodes, indices = path.get("entityIds"), path.get("edgeIndices")
        if (not isinstance(nodes, list) or len(nodes) < 2 or any(not isinstance(n, str) for n in nodes)
                or len(set(nodes)) != len(nodes) or not isinstance(indices, list) or len(indices) != len(nodes) - 1):
            raise ValueError(f"{path['id']}: invalid connection path")
        if map_nodes is not None:
            refs(path, "entityIds", map_nodes, True)
        for position, index in enumerate(indices):
            if type(index) is not int or index not in mappings:
                raise ValueError(f"{path['id']}: path requires a sourced relationship for every step")
            claims = mappings[index].get("claimIds", [])
            if not claims or any(tables['claims'][c]['status'] != 'documented' for c in claims):
                raise ValueError(f"{path['id']}: path requires current documented claims")
            if map_data:
                edge = map_data['edges'][index]
                if set(edge[:2]) != set(nodes[position:position + 2]) or edge[2] not in {'A', 'B'}:
                    raise ValueError(f"{path['id']}: disconnected or unsupported path step")
    return tables


def validate_transition(previous, candidate, map_data=None):
    """Current views may supersede a record; the old statement remains addressable."""
    old = validate(previous, map_data)
    new = validate(candidate, map_data)
    for key in ("sources", "claims", "feedback", "revisions"):
        for ident, row in old[key].items():
            if ident not in new[key]:
                raise ValueError(f"Cannot delete historical {key} record {ident}")
            incoming = new[key][ident]
            for field, value in row.items():
                if key == "claims" and field == "status" and value != "superseded" and incoming.get(field) == "superseded":
                    if not any(cid not in old["claims"] and c.get("supersedes") == ident for cid, c in new["claims"].items()):
                        raise ValueError(f"{ident}: supersession requires a replacement claim")
                    continue
                if key == "sources" and field == "accessedAt":
                    continue
                if incoming.get(field) != value:
                    raise ValueError(f"Cannot rewrite historical {key} record {ident}.{field}; append a new record")
    appended_revisions = [r for ident, r in new["revisions"].items() if ident not in old["revisions"]]
    for collection in ("comparisons", "watchpoints", "topicProposals", "categories", "networkPaths"):
        for ident, row in old[collection].items():
            if ident not in new[collection]:
                raise ValueError(f"Cannot delete historical {collection} record {ident}")
            incoming = new[collection][ident]
            if incoming != row and not any(
                change.get("collection") == collection and change.get("id") == ident
                and change.get("before") == row and change.get("after") == incoming and change.get("reason")
                for revision in appended_revisions for change in revision.get("changes", [])
            ):
                raise ValueError(f"{ident}: changes require a dated revision retaining before and after records")
    for ident, topic in old["topics"].items():
        if ident not in new["topics"]:
            raise ValueError(f"Retain old topic identity {ident}; mark it dormant instead")
        incoming = new["topics"][ident]
        if incoming != topic and not any(
            ident in revision.get("topicIds", []) and any(
                change.get("collection") == "topics" and change.get("id") == ident
                and change.get("before") == topic and change.get("after") == incoming and change.get("reason")
                for change in revision.get("changes", [])
            ) for revision in appended_revisions
        ):
            raise ValueError(f"{ident}: topic changes require a dated revision retaining before and after records")
    for ident in new["claims"]:
        if ident not in old["claims"] and not any(ident in r.get("claimIds", []) for r in appended_revisions):
            raise ValueError(f"{ident}: new claim requires a dated revision")
    return new


def terms(text):
    return set(re.findall(r"[^\W_]{3,}", str(text).lower(), re.UNICODE))


def suggest(data, document):
    """Rank topic retrieval candidates internally, never people or political outcomes."""
    validate(data)
    if not all(document.get(k) for k in ("url", "title", "summary")):
        raise ValueError("Candidate document needs url, title and summary")
    valid_source_url(document["url"])
    words = terms(document["title"] + " " + document["summary"])
    matches = []
    for topic in data["topics"]:
        vocabulary = terms(" ".join([topic["title"], *topic.get("keywords", [])]))
        weight = len(words & vocabulary)
        for feedback in data["feedback"]:
            if feedback.get("purpose", "topic_fit") == "topic_fit" and topic["id"] in feedback["topicIds"]:
                overlap = len(words & terms(feedback.get("exampleText", "")))
                weight += overlap if feedback["decision"] == "accept" else -overlap
        if weight > 0:
            matches.append((weight, topic["id"]))
    matches.sort(key=lambda item: (-item[0], item[1]))
    digest = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
    return {"id": "candidate-" + digest[:20], "document": document,
            "topicIds": [ident for _, ident in matches[:6]], "requiresReview": True,
            "discoveryMethod": "Term matching with recorded feedback; source verification pending",
            "newTopicQuestion": "Does this source warrant a new topic?" if not matches else None,
            "createdAt": datetime.now(timezone.utc).isoformat()}


def feedback_candidate(data, proposal, decision, reason, topic_ids):
    candidate = copy.deepcopy(data)
    if not reason.strip() or not topic_ids:
        raise ValueError("Feedback requires a reason and explicit topic IDs")
    document = proposal.get("document", {})
    topic_ids = sorted(set(topic_ids))
    identity = json.dumps([proposal["id"], decision, reason, topic_ids], ensure_ascii=False)
    record = {"id": "feedback-" + hashlib.sha256(identity.encode()).hexdigest()[:20],
              "purpose": "topic_fit",
              "proposalId": proposal["id"], "decision": decision, "reason": reason,
              "topicIds": topic_ids, "exampleText": document.get("title", "") + " " + document.get("summary", ""),
              "date": date.today().isoformat()}
    if record["id"] not in {r["id"] for r in candidate["feedback"]}:
        candidate["feedback"].append(record)
    candidate["updatedAt"] = date.today().isoformat()
    validate_transition(data, candidate)
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "queue", "suggest", "feedback"))
    parser.add_argument("--registry", type=Path, default=ROOT / "research_registry.json")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--decision", choices=("accept", "reject"))
    parser.add_argument("--reason", default="")
    parser.add_argument("--topic", action="append", default=[])
    args = parser.parse_args()
    data = read_json(args.registry)
    map_path = args.registry.parent / "map_source.json"
    map_data = read_json(map_path) if map_path.exists() else None
    validate(data, map_data)
    if args.previous:
        validate_transition(read_json(args.previous), data, map_data)
    if args.command == "validate":
        print(f"Research registry valid: {len(data['topics'])} topics, {len(data['sources'])} sources, {len(data['claims'])} claims")
        return
    if args.command == "queue":
        result = {"topics": [{"id": t["id"], "title": t["title"], "questions": t.get("researchQuestions", []),
                               "keywords": t.get("keywords", [])} for t in data["topics"] if t["status"] != "dormant"],
                  "openChecks": [w for w in data["watchpoints"] if w["status"] == "open"],
                  "publicationRule": "Retrieve originals; propose changes; validate transition; preserve prior records."}
    else:
        if not args.input or not args.output:
            parser.error("suggest and feedback require --input and --output")
        if args.output.resolve() == args.registry.resolve():
            parser.error("Write a separate candidate file; this command cannot overwrite the live registry")
        proposal = read_json(args.input)
        if args.command == "suggest":
            result = suggest(data, proposal)
        else:
            if not args.decision:
                parser.error("feedback requires --decision")
            result = feedback_candidate(data, proposal, args.decision, args.reason, args.topic)
    if args.output:
        output = args.output.resolve()
        project = ROOT.parent.resolve()
        if output.is_relative_to(project) and not output.is_relative_to(project / ".architecture"):
            parser.error("Candidate output inside this project must be under .architecture/; published sources are protected")
        write_json(args.output, result)
        print(f"Candidate written: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"Research validation failed: {exc}")
