"""Static topic, synthesis and evidence views; the master remains untouched."""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

from research_registry import read_json, terms, validate


def esc(value):
    return html.escape(str(value), quote=True)


class Outline(HTMLParser):
    def __init__(self):
        super().__init__()
        self._rows = []
        self._main_rows = []
        self._saw_main = False
        self.stack = []
        self.hierarchy = {}
        self.current = None

    @property
    def rows(self):
        return self._main_rows if self._saw_main else self._rows

    def context(self):
        ancestors = list(reversed(self.stack))
        brief = next((attrs.get("id", "") for tag, attrs in ancestors
                      if tag == "details" and attrs.get("id", "").startswith("brief-")), "")
        if brief:
            return "brief", "Week ending " + brief.removeprefix("brief-")
        if any(tag == "article" and attrs.get("id") == "report-story" for tag, attrs in ancestors):
            return "report", ""
        if any(tag == "section" and attrs.get("id") == "update" for tag, attrs in ancestors):
            return "current", ""
        return "main", ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append((tag, attrs))
        if tag == "main" and attrs.get("id") == "main-content":
            self._saw_main = True
        if tag in {"h2", "h3", "h4"} and self.current is None:
            in_dialog = any(parent == "dialog" for parent, _ in self.stack[:-1])
            in_main = any(parent == "main" and values.get("id") == "main-content"
                          for parent, values in self.stack[:-1])
            if not in_dialog:
                scope, date_context = self.context()
                level = int(tag[1])
                key = (scope, date_context)
                parents = [self.hierarchy.get(key, {}).get(parent, "")
                           for parent in range(2, level)]
                self.current = {"id": attrs.get("id", ""), "title": "", "level": level,
                                "tag": tag, "inMain": in_main, "scope": scope,
                                "dateContext": date_context,
                                "parents": [title for title in parents if title]}

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.current and tag == self.current["tag"]:
            row = {key: value for key, value in self.current.items()
                   if key not in {"tag", "inMain"}}
            context_key = (row["scope"], row["dateContext"])
            hierarchy = self.hierarchy.setdefault(context_key, {})
            hierarchy[row["level"]] = row["title"]
            for level in list(hierarchy):
                if level > row["level"]:
                    del hierarchy[level]
            if row["id"]:
                self._rows.append(row)
                if self.current["inMain"]:
                    self._main_rows.append(row)
            self.current = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        if self.current:
            self.current["title"] += value


