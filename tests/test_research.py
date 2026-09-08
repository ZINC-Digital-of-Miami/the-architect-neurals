"""Meaningful regression cases for evidence retention and candidate publication boundaries."""
import copy
import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from research_registry import feedback_candidate, read_json, suggest, validate, validate_transition, write_json
from build_research import Outline, build_research


class ResearchIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(ROOT / "src/research_registry.json")
        self.map = read_json(ROOT / "src/map_source.json")

    def test_real_registry_has_resolvable_sources_and_entities(self):
        validate(self.data, self.map)

    def test_company_role_profile_is_identified_as_a_company_statement(self):
        claim = next(c for c in self.data['claims'] if c['id'] == 'trump-jr-1789-partner-profile')
        source = next(s for s in self.data['sources'] if s['id'] == claim['sourceIds'][0])
        self.assertEqual(source['sourceType'], 'corporate_statement')
        self.assertIsNone(claim['eventDate'])
        candidate = copy.deepcopy(self.data)
        next(c for c in candidate['claims'] if c['id'] == claim['id'])['status'] = 'documented'
        next(s for s in candidate['sources'] if s['id'] == source['id'])['sourceType'] = 'reporting'
        with self.assertRaisesRegex(ValueError, 'single-origin'):
            validate(candidate, self.map)

    def test_sparse_topic_keeps_report_coverage_before_structured_records(self):
        data = copy.deepcopy(self.data)
        topic = {**copy.deepcopy(data['topics'][0]), 'id': 'test-sparse-topic'}
        data['topics'].append(topic)
        with tempfile.TemporaryDirectory() as temp:
            src, dist = Path(temp) / 'src', Path(temp) / 'site'
            src.mkdir(); dist.mkdir(); (src / 'briefs').mkdir()
            (src / 'research_registry.json').write_text(json.dumps(data))
            (src / 'map_source.json').write_text(json.dumps(self.map))
            (src / 'research_ui.js').write_text('')
            (dist / 'index.html').write_text('<h2 id="existing">Preserved section</h2>')
            build_research(src, dist, lambda title, body, **kw: body)
            page = (dist / 'topics/test-sparse-topic.html').read_text()
            self.assertEqual(page.count('id="report"'), 1)
            self.assertLess(page.index('id="report"'), page.index('id="records"'))
            self.assertIn(html.escape(topic['reportLinks'][0]['href'], quote=True), page[:page.index('id="records"')])

    def test_connection_path_rejects_a_disconnected_intermediary(self):
        path = self.data["networkPaths"][0]
        path["entityIds"][1] = next(n for n in self.map["nodes"] if n not in path["entityIds"])
        with self.assertRaisesRegex(ValueError, "disconnected"):
            validate(self.data, self.map)

    def test_connection_path_cannot_promote_an_unverified_claim(self):
        index = self.data["networkPaths"][0]["edgeIndices"][0]
        relation = next(r for r in self.data["relationships"] if r["mapEdgeIndex"] == index)
        claim = next(c for c in self.data["claims"] if c["id"] == relation["claimIds"][0])
        claim["status"] = "lead"
        with self.assertRaisesRegex(ValueError, "current documented"):
            validate(self.data, self.map)

    def test_connection_path_rejects_documented_but_unrelated_evidence(self):
        relation = next(r for r in self.data["relationships"] if r["mapEdgeIndex"] == 70)
        unrelated = next(c for c in self.data["claims"] if c["id"] == "afd-thuringia-history-ruling-2024")
        relation.update(claimIds=[unrelated["id"]], sourceIds=unrelated["sourceIds"])
        with self.assertRaisesRegex(ValueError, "does not support"):
            validate(self.data, self.map)

    def test_relationship_evidence_changes_require_retained_history(self):
        candidate = copy.deepcopy(self.data)
        relation = next(r for r in candidate["relationships"] if r["mapEdgeIndex"] == 70)
        before = copy.deepcopy(relation)
        relation["reportHref"] = "/topics/trump-early-financing.html"
        with self.assertRaisesRegex(ValueError, "before and after evidence"):
            validate_transition(self.data, candidate, self.map)
        candidate["revisions"].append({"id": "relationship-evidence-review", "date": "2026-09-08",
            "changes": [{"collection": "relationships", "mapEdgeIndex": 70,
            "before": before, "after": copy.deepcopy(relation), "reason": "Retain the prior evidence route."}]})
        validate_transition(self.data, candidate, self.map)

    def test_new_connection_path_requires_a_revision(self):
        candidate = copy.deepcopy(self.data)
        candidate["networkPaths"].append({**copy.deepcopy(candidate["networkPaths"][0]), "id": "unreviewed-path"})
        with self.assertRaisesRegex(ValueError, "new path requires"):
            validate_transition(self.data, candidate, self.map)

    def test_connection_path_context_changes_retain_prior_interpretation(self):
        candidate = copy.deepcopy(self.data)
        path = candidate["networkPaths"][0]
        before = copy.deepcopy(path)
        path["context"] = "A newly reviewed interpretation with explicit limits."
        with self.assertRaisesRegex(ValueError, "before and after"):
            validate_transition(self.data, candidate, self.map)
        candidate["revisions"].append({"id": "path-context-review", "date": "2026-09-08",
            "pathIds": [path["id"]], "changes": [{"collection": "networkPaths", "id": path["id"],
            "before": before, "after": copy.deepcopy(path), "reason": "New evidence changes the interpretation."}]})
        validate_transition(self.data, candidate, self.map)

    def test_single_wire_story_cannot_be_promoted_by_syndication(self):
        candidate = copy.deepcopy(self.data)
        claim = next(c for c in candidate["claims"] if c["id"] == "rothschild-taj-creditor-role")
        claim["status"] = "documented"
        with self.assertRaisesRegex(ValueError, "single-origin"):
            validate(candidate, self.map)

    def test_source_url_cannot_execute_script(self):
        self.data["sources"][0]["url"] = "javascript:alert(document.cookie)"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate(self.data, self.map)

    def test_unknown_identity_cannot_create_map_connection(self):
        self.data["topics"][0]["entityIds"].append("ROTHSCHILD")
        with self.assertRaisesRegex(ValueError, "entityIds"):
            validate(self.data, self.map)

    def test_old_statement_cannot_be_reworded(self):
        candidate = copy.deepcopy(self.data)
        candidate["claims"][0]["text"] += " New asserted motive."
        with self.assertRaisesRegex(ValueError, "Cannot rewrite"):
            validate_transition(self.data, candidate, self.map)

    def test_old_source_cannot_be_removed(self):
        candidate = copy.deepcopy(self.data)
        candidate["sources"].pop(0)
        with self.assertRaises(ValueError):
            validate_transition(self.data, candidate, self.map)

    def test_supersession_retains_original_and_requires_replacement(self):
        candidate = copy.deepcopy(self.data)
        current = next(c for c in candidate["claims"] if c["status"] != "superseded")
        current["status"] = "superseded"
        with self.assertRaisesRegex(ValueError, "replacement"):
            validate_transition(self.data, candidate, self.map)
        replacement = copy.deepcopy(current)
        replacement.update(id="new-record", status="lead", supersedes=current["id"])
        candidate["claims"].append(replacement)
        candidate["revisions"].append({"id": "replacement-recorded", "date": "2026-09-08", "summary": "New record", "claimIds": ["new-record"]})
        validate_transition(self.data, candidate, self.map)

    def test_renaming_topic_requires_dated_history(self):
        candidate = copy.deepcopy(self.data)
        before = copy.deepcopy(candidate["topics"][0])
        candidate["topics"][0]["title"] = "New topic name"
        with self.assertRaisesRegex(ValueError, "dated revision"):
            validate_transition(self.data, candidate, self.map)
        candidate["revisions"].append({"id": "topic-rename", "date": "2026-09-08", "topicIds": [candidate["topics"][0]["id"]], "summary": "Scope renamed"})
        with self.assertRaisesRegex(ValueError, "before and after"):
            validate_transition(self.data, candidate, self.map)
        candidate["revisions"][-1]["changes"] = [{"collection": "topics", "id": before["id"],
            "before": before, "after": copy.deepcopy(candidate["topics"][0]), "reason": "Scope renamed"}]
        validate_transition(self.data, candidate, self.map)

    def test_topic_scope_history_survives_successive_updates(self):
        previous = copy.deepcopy(self.data)
        for index in range(2):
            candidate = copy.deepcopy(previous)
            before = copy.deepcopy(candidate["topics"][0])
            candidate["topics"][0]["description"] = f"Reviewed scope {index}"
            candidate["revisions"].append({"id": f"scope-review-{index}", "date": "2026-09-08",
                "topicIds": [before["id"]], "changes": [{"collection": "topics", "id": before["id"],
                "before": before, "after": copy.deepcopy(candidate["topics"][0]), "reason": "Scope reviewed"}]})
            validate_transition(previous, candidate, self.map)
            previous = candidate
        rewritten = copy.deepcopy(previous)
        rewritten["revisions"][-2]["changes"][0]["before"]["description"] = "Rewritten original"
        with self.assertRaisesRegex(ValueError, "Cannot rewrite historical"):
            validate_transition(previous, rewritten, self.map)
        self.assertEqual(previous["revisions"][-2]["changes"][0]["before"], self.data["topics"][0])

    def test_added_topic_metadata_also_requires_a_retained_snapshot(self):
        candidate = copy.deepcopy(self.data)
        candidate["topics"][0]["scopeNote"] = "Newly recorded scope detail"
        with self.assertRaisesRegex(ValueError, "before and after"):
            validate_transition(self.data, candidate, self.map)

    def test_synthesis_tab_selection_clears_old_claim_fragment(self):
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
function page(href) {
  const names = ['overview', 'timeline', 'compare', 'checks', 'contents'];
  const events = {};
  const document = {activeElement: null, addEventListener() {}};
  const context = {URL, URLSearchParams, document, location: new URL(href),
    addEventListener: (name, callback) => { events[name] = callback; }};
  const views = names.map(name => ({id: `view-${name}`, dataset: {view: name},
    hidden: false, setAttribute() {}, closest() { return this; }}));
  const tabs = names.map(name => ({dataset: {viewTab: name}, attributes: {}, handlers: {},
    parentElement: {setAttribute() {}},
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, callback) { this.handlers[key] = callback; },
    focus() { document.activeElement = this; }}));
  const claim = {closest: () => views[1]};
  document.getElementById = id => id === 'claim-record' ? claim : views.find(view => view.id === id) || null;
  document.querySelectorAll = selector => selector === '[data-view-tab]' ? tabs : selector === '[data-view]' ? views : [];
  context.history = {pushState(_state, _title, url) { context.location = new URL(url, context.location); }};
  vm.runInNewContext(source, context);
  return {context, views, tabs, events,
    selected: () => tabs.find(tab => tab.attributes['aria-selected'] === 'true').dataset.viewTab};
}
const initial = page('https://example.org/synthesis.html#claim-record');
assert.equal(initial.selected(), 'timeline');
assert.equal(initial.views[1].hidden, false);
initial.tabs[0].handlers.click();
assert.equal(initial.selected(), 'overview');
assert.equal(initial.context.location.hash, '');
assert.equal(page(initial.context.location.href).selected(), 'overview');
initial.tabs[0].handlers.keydown({key: 'End', preventDefault() {}});
assert.equal(initial.selected(), 'contents');
assert.equal(initial.context.document.activeElement, initial.tabs[4]);
assert.equal(page(initial.context.location.href).selected(), 'contents');
initial.context.location = new URL('https://example.org/synthesis.html#claim-record');
initial.events.popstate();
assert.equal(initial.selected(), 'timeline');
"""
        result = subprocess.run(["node", "-e", script, str(ROOT / "src/research_ui.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_reader_opens_saved_panel_and_top_scrolls_past_sticky_header(self):
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const documentEvents = {}, windowEvents = {}, failures = [];
const document = {activeElement: null, documentElement: {classList: {add() {}}},
  addEventListener(type, callback) { (documentEvents[type] ||= []).push(callback); }};
const context = {URL, URLSearchParams, document, location: new URL('https://example.org/synthesis.html'),
  scrollY: 2800, innerHeight: 800,
  matchMedia: () => ({matches: false, addEventListener() {}}),
  addEventListener(type, callback) { (windowEvents[type] ||= []).push(callback); },
  requestAnimationFrame(callback) { callback(); return 1; },
  setTimeout() { return 1; }, clearTimeout() {},
  CustomEvent: class { constructor(type, options) { this.type = type; Object.assign(this, options); } },
  localStorage: {getItem: () => JSON.stringify({version: 1, id: 'view-timeline', offset: 0})},
  scrollTo({top}) { context.scrollY = top; }};
context.window = context;
context.history = {pushState(_state, _title, url) { context.location = new URL(url, context.location); }};
function element(id, dataset = {}) {
  return {id, dataset, attributes: {}, handlers: {}, parentElement: null, hidden: false,
    setAttribute(key, value) { this.attributes[key] = value; },
    getAttribute(key) { return this.attributes[key]; },
    hasAttribute(key) { return key in this.attributes; },
    addEventListener(type, callback) { this.handlers[type] = callback; },
    dispatchEvent(event) { event.target = this; (documentEvents[event.type] || []).forEach(callback => callback(event)); },
    focus() { document.activeElement = this; },
    closest(selector) { return selector === '[data-view]' && this.dataset.view ? this : null; },
    getBoundingClientRect() { return {top: 0}; },
    scrollIntoView() { this.scrolledIntoView = true; }};
}
const names = ['overview', 'timeline', 'compare', 'checks', 'contents'];
const views = names.map(name => element(`view-${name}`, {view: name}));
const tabs = names.map(name => Object.assign(element('', {viewTab: name}), {parentElement: {setAttribute() {}}}));
const details = {tagName: 'DETAILS', open: false, parentElement: null};
views[1].parentElement = details;
const top = element('top'), resume = element('resume'), status = {textContent: ''};
document.getElementById = id => id === 'top' ? top : views.find(view => view.id === id) || null;
document.querySelector = selector => selector === '[data-ui-resume]' ? resume : selector === '[data-ui-status]' ? status : null;
document.querySelectorAll = selector => selector === '[data-view-tab]' ? tabs : selector === '[data-view]' ? views : [];
vm.createContext(context);
for (const path of process.argv.slice(1)) vm.runInContext(fs.readFileSync(path, 'utf8'), context);
const check = (name, condition) => { if (!condition) failures.push(name); };
resume.handlers.click();
check('resume exposes saved panel and selects its tab', !views[1].hidden && tabs[1].attributes['aria-selected'] === 'true');
check('resume records selected view in URL', context.location.searchParams.get('view') === 'timeline');
check('resume still reveals collapsed chapter details', details.open);
check('resume focuses saved section', document.activeElement === views[1]);
const anchor = {href: new URL('#top', context.location).href, target: '',
  closest(selector) { return selector === 'a[href]' ? this : null; }};
const click = {target: anchor, button: 0, defaultPrevented: false,
  preventDefault() { this.defaultPrevented = true; }};
(documentEvents.click || []).forEach(callback => callback(click));
check('Top explicitly resets document scroll despite sticky rect', context.scrollY === 0 && !top.scrolledIntoView);
check('Top retains fragment identity and keyboard focus', context.location.hash === '#top' && document.activeElement === top);
context.scrollY = 1700;
(windowEvents.hashchange || []).forEach(callback => callback());
check('hash navigation to Top also resets scroll', context.scrollY === 0);
assert.deepEqual(failures, []);
"""
        result = subprocess.run(["node", "-e", script, str(ROOT / "src/research_ui.js"),
                                 str(ROOT / "src/site_ui.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_feedback_improves_retrieval_without_creating_claim(self):
        document = {"url": "https://example.org/record", "title": "Quasar discovery", "summary": "Distinct quasar terminology"}
        proposal = suggest(self.data, document)
        self.assertNotIn("trump-early-financing", proposal["topicIds"])
        accepted = feedback_candidate(self.data, proposal, "accept", "Explicit topic assignment for test", ["trump-early-financing"])
        self.assertIn("trump-early-financing", suggest(accepted, document)["topicIds"])
        self.assertEqual(self.data["claims"], accepted["claims"])
        self.assertEqual(self.data["sources"], accepted["sources"])
        self.assertTrue(suggest(accepted, document)["requiresReview"])

    def test_candidate_file_cannot_clobber_existing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.json"
            write_json(path, {"id": "a"})
            write_json(path, {"id": "a"})
            with self.assertRaisesRegex(ValueError, "already exists"):
                write_json(path, {"id": "b"})
            self.assertEqual(read_json(path), {"id": "a"})

    def test_evidence_rejection_does_not_suppress_later_topic_retrieval(self):
        document = {"url": "https://example.org/new-record", "title": "Rothschild Trump financing creditor bankruptcy", "summary": "A newly available original record"}
        expected = suggest(self.data, document)["topicIds"]
        self.assertIn("trump-early-financing", expected)
        for purpose in ("evidence_review", "source_route"):
            candidate = copy.deepcopy(self.data)
            candidate["feedback"].append({"id": "rejected-old-claim", "date": "2026-09-08",
                "decision": "reject", "purpose": purpose, "topicIds": ["trump-early-financing"],
                "exampleText": document["title"] + " " + document["summary"],
                "reason": "Earlier claim lacked an original document; keep researching the connection."})
            self.assertEqual(suggest(candidate, document)["topicIds"], expected)

    def test_cli_refuses_writing_a_protected_source(self):
        protected = ROOT / "src/master_report.md"
        before = protected.read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / "src/research_registry.py"), "queue", "--output", str(protected)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected", result.stderr)
        self.assertEqual(before, protected.read_bytes())

    def test_outline_handles_nested_text_and_void_elements(self):
        parser = Outline()
        parser.feed('<h2 id="first">One <em>two</em><br>three</h2><p>Not a heading</p><h3 id="second">Four</h3>')
        self.assertEqual([r["title"] for r in parser.rows], ["One twothree", "Four"])
        self.assertEqual([r["id"] for r in parser.rows], ["first", "second"])

    def test_correction_headings_are_in_the_complete_outline(self):
        parser = Outline()
        parser.feed('<h4 id="u-corrections">Corrections</h4><h4 id="u-silence">Silence ledger</h4>')
        self.assertEqual([r["id"] for r in parser.rows], ["u-corrections", "u-silence"])

    def test_self_and_cyclic_supersession_are_rejected(self):
        candidate = copy.deepcopy(self.data)
        first, second = candidate["claims"][:2]
        first["supersedes"] = first["id"]
        with self.assertRaisesRegex(ValueError, "superseded claim"):
            validate(candidate, self.map)
        first["supersedes"] = second["id"]
        second["supersedes"] = first["id"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            validate(candidate, self.map)

    def test_history_cannot_lose_checks_or_comparisons(self):
        for collection in ("watchpoints", "comparisons"):
            with self.subTest(collection=collection):
                candidate = copy.deepcopy(self.data)
                candidate[collection] = []
                with self.assertRaisesRegex(ValueError, "Cannot delete"):
                    validate_transition(self.data, candidate, self.map)

    def test_completed_check_retains_prior_state_in_revision(self):
        candidate = copy.deepcopy(self.data)
        before = copy.deepcopy(candidate["watchpoints"][0])
        candidate["watchpoints"][0].update(status="resolved", lastCheckedAt="2026-09-08", outcome="Recorded outcome")
        after = candidate["watchpoints"][0]
        with self.assertRaisesRegex(ValueError, "before and after"):
            validate_transition(self.data, candidate, self.map)
        candidate["revisions"].append({"id": "check-reviewed", "date": "2026-09-08", "changes": [{"collection": "watchpoints", "id": before["id"], "before": before, "after": after, "reason": "Source check completed"}]})
        validate_transition(self.data, candidate, self.map)

    def test_changed_feedback_assignment_is_not_silently_ignored(self):
        proposal = suggest(self.data, {"url": "https://example.org/a", "title": "Example", "summary": "New original record"})
        first = feedback_candidate(self.data, proposal, "accept", "Reviewed", ["germany-afd"])
        second = feedback_candidate(first, proposal, "accept", "Reviewed", ["trump-early-financing"])
        self.assertEqual(len(second["feedback"]), len(first["feedback"]) + 1)

    def test_invalid_metadata_cannot_enter_public_registry(self):
        cases = [
            ("topic date", lambda d: d["topics"][0].update(createdAt="not-a-date")),
            ("source chronology", lambda d: d["sources"][0].update(accessedAt="1900-01-01")),
            ("URL host", lambda d: d["sources"][0].update(url="https://invalid host.example/path")),
            ("URL port", lambda d: d["sources"][0].update(url="https://example.org:not-a-port/path")),
            ("boolean index", lambda d: d.update(relationships=[{"mapEdgeIndex": True, "sourceIds": [d["sources"][0]["id"]]}])),
            ("claim reference", lambda d: d.update(relationships=[{"mapEdgeIndex": 0, "sourceIds": [d["sources"][0]["id"]], "claimIds": ["missing"]}]))
        ]
        for label, mutate in cases:
            with self.subTest(case=label):
                candidate = copy.deepcopy(self.data); mutate(candidate)
                with self.assertRaises(ValueError):
                    validate(candidate, self.map)

    def test_generated_pages_escape_untrusted_titles_and_preserve_all_topics(self):
        with tempfile.TemporaryDirectory() as temp:
            src, dist = Path(temp) / "src", Path(temp) / "site"
            src.mkdir(); dist.mkdir(); (src / "briefs").mkdir()
            data = copy.deepcopy(self.data)
            data["topics"][0]["title"] = '<script>alert("x")</script>'
            (src / "research_registry.json").write_text(json.dumps(data))
            (src / "map_source.json").write_text(json.dumps(self.map))
            (src / "research_ui.js").write_text("")
            (dist / "index.html").write_text('<h2 id="existing">Original heading</h2>')
            urls = build_research(src, dist, lambda title, body, **kw: body)
            output = (dist / "topics.html").read_text()
            self.assertNotIn('<script>alert("x")</script>', output)
            self.assertIn('&lt;script&gt;', output)
            self.assertEqual(len(urls), len(data["topics"]) + 2)
            published = read_json(dist / "research/data.json")
            self.assertEqual(published["reportSections"][0]["href"], "/#existing")
            self.assertEqual(len(published["entities"]), len(self.map["nodes"]))

    def test_unknown_source_and_event_dates_remain_explicit_without_breaking_timeline(self):
        with tempfile.TemporaryDirectory() as temp:
            src, dist = Path(temp) / "src", Path(temp) / "site"
            src.mkdir(); dist.mkdir(); (src / "briefs").mkdir()
            data = copy.deepcopy(self.data)
            target = next(c for c in data["claims"] if c["status"] != "superseded")
            source_id = target["sourceIds"][0]
            next(s for s in data["sources"] if s["id"] == source_id)["publishedAt"] = None
            target["eventDate"] = None
            target["reviewedAt"] = None
            (src / "research_registry.json").write_text(json.dumps(data))
            (src / "map_source.json").write_text(json.dumps(self.map))
            (src / "research_ui.js").write_text("")
            (dist / "index.html").write_text('<h2 id="existing">Original heading</h2>')
            build_research(src, dist, lambda title, body, **kw: body)
            output = (dist / "synthesis.html").read_text()
            self.assertIn("Publication date not recorded", output)
            self.assertIn("Event or scheduled date: Not recorded", output)
            self.assertNotIn("None", output)

    def test_superseded_claim_keeps_its_synthesis_address_and_replacement_link(self):
        with tempfile.TemporaryDirectory() as temp:
            src, dist = Path(temp) / "src", Path(temp) / "site"
            src.mkdir(); dist.mkdir(); (src / "briefs").mkdir()
            data = copy.deepcopy(self.data)
            original = next(c for c in data["claims"] if c["status"] != "superseded")
            original["status"] = "superseded"
            replacement = {**copy.deepcopy(original), "id": "addressable-replacement", "status": "documented", "supersedes": original["id"]}
            data["claims"].append(replacement)
            (src / "research_registry.json").write_text(json.dumps(data))
            (src / "map_source.json").write_text(json.dumps(self.map))
            (src / "research_ui.js").write_text("")
            (dist / "index.html").write_text('<h2 id="existing">Original heading</h2>')
            build_research(src, dist, lambda title, body, **kw: body)
            output = (dist / "synthesis.html").read_text()
            self.assertEqual(output.count(f'id="claim-{original["id"]}"'), 1)
            self.assertIn('href="/synthesis.html#claim-addressable-replacement"', output)
            self.assertIn(html.escape(original["text"], quote=True), output)


if __name__ == "__main__":
    unittest.main()
