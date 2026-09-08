# Preserved research platform — approved implementation

The owner approved the desktop/mobile report, map, Topics and Synthesis concepts and
authorized execution on September 8, 2026. The authorized result includes the new
interface, source-aware evolving topics, a robust weekly Codex workflow, and retirement
of the matching Claude Sunday schedule after verification. This approval supersedes
the earlier design freeze; it does not authorize rewriting the accumulated report.

## Invariants

- Live GitHub `ZINC-Digital-of-Miami/the-architect-neurals` main is canonical.
- Preserve the master report, source index and already published briefs byte for byte.
- Preserve original correction entries and legacy map identities, relations and grades.
- Add new research as separately dated source-linked records; never infer causation
  from proximity, co-occurrence, common names or a graph layout.
- Keep original public URLs, anchor identities and archived publications reachable.
- Use the existing static Python/JavaScript architecture, no new framework or packages.
- Keep political content factual, attributed and source-cited. No political scores,
  candidate rankings, election forecasts, or unsupported statements of motive.
- Existing authored interpretations remain preserved historical text. New synthesized
  views distinguish them from newly verified original records.
- Keep one production writer; no schedule cutover before preservation and rehearsal pass.

## Design

Visual thesis: the approved editorial paper/serif report remains the primary reading
surface; restrained red navigation and a dark/gold map support long-form research.
Content plan: preserved report; current record; editable Topics; evidence-based Synthesis;
source-linked map exploration; complete archives and source access.
Interaction thesis: responsive menu/contents disclosure, persistent reading position,
reduced-motion-aware reading progress, keyboard-accessible map selection and zoom.

## Ownership and interfaces

1. Shared UI: `src/build_site3.py`, `src/final.css`, `src/site_ui.js`.
   Exposes `render_page(title, body_inner, active=..., sidebar_html=...,
   description=..., page_class=...)` and calls
   `build_research(ROOT, DIST, render_page)` before sitemap/manifest generation.
2. Map: `src/neural_map.html`, with generator edits only if required. Consumes existing
   `/map/data.json`, `/map/svg.frag` and new `/research/data.json`.
3. Research data/pages: `src/research_registry.json`, `src/research_registry.py`,
   `src/build_research.py`, `src/research_ui.js`. Generates `/topics.html`, topic detail
   pages, `/synthesis.html`, `/research/data.json` and the report outline.
4. Preservation/run/release: `preservation/`, `scripts/`, `check.sh`, `deploy.sh`,
   `pull_src.sh`, and run instructions. External schedules are changed only by the root.

Registry contract: categories have `id,title,description`; topics have
`id,title,description,categoryIds,entityIds,status,reportLinks,researchQuestions`;
sources retain publisher, date, exact URL and source type; claims retain source IDs,
statement scope, dates, status and context. Legacy map relation citations stay empty
unless independently verified. Topic proposals and accepted/rejected feedback are
recorded separately; semantic research is performed by the scheduled Codex researcher.

## Execution and acceptance

- [x] Freeze and validate original preservation baseline; prove prohibited changes fail.
- [x] Implement shared report chrome and responsive layout without rewriting source prose.
- [x] Implement editable topic registry, complete report outline, source-linked detail pages,
      synthesis timeline/comparison/check views, and candidate/feedback validation.
- [x] Implement searchable map, topic filters, keyboard/list access, focus links and zoom.
- [x] Implement exclusive weekly run state, Sunday Chicago dates, resumable candidates,
      separate successful-publication receipts, source coverage and bounded retries.
- [x] Run full project guards, registry/guard failure tests and JavaScript/Python checks.
- [x] Verify rendered desktop/mobile routes, menus, anchors, filters, map and source links.
- [x] Review every changed hunk/full enclosing function and resolve identified failures.
- [ ] Commit reviewed change, land through GitHub main, deploy exact main and directly
      verify public output and protected content digests.
- [x] Prepare Codex schedule paused and verify its stored prompt/configuration.
- [ ] Schedule cutover is ON HOLD at the owner's September 8 direction. Do not inspect
      or change Claude accounts/schedules. Keep the Codex replacement paused.
- [ ] Remove the delivered feature branch after live verification; retain release evidence.

Weekly collection must cover the source gap since the last verified published window.
The design release must not invent a missing weekly brief or advance a research watermark
just because the UI changed. A source's publication date, event date and review date remain
different fields. Archive transport and source retrieval failures must be explicit.

## Implementation review, September 8

The Cast now separates 19 principal people already present in the retained report from
six companies/vehicles. Donald Trump Jr. and Eric Trump each have their own entry.
The four most connected existing map hubs have a slow pulse with pause/resume and
reduced-motion support. The owner retained existing colors with maroon Topics submenu
links; the later request to recolor all links was withdrawn before implementation.

Independent reviews compared every scoped changed hunk and enclosing function. The
master/source index/three briefs, 17 correction blocks, 31 map nodes and 62 legacy edges
remain protected. A clean isolated rebuild must match every generated public path/byte.
Interrupted weekly completion retains a durable intent and revalidates the exact receipt
before recovery. Live main is checked both before and after receipt verification.
The design release retains weekly coverage through August 30; September 6 remains due.

Final local checks: 37 workflow/preservation regression tests and 23 research/reader
tests passed; all 22 generated pages have unique IDs and resolving local links/anchors.
Fourteen browser measurements across seven route types at 390px and 1280px showed no
document overflow. Browser interaction checks covered mobile menus and dossiers,
search and empty results, map zoom/pan/fit, entity links, four hub pulses and pause/resume,
synthesis claim links/tabs, saved Timeline restoration and Top reaching scroll position 0.
Reduced-motion CSS was inspected; the operating-system preference was not changed.