def build_research(root, dist, render_page):
    root, dist = Path(root), Path(dist)
    data = read_json(root / "research_registry.json")
    map_data = read_json(root / "map_source.json")
    tables = validate(data, map_data)
    topics, sources = tables["topics"], tables["sources"]
    dated_briefs = sorted(p.stem for p in (root / "briefs").glob("????-??-??.html"))
    current_through = dated_briefs[-1] if dated_briefs else "Not recorded"
    parser = Outline()
    parser.feed((dist / "index.html").read_text(encoding="utf-8"))
    seen = set()
    outline = []
    for row in parser.rows:
        if row["id"] not in seen:
            seen.add(row["id"])
            outline.append({**row, "href": "/#" + row["id"]})
    data["reportSections"] = outline
    data["reportCurrentThrough"] = current_through
    data["briefs"] = [{"date": d, "url": f"/briefs/{d}.html"} for d in dated_briefs]
    explicit_entities = {row["id"]: dict(row) for row in data.get("entities", [])
                         if isinstance(row, dict) and isinstance(row.get("id"), str)}
    entities = []
    for ident in map_data["nodes"]:
        explicit = explicit_entities.pop(ident, {})
        derived_topics = [t["id"] for t in data["topics"] if ident in t.get("entityIds", [])]
        topic_ids = list(dict.fromkeys([*explicit.get("topicIds", []), *derived_topics]))
        report_href = explicit.get("reportHref") or next(
            (link["href"] for topic in data["topics"] if ident in topic.get("entityIds", [])
             for link in topic.get("reportLinks", [])), "/#top")
        entities.append({**explicit, "id": ident, "topicIds": topic_ids, "reportHref": report_href})
    entities.extend(explicit_entities.values())
    data["entities"] = entities
    (dist / "research").mkdir(parents=True, exist_ok=True)
    (dist / "topics").mkdir(parents=True, exist_ok=True)
    (dist / "research" / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dist / "research-ui.js").write_text((root / "research_ui.js").read_text(encoding="utf-8"), encoding="utf-8")

    def source_links(ids):
        return '<ul class="source-links">' + "".join(
            f'<li><a href="{esc(sources[s]["url"])}" rel="noopener noreferrer">{esc(sources[s]["publisher"])}: {esc(sources[s]["title"])}</a>'
            f'<span class="topic-meta">{esc(sources[s].get("publishedAt") or "Publication date not recorded")} · reviewed {esc(sources[s]["accessedAt"])}</span>'
            + (f'<span class="topic-meta">Location: {esc(sources[s]["locator"])}</span>' if sources[s].get("locator") else "") + '</li>'
            for s in ids) + "</ul>"

    def claim_html(claim):
        labels = {"documented": "Documented record", "lead": "Research lead · primary verification pending",
                  "disputed": "Disputed record", "superseded": "Superseded · retained history"}
        history_links = []
        if claim.get("supersedes"):
            history_links.append(f'<a href="/synthesis.html#claim-{esc(claim["supersedes"])}">Read the preceding record</a>')
        for replacement in data["claims"]:
            if replacement.get("supersedes") == claim["id"]:
                history_links.append(f'<a href="/synthesis.html#claim-{esc(replacement["id"])}">Read the replacement record</a>')
        return (f'<article class="evidence-record" id="claim-{esc(claim["id"])}">'
                f'<div class="record-type">{esc(labels[claim["status"]])} · {esc(claim["recordType"])}</div>'
                f'<p>{esc(claim["text"])}</p><p class="record-context">{esc(claim["context"])}</p>'
                f'<p class="topic-meta">Event or scheduled date: {esc(claim.get("eventDate") or "Not recorded")} · Source review: {esc(claim.get("reviewedAt") or "Not recorded")}</p>'
                f'{source_links(claim["sourceIds"])}'
                + ('<p class="record-context">' + ' · '.join(history_links) + '</p>' if history_links else '') + '</article>')

    def topic_row(topic):
        cats = " ".join(topic["categoryIds"])
        searchable = " ".join([topic["title"], topic["description"], *topic.get("keywords", []),
                               *(tables["categories"][c]["title"] for c in topic["categoryIds"])])
        return (f'<article class="topic-row" data-topic-record data-categories="{esc(cats)}" data-status="{esc(topic["status"])}" data-search="{esc(searchable.lower())}">'
                f'<div><h2><a href="/topics/{esc(topic["id"])}.html">{esc(topic["title"])}</a></h2>'
                f'<p>{esc(topic["description"])}</p><span class="topic-meta">'
                + " · ".join(esc(tables["categories"][c]["title"]) for c in topic["categoryIds"])
                + f'</span></div><div class="topic-links"><a href="/topics/{esc(topic["id"])}.html">Explore topic <span aria-hidden="true">→</span></a></div></article>')

    def sidebar():
        return '<p class="sidebar-label">Across the report</p><ul>' + "".join(
            f'<li><a href="/topics.html?category={esc(c["id"])}">{esc(c["title"])}</a></li>' for c in data["categories"]
        ) + '</ul><p class="sidebar-label">The record</p><ul><li><a href="/#u-corrections">Corrections</a></li><li><a href="/sources.html">Original source index</a></li><li><a href="/synthesis.html?view=contents">Full report contents</a></li></ul>'

    freshness = (f'<p class="topic-meta">Published weekly record through {esc(current_through)} · '
                 f'Structured research reviewed {esc(data["updatedAt"])}</p>')
    footer = ('<aside class="research-note"><strong>How this record grows.</strong> '
              'The topic registry supplies these pages and the map filters. New evidence can suggest topics; '
              'recorded review accepts or rejects those suggestions. A source establishes only what it actually records. '
              'Historical editions and superseded claims remain accessible.</aside>')
    scripts = '<script src="/research-ui.js" defer></script>'

    def write_page(path, title, body, active):
        destination = dist / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_page(title, body + scripts, active=active, sidebar_html=sidebar(),
                                           description="Source-linked topics, research questions and preserved report history.",
                                           page_class="research-page"), encoding="utf-8")

    categories = '<button type="button" class="filter-button" data-category="all" aria-pressed="true">All categories</button>' + "".join(
        f'<button type="button" class="filter-button" data-category="{esc(c["id"])}" aria-pressed="false">{esc(c["title"])}</button>' for c in data["categories"])
    topic_body = ('<header class="research-intro"><p class="kicker">THE RESEARCH INDEX</p><h1>Topics</h1>'
                  '<p class="dek">Follow subjects, records and open questions across the report.</p>' + freshness + '</header>'
                  '<section class="research-toolbar" aria-label="Filter topics"><label class="research-search">Find a topic'
                  '<input type="search" id="topic-search" placeholder="Search subjects, people or records" autocomplete="off"></label>'
                  f'<div class="filter-row" aria-label="Topic categories">{categories}</div>'
                  '<div class="filter-row" aria-label="Research status"><button type="button" class="filter-button" data-status-filter="all" aria-pressed="true">All statuses</button>'
                  + "".join(f'<button type="button" class="filter-button" data-status-filter="{s}" aria-pressed="false">{label}</button>' for s, label in (("active", "Active"), ("new", "New"), ("watching", "Watching"), ("dormant", "Archived")))
                  + '</div><p id="topic-results" class="topic-meta" aria-live="polite"></p></section>'
                  + '<div class="topic-list">' + "".join(topic_row(t) for t in data["topics"]) + '</div>'
                  '<p id="topic-empty" hidden>No topics match. Try another search or category.</p>' + footer)
    write_page("topics.html", "Topics — The Architecture", topic_body, "topics")
    urls = ["/topics.html", "/synthesis.html"]

    for topic in data["topics"]:
        ident = topic["id"]
        claims = [c for c in data["claims"] if ident in c["topicIds"]]
        current_claims = [c for c in claims if c["status"] != "superseded"]
        old_claims = [c for c in claims if c["status"] == "superseded"]
        questions = '<ol class="question-list">' + "".join(f'<li>{esc(q)}</li>' for q in topic.get("researchQuestions", [])) + '</ol>'
        report_links = '<ul class="question-list">' + "".join(f'<li><a href="{esc(l["href"])}">{esc(l["label"])} <span aria-hidden="true">→</span></a></li>' for l in topic.get("reportLinks", [])) + '</ul>'
        entities = "".join(f'<li><a href="/neural.html?entity={quote(e)}&amp;topic={quote(ident)}">{esc(map_data["nodes"][e].get("name", e)) if isinstance(map_data["nodes"][e], dict) else esc(e)}</a></li>' for e in topic.get("entityIds", []))
        if entities:
            entities = '<p>Entities associated with this research topic; this list does not assert a relationship between them.</p><ul class="question-list">' + entities + '</ul>'
        else:
            entities = '<p>No entities from the existing map are assigned to this topic.</p>'
        relevant_feedback = [f for f in data["feedback"] if ident in f.get("topicIds", [])]
        feedback_labels = {"topic_fit": "Topic relevance", "source_route": "Source access", "evidence_review": "Evidence review"}
        feedback_html = "".join(f'<li>{esc(f["date"])} · {esc(feedback_labels[f.get("purpose", "topic_fit")])} · {esc(f["decision"])}: {esc(f["reason"])}</li>' for f in relevant_feedback)
        body = (f'<header class="research-intro"><p class="kicker"><a href="/topics.html">TOPICS</a> / {esc(topic["status"].upper())}</p><h1>{esc(topic["title"])}</h1>'
                f'<p class="dek">{esc(topic["description"])}</p>{freshness}</header>'
                + f'<section class="research-panel"><h2 id="report">In the full report</h2><p class="topic-meta">{len(topic.get("reportLinks", []))} linked sections · {len(current_claims)} structured records · {len(topic.get("entityIds", []))} mapped entities</p>'
                + '<p>These links open the preserved report, including its dated evidence and qualifications.</p>' + report_links + '</section>'
                '<section><h2 id="records">Evidence & context</h2>'
                + ("".join(claim_html(c) for c in current_claims) if current_claims else '<p class="research-note">Separate structured records have not yet been added here. Read the report sections above for the existing coverage.</p>')
                + '</section><div class="research-grid"><section class="research-panel"><h2 id="questions">Open questions</h2>' + questions
                + f'</section><section class="research-panel"><h2>Explore connections</h2><p><a href="/neural.html?topic={quote(ident)}">Open this topic in the map →</a></p><p><a href="/synthesis.html?view=connections">Follow dated connection paths →</a></p></section></div>'
                + '<section><h2 id="entities">Related entities</h2>' + entities + '</section>'
                + '<section><h2 id="history">Research history</h2><p>Topic opened ' + esc(topic["createdAt"]) + '; updated ' + esc(topic["updatedAt"]) + '.</p>'
                + ('<ul>' + feedback_html + '</ul>' if feedback_html else '<p>No retrieval feedback has been recorded for this topic yet.</p>')
                + ("<details><summary>Superseded records</summary>" + "".join(claim_html(c) for c in old_claims) + "</details>" if old_claims else "")
                + '</section>' + footer)
        write_page(f"topics/{ident}.html", topic["title"] + " — The Architecture", body, "topics")
        urls.append(f"/topics/{ident}.html")

    connections = '<section class="research-view" id="view-connections" data-view="connections"><h2>Connections across the record</h2><p>Follow each relationship, its date and its evidence. A path can cross different periods; it does not by itself establish shared intent or continuing control.</p><h3>Curated connection paths</h3>'
    relationships = {r["mapEdgeIndex"]: r for r in data.get("relationships", [])}
    for path in data.get("networkPaths", []):
        connections += (f'<article class="evidence-record" id="connection-{esc(path["id"])}"><h3>{esc(path["title"])}</h3>'
                        f'<p>{esc(path["summary"])}</p><ol class="question-list">')
        for index in path["edgeIndices"]:
            start, end, grade, label = map_data["edges"][index]
            record = relationships[index]
            connections += '<li>' + ' → '.join(
                f'<a href="/neural.html?entity={quote(entity)}&amp;topic={quote(path["topicIds"][0])}">{esc(map_data["nodes"][entity]["name"])}</a>'
                for entity in (start, end)) + f'<p>{esc(label)} · Evidence [{esc(grade)}]</p><p>'
            connections += ' · '.join(f'<a href="/synthesis.html#claim-{esc(cid)}">Read the supporting record</a>' for cid in record["claimIds"])
            connections += '</p>' + source_links(record["sourceIds"]) + '</li>'
        connections += (f'</ol><p class="record-context">{esc(path["context"])}</p><p><strong>Next check:</strong> {esc(path["nextCheck"])}</p>'
                        f'<p class="topic-meta">Reviewed {esc(path["reviewedAt"])}</p>'
                        f'<p><a href="/neural.html?topic={quote(path["topicIds"][0])}">Explore the complete topic map →</a></p></article>')
    if not data.get("networkPaths"):
        connections += '<p>No connection paths have completed evidence review yet.</p>'
    connections += '<h3>All reviewed relationships</h3><p>Each record below is an existing relationship with attached reviewed evidence. The accumulated map also retains relationships whose source link has not yet been attached; their existing grade remains explicit in the map.</p>'
    for relation in data.get("relationships", []):
        index = relation["mapEdgeIndex"]
        start, end, grade, label = map_data["edges"][index]
        claim_records = [tables["claims"][claim_id] for claim_id in relation.get("claimIds", [])]
        connections += (f'<article class="evidence-record" id="relationship-edge-{index}">'
                        f'<h4>{esc(map_data["nodes"][start]["name"])} → {esc(map_data["nodes"][end]["name"])}</h4>'
                        f'<p>{esc(label)} · Evidence [{esc(grade)}]</p>')
        if claim_records:
            connections += '<ul class="question-list">' + "".join(
                f'<li><a href="/synthesis.html#claim-{esc(claim["id"])}">{esc(claim["text"])}</a>'
                f'<p class="record-context">{esc(claim["context"])}</p></li>' for claim in claim_records) + '</ul>'
        connections += source_links(relation["sourceIds"])
        if relation.get("reportHref"):
            connections += f'<p><a href="{esc(relation["reportHref"])}">Read report context →</a></p>'
        connections += '</article>'
    connections += '</section>'

    overview = (f'<section class="research-view" id="view-overview" data-view="overview"><section class="research-panel"><h2>The complete report is here</h2><p>Explore {len(outline)} linked headings and the preserved weekly archive alongside the new structured records.</p><p><a href="?view=contents">Browse the full report index →</a> · <a href="/#top">Read the report →</a></p></section><h2>Questions across the report</h2><p><a href="?view=connections">Explore connections across the record →</a></p><div class="topic-list">'
                + "".join(topic_row(t) for t in data["topics"] if t["status"] in {"active", "new"})
                + '</div><p><a href="/topics.html">Browse every research topic →</a></p><div class="research-grid">'
                '<section class="research-panel"><h2>Compare the history</h2><p>Examine original records, similarities, material differences and evidence against each comparison.</p><a href="?view=compare">Open historical comparisons →</a></section>'
                '<section class="research-panel"><h2>Next records to check</h2><p>Questions retain their dates, source checks and outcomes. Unanswered questions remain open.</p><a href="?view=checks">Open research checks →</a></section></div>'
                '<p class="research-note">Claim → Original source → Context → Revision history</p></section>')
    timeline = '<section class="research-view" id="view-timeline" data-view="timeline"><h2>Structured record timeline</h2><p class="research-note">This timeline contains the new structured records below. The preserved weekly archive remains separate; a scheduled event is not an observed outcome.</p>'
    timeline += "".join(claim_html(c) for c in sorted(data["claims"], key=lambda c: c.get("eventDate") or "", reverse=True) if c["status"] != "superseded")
    superseded = [c for c in data["claims"] if c["status"] == "superseded"]
    if superseded:
        timeline += '<details><summary>Earlier records and their replacements</summary>' + ''.join(claim_html(c) for c in superseded) + '</details>'
    timeline += '<h2>Published weekly archive</h2><ul>' + "".join(f'<li><a href="/briefs/{d}.html">Week ending {d}</a></li>' for d in reversed(dated_briefs)) + '</ul></section>'
    comparison_html = '<section class="research-view" id="view-compare" data-view="compare"><h2>Historical comparisons</h2><p>A comparison records its evidence and limits. It is not an outcome forecast.</p>'
    for comparison in data["comparisons"]:
        comparison_html += f'<article class="evidence-record"><h3>{esc(comparison["title"])}</h3><dl class="history-grid">'
        for key, label in (("historicalCase", "Historical case"), ("documentedBasis", "Documented basis"), ("similarities", "Similarities"), ("differences", "Material differences"), ("counterevidence", "Evidence against the comparison"), ("nextCheck", "Next record to check")):
            comparison_html += f'<dt>{label}</dt><dd>{esc(comparison.get(key, "Not established"))}</dd>'
        comparison_html += '</dl>' + source_links(comparison["sourceIds"]) + '</article>'
    comparison_html += '<p class="research-note">The preserved report’s forecast chapter describes its estimates as judgment, not a model output. This structured view does not assign political scores or forecast election outcomes.</p></section>'
    checks = '<section class="research-view" id="view-checks" data-view="checks"><h2>Next records to check</h2><div class="checks-list">'
    for check in data["watchpoints"]:
        checks += (f'<article class="evidence-record"><h3>{esc(check["question"])}</h3>'
                   f'<p class="topic-meta">Last checked: {esc(check.get("lastCheckedAt") or "Not yet recorded")} · {esc(check["status"])}</p>'
                   f'<p>{esc(check["outcome"])}</p><p><strong>Next check:</strong> {esc(check.get("nextCheck") or "Not yet specified")}</p>'
                   + source_links(check.get("sourceIds", [])) + '<p>' + " · ".join(f'<a href="/topics/{esc(t)}.html">{esc(topics[t]["title"])}</a>' for t in check["topicIds"]) + '</p></article>')
    checks += '</div><h2>Revision history</h2><p>These dated records preserve additions and before-and-after corrections to the structured research layer.</p><div class="checks-list">'
    for revision in data["revisions"]:
        checks += (f'<article class="evidence-record" id="revision-{esc(revision["id"])}">'
                   f'<h3>{esc(revision["date"])} · {esc(revision["id"])}</h3><p>{esc(revision["summary"])}</p>')
        links = []
        links.extend(f'<a href="/synthesis.html#claim-{esc(claim_id)}">Claim: {esc(claim_id)}</a>'
                     for claim_id in revision.get("claimIds", []))
        links.extend(f'<a href="/topics/{esc(topic_id)}.html">Topic: {esc(topics[topic_id]["title"])}</a>'
                     for topic_id in revision.get("topicIds", []))
        links.extend(f'<a href="/synthesis.html#connection-{esc(path_id)}">Path: {esc(path_id)}</a>'
                     for path_id in revision.get("pathIds", []))
        if links:
            checks += '<p>' + ' · '.join(links) + '</p>'
        for change in revision.get("changes", []):
            identity = change.get("id", change.get("mapEdgeIndex", "record"))
            checks += (f'<details><summary>{esc(change.get("collection", "record"))} · {esc(identity)}</summary>'
                       f'<p>{esc(change.get("reason", "Reason not recorded"))}</p>')
            if "before" in change:
                checks += '<h4>Before</h4><pre>' + esc(json.dumps(change["before"], ensure_ascii=False, indent=2)) + '</pre>'
            if "after" in change:
                checks += '<h4>After</h4><pre>' + esc(json.dumps(change["after"], ensure_ascii=False, indent=2)) + '</pre>'
            checks += '</details>'
        checks += '</article>'
    checks += '</div></section>'
    contents = '<section class="research-view" id="view-contents" data-view="contents"><h2>The complete report index</h2><p>These links open the preserved authored sections, including their interpretations and qualifications. Inclusion is not a new verification of each underlying claim.</p><ol class="report-outline">'
    contents += "".join(
        f'<li class="outline-level-{row["level"]}"><a href="{esc(row["href"])}">{esc(row["title"])}</a>'
        + ('<span class="topic-meta">' + esc(" · ".join([
            row.get("dateContext") or {"current": "Current weekly record", "report": "Preserved report"}.get(row.get("scope"), "Main report"),
            " › ".join(row.get("parents", []))
        ]).strip(" · ")) + '</span>' if row.get("scope") or row.get("parents") else '')
        + '</li>' for row in outline) + '</ol></section>'
    tabs = '<div class="view-tabs" aria-label="Synthesis views">' + "".join(f'<button type="button" data-view-tab="{ident}" aria-controls="view-{ident}">{label}</button>' for ident, label in (("overview", "Overview"), ("connections", "Connections"), ("timeline", "Timeline"), ("compare", "Historical comparisons"), ("checks", "Records to check"), ("contents", "Full report"))) + '</div>'
    body = ('<header class="research-intro"><p class="kicker">SYNTHESIS</p><h1>The wider picture.</h1><p class="dek">Explore the record, compare the history, follow what changes.</p>'
            + freshness + '</header>' + tabs + overview + connections + timeline + comparison_html + checks + contents + footer)
    write_page("synthesis.html", "Synthesis — The Architecture", body, "synthesis")
    return urls
