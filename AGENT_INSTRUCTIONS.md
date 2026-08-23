# THE ARCHITECTURE — Agent Instructions + Scheduled-Update Spec

Handoff document. Follow it exactly. Everything referenced ships in this package.

---

## 1. What this is

A single-page investigative report site — *The Architecture* by Kirk Musick — plus a weekly
evidence process that folds new material into it. The site is static: no framework, no build
step at deploy time, no server. The published page is one self-contained HTML file (~414 KB)
with the CSS inlined; Google Fonts is the only external dependency.

Live: <https://the-architecture-neurals.vercel.app/>
(`the-architecture-liard.vercel.app` is the project's former address and redirects here.)
Vercel project: `the-architecture` · Team: `zincdigitalofmiamis-projects` · no Git repository —
every deployment is a direct file upload from the Vercel CLI (see §3).
Dashboard: <https://vercel.com/zincdigitalofmiamis-projects/the-architecture>

The report is the product. **Nothing in the weekly process may soften, restructure, or
re-voice the existing text.** New material is appended in its own sections; corrections are
logged, never silently applied.

---

## 2. File map

```
site/                       ← THIS FOLDER IS THE DEPLOY. Nothing here needs building.
  index.html                  the whole report, CSS inlined, ~414 KB
  styles.css                  same CSS as a file, for the sub-pages
  neural.html                 the neural map page (generated from src/neural_map.html)
  map/svg.frag  map/data.json the map drawing + dossier data the page fetches at runtime
  sources.html                200-entry source archive, standalone
  briefs/2026-08-16.html      weekly brief 001, standalone
  robots.txt  sitemap.xml     public + indexed; /src/ is disallowed
  vercel.json                 static config, X-Robots-Tag: index, follow
  src/                        self-hosted copy of the working sources (below) plus this file
                              and MANIFEST.json — the weekly run pulls its working copy from
                              here: fetch /src/MANIFEST.json, then every listed path, and
                              check each SHA-256. Written by the build; never hand-edit.

src/                        ← SOURCES + GENERATOR. Regenerate only from here.
  master_report.md            221 KB — the master report, third edition (2026-07-19)
  update_part2.html           the appended weekly record: gap, week, node, corrections,
                              silence ledger, open threads
  sources_manifest.md         the 200-entry source index
  final.css                   the single stylesheet — the only place the look is defined
  briefs/2026-08-16.html      brief 001 source (reconstructed from the built sub-page; the
                              builder normalizes either form to the same bare body)
  briefs/_TEMPLATE.html       the shape every new brief must take
  neural_map.html             the neural map section (own <style>/<script>)
  neural_svg.frag             the map drawing  ┐ regenerated together by
  neural_data.json            the map dossiers ┘ `node src/build_neural_map.js`
  build_neural_map.js         THE map build step — reads map_source.json, runs mapgen.js,
                              writes the two files above. Node 18+, no dependencies.
  map_source.json             the canonical node/edge tables — the file you edit
  mapgen.js                   the layout + edge-grading engine build_neural_map.js calls
  build_neural_map.py         LEGACY, do not run — hardcoded 21-node tables, ignores
                              map_source.json, writes nothing the site uses (see its header)
  build_site3.py              the generator (v3.2)
  WEEKLY_RUN.md               the run book (v3): §0 gates and stop conditions, §A the eight
                              research agents (leaf agents — no nesting), §B the writing standard,
                              §C the exact in-run actions, §D the turnover written after the work
  brief_lint.py               enforces the canonical brief shape (= Brief 001) and the voice floor;
                              check.sh runs it on every brief, every build
  agents/1-elections.md …     the eight standing research specialists — job, standing instruction,
  agents/8-dockets.md         owned anchors, working routes, known traps, sweep areas, and the handoff
                              written to each by the agent that closed the previous run

check.sh                    the pre-deploy guards (no network) — the automated run calls this
deploy.sh                   build + check.sh + link + deploy: --prod (the weekly run), or no
                            flag = preview then --promote <url> (manual review)
pull_src.sh                 pulls the working copy from the newest READY deployment (preview
                            or production) and verifies every hash — the run starts here
AGENT_INSTRUCTIONS.md       this file
AUTOMATED_RUN_TASK.md       the Sunday scheduled-task text (v8, local Claude Code Desktop) that executes §5
```

### Deploy verbatim or regenerate — both are valid

- **Verbatim.** `site/` is already correct. From inside `site/`:
  `vercel link --team zincdigitalofmiamis-projects --project the-architecture --yes` once,
  then `vercel deploy --prod --yes`. The folder is named `site` and the project is named
  `the-architecture`; an unlinked folder plus `--yes` auto-links by folder name, which would
  create a stray project called `site` instead of updating the live one. `deploy.sh` does the
  link check for you.
- **Regenerate.** Only when `src/` changed. `python3 src/build_site3.py` rewrites `site/`
  in place. Requires Python 3 and `markdown` (`pip install markdown`). The script reads from
  its own directory and writes to `../site` — no absolute paths, no working-directory
  assumptions. `ARCH_ROOT`, `ARCH_DIST`, `ARCH_SITE_URL` override if the layout moves; the
  built-in `ARCH_SITE_URL` default is the live address above, so robots.txt and sitemap.xml
  come out right without setting anything.

Never hand-edit `site/index.html`. It is generated. Edit `src/` and rebuild.

---

## 3. Deploy configuration

| Setting | Value |
| --- | --- |
| Project | `the-architecture` (team `zincdigitalofmiamis-projects`, no Git repository) |
| Type | static output directory, **no build step**, no framework preset |
| What gets uploaded | the contents of `site/` only — `src/`, `deploy.sh` and this file stay out of the upload (the self-hosted copies under `site/src/` go up with it) |
| Automated deploy | **Straight to production, then verified.** The weekly run (a local Claude Code Desktop task on Kirk's Mac, v8) runs `./deploy.sh --no-build --prod` (link + `vercel deploy --prod --yes`) on the Mac's persisted `vercel login` session, then verifies the live address, then syncs the working copy back into the project folder and pushes it to GitHub (`ZINC-Digital-of-Miami/the-architect-neurals`, `main`) as the off-machine backup. No token file exists anywhere; `VERCEL_TOKEN` is honoured by `deploy.sh` only for non-interactive use elsewhere. The Vercel **connector** is not the transport for this site: its `deploy_to_vercel` call carries every file through the model's context, and `site/` is ~1.7 MB — far beyond what a single tool call can carry. |
| Reviewed deploy (manual) | `./deploy.sh` with no flags creates a *preview* and prints its URL; after review, `./deploy.sh --promote <url>` launches exactly that preview. Used for the initial go-live of a new package and for any change you want to see first; not part of the weekly run. |
| Working copy of record | the newest READY deployment of the project, preview or production (`pull_src.sh`), so a previewed-but-unpromoted week is never lost; the live alias is the fallback |
| Manual deploy | `./deploy.sh` (preview) then `./deploy.sh --promote <url>`, or `./deploy.sh --prod` to go straight to production; equivalently from inside `site/`: `vercel link --team zincdigitalofmiamis-projects --project the-architecture --yes` then `vercel deploy --yes` / `vercel deploy --prod --yes` |
| Root directory (dashboard) | empty — the upload *is* the site root |
| Install / build command | none — leave empty |
| Visibility | production **public**. Manual previews may stay behind Vercel Authentication (the project default). No password protection, no Trusted IPs. |
| Indexing | **allowed** — `robots.txt` allows all except `/src/`, `vercel.json` sets `X-Robots-Tag: index, follow`, every page carries `<meta name="robots" content="index,follow">` |

Do not add a `package.json`, a framework preset, or password protection. Any of the three
will change how Vercel treats the directory.

A deployment is not done until it is verified live: `GET /` on the live address returns 200
with the new masthead date, `GET /briefs/YYYY-MM-DD.html` returns 200, and
`GET /src/MANIFEST.json` carries the new date. (Manual previews sit behind Vercel sign-in
under the project's default protection; `vercel curl` reads through it for checks.)

---

## 4. Design tokens — do not re-invent the look

The look is defined once, in `src/final.css` (mirrored to `site/styles.css` by the build).
A deliberate single theme: white ground, large serif type, full-width shell with a left
sidebar and a dark top menu. Take every value from these variables.

```css
--paper:#ffffff  --ink:#17150f  --ink-2:#4c4a42  --ink-3:#8a877c
--rule:#e2dfd6   --rule-soft:#f4f2ec  --card:#fbfaf7
--tier-a-bg:#e9f1e5  --tier-a-fg:#2c5030  --tier-a-rule:#b9cdb2   /* A — primary record */
--tier-b-bg:#f6eed9  --tier-b-fg:#6f5716  --tier-b-rule:#dcc98f   /* B — two+ outlets  */
--tier-c-bg:#f1eae7  --tier-c-fg:#83655a  --tier-c-rule:#d6c4bc   /* C — rejected      */
--absent-bg:#eceef4  --absent-fg:#3f4c69  --absent-rule:#bcc6d9   /* verified absence  */
--dotted:#a34a2b  --accent:#8c2f1b  --link:#274d8f  --mark:#fff3c4
--nav-h:58px
```

- Body: `"Source Serif 4", Georgia, serif` · 19px · line-height 1.68 · `tabular-nums`.
- Headings (h1–h3): `--font-display: "DM Serif Display", Georgia, serif` at weight 400 — the
  display face from the report design system. DM Serif Display ships one weight; never set
  `font-weight: 600/700` on a heading (the browser fakes it and it shows).
- Mono (nav, kickers, meta, dates, h4 labels): `"IBM Plex Mono", ui-monospace, monospace`.
- Fonts load from Google Fonts — DM Serif Display (roman + italic), Source Serif 4 (400/600/700
  + italics) and IBM Plex Mono (400/500/600). Keep the `preconnect` pair.
- Existing classes to reuse rather than replace: `.tier a|b|c|abs`, `.correction` with
  `.was`/`.now`, `.clocks`, `.ledger`, `.rail`/`.stop`, `.card`, `.arch3`, `.part-open`,
  `.dek`, `.front-matter`, `.ed-note`, `.manifest`, `.lede-line`, `.mast`, `.mast-kicker`.
- No new colors, no second typeface, no dark mode, no framework. If a new element is
  genuinely needed, add one rule to `src/final.css` using the variables above.

---

## 5. The weekly scheduled update

Runs weekly, week ending Sunday. Output of the run is edits to `src/` plus one deploy.

0. **The neural map** (`/neural.html`) is part of the weekly surface. Its drawing and dossier
   data live in two generated assets — `src/neural_svg.frag` and `src/neural_data.json`,
   copied by the build to `site/map/svg.frag` and `site/map/data.json`. Node/edge changes are
   made by regenerating those two files from the map's node and edge tables (grades [A]/[B]/
   [C]/[O]; dotted stays dotted until a document closes it): edit `src/map_source.json`,
   then run `node src/build_neural_map.js` — which prints the new counts and the flags it
   set. (`src/build_neural_map.py` is legacy and regenerates nothing; do not run it.)
   Then update the "data state" date in `src/neural_map.html` (kicker,
   stamp), the node/edge counts, the "This window" chip strip, and the week ledger at the
   foot of the section.

1. **Gather** the week's material to the evidence rules in §6. The literal research-agent
   spawn prompts and the command-level procedure live in `src/WEEKLY_RUN.md` — §A is the eight
   prompts (spawned in ONE message; each agent is a leaf), §C the exact actions, §D the turnover
   written after the work. Follow it rather than improvising. Primary records first:
   dockets, filings (with accession numbers), roll calls, agency decision documents,
   contract solicitations, FOIA responses.
2. **Write the brief.** Copy `src/briefs/_TEMPLATE.html` to
   `src/briefs/YYYY-MM-DD.html` (the week-ending Sunday). Keep the `<body>` wrapper —
   the build strips everything outside it. The shape is Brief 001's and is enforced by
   `src/brief_lint.py`: eight `<section>`/`<h2>` blocks — The lede · Architecture I — The family
   money · II — Executive power · III — The wars and the count · The node where the architectures
   touch · What would change the tier · Rejected below [B], with reasons · Next week's priorities.
   Voice per `WEEKLY_RUN.md` §B: declarative, dated, sourced; bolded topic leads; no lists.
3. **Update `src/update_part2.html`** — this is the page's live record:
   - `#u-week` — replace with the new week; move the outgoing week's substance into the
     brief archive (it is already there via step 2) and keep only what still carries.
   - `#u-node` — the node diagram, if the week changed it.
   - `#u-corrections` — **append only.** Never delete or reword an existing entry
     (see §7). Number sequentially: C-005, C-006, …
   - `#u-silence` — advance every clock's day count and the `clocks-asof` date. A week
     with no answer is a finding: the count goes up, the entry stays.
   - `#u-threads` — retire threads that resolved (state how), add the new next checks.
4. **Update the nearest-dates rail** in `src/build_site3.py` (`rail_stops`): drop dates
   that have passed, add newly docketed ones, keep `NOV 3` flagged `big` until it passes.
5. **Rebuild:** `python3 src/build_site3.py`. Brief numbering, the edition number, the
   masthead date, the archive list, the per-brief pages, and `sitemap.xml` all derive from
   the contents of `src/briefs/` — nothing to bump by hand.
6. **Check** before deploying: `site/index.html` exists and is > 350 KB; it contains
   `id="u-corrections"`, `id="u-silence"`, `id="u-threads"`, `id="brief-001"`, `id="sources"`;
   the new brief resolves at `/briefs/YYYY-MM-DD.html`; the four permanent corrections in §7
   are still present in substance (the C-002 ExodusPoint figure `$1,269,843` must appear);
   `site/src/MANIFEST.json` exists; `robots.txt` disallows `/src/`; `sitemap.xml` carries the
   live address; and no `class="content"` appears more than once (a nested wrapper means a
   brief was ingested without unwrapping). `deploy.sh` asserts all of this.
7. **Deploy to production, then verify.** Automated runs (v8, local) run
   `./deploy.sh --no-build --prod` on the persisted CLI login, then fetch `/`, the new brief page
   and `/src/MANIFEST.json` from the live address and confirm the new date is what is serving;
   on success they commit and push the synced tree to GitHub. If the CLI is not logged in or
   errors, or verification never passes, the run does **not**
   stop: it packages the rebuilt tree as `THE_ARCHITECTURE_deploy_YYYY-MM-DD.zip`, presents
   it as the run's output file, and says plainly in its notification that the site is
   **not live** and why. Never report a launch that was not verified.

The automated weekly task that executes this section is kept beside this file as
`AUTOMATED_RUN_TASK.md`; the task text and this spec must agree, and this spec governs.

The master report itself (`src/master_report.md`, third edition, 2026-07-19) is **frozen**.
It changes only in a numbered new edition. Weekly material never edits it; where the weekly
record supersedes a line in it, that is handled by the inline edition-note mechanism at the
top of `build_site3.py` (`notes`), which annotates without rewriting.

---

## 6. Evidence rules

These are the report's spine. They are not style preferences.

- **[A] Primary record cited directly**, or an on-the-record admission — the docket entry,
  the roll call, the filing itself, the agency's own decision document.
- **[B] Two or more genuinely independent named outlets** with the primary record
  identified. Syndications of one wire story count as one origin. Origins are counted,
  not headlines.
- **[C] Single outlet, anonymous, or aggregator — rejected**, with the reason stated.
  Rejections are published, not hidden.
- **ABSENT: checked for and not found.** A verified absence is a result, not a gap. Some of
  the report's most important findings are absences. Say what was searched.
- **Dotted edges.** A documented sequence is never asserted as a proven cause. Where two
  facts sit suggestively close, the edge is drawn dotted and labeled, and stays dotted until
  a document closes it.
- **Denials, with scope.** Every denial stays attached to its allegation and is read for
  exactly what it denies. A knowledge-qualified denial, a motive-only denial, and a narrow
  denial beside a broad one are each findings.
- **Structure, not intent.** Report what was built and when. Private positions stay
  separated from government actions.
- **Corrections are permanent.** Logged with date and ID, was/now, and the tier of the
  record that forced the correction.
- **Context, not claims.** When a premise fails the record — no docket, filing, roll call or
  decision document supports it — the rejection stands, and it is followed by validated
  context: what the primary record *does* show [A], then what two or more independent named
  outlets report about the circumstances the premise was pointing at [B], each outlet named
  with its date. The context never restates the rejected claim as fact and never supplies a
  motive; it explains the surrounding facts so the reader can see why the premise arose.
  Applies to every rejected item and every verified absence. If no sourced context exists,
  the entry says so. Context is appended as a new dated entry (or a dated line under the
  item), never by rewording the original.

Tone: declarative, dated, sourced. No speculation about motive, no rhetorical escalation,
no adjectives doing an evidence tier's work.

---

## 7. The four permanent corrections — never revert

Logged 2026-08-16, tier [A]. Earlier drafts and the wider tracking corpus carry the "was"
versions. If any of them reappears in the site, the build is stale or a regression shipped.
Context lines are appended under an entry (dated), never folded into its original text.

| ID | Was | Now (correct) |
| --- | --- | --- |
| **C-001** | Eric Trump joined the ALT5 Sigma board per the company's 8/13/25 release. | **Never seated.** Aug 29, 2025 8-K (acc. 0001641172-25-026082): designated *observer* "after discussion with The Nasdaq Stock Market LLC." Zero proxy occurrences; no Form 3. |
| **C-002** | ALT5 raised $1.5B including $750M from Point72 and ExodusPoint. | **$750M cash + $750M in WLFI tokens from World Liberty itself** as "Lead Investor." Point72 Q2-26 13F: no position (only-ever exposure $1.08M of Q3-25 calls). ExodusPoint Q2-26 13F-HR (acc. 0001736225-26-000010, period 6/30/26, filed 8/14/26): 2,170,301 sh of "AI FINL CORP" (CUSIP 47089W104 = ALT5 Sigma, CIK 862861) worth **$1,269,843** — 0.008% of a 1,510-position, $15.53B book. A rounding error, not "no position." |
| **C-003** | An AG swearing-in was postponed over Republican dissent. | **No record supports postponement.** Blanche confirmed Sat Aug 8, 4:17 a.m. (50–49–1, roll call #230, PN1078; Collins and Murkowski no; McConnell not voting); sworn in Mon Aug 10 by Third Circuit Judge Emil Bove. The only anomaly in evidence is press exclusion from the ceremony. **Context added 2026-08-22 [B]:** the margin was the narrowest available — a 53–47 majority with McConnell absent since a June fall and every Democrat opposed left room for two defections (Roll Call, CBS, NPR, Aug 8); Collins (Aug 4) and Murkowski (Aug 7) defected over the department's independence — the $1.8B "anti-weaponization" fund, the IRS-settlement audit immunity for the president and family, the Epstein-files release, the targeting of former staff and sitting senators (ABC, CBS, Roll Call, The Hill); Cornyn and Tillis had conditioned their votes on a written rescission of the fund and a rewrite of the immunity language, Tillis also on a meeting with Epstein survivors (NPR, PBS, Daily Caller); Cassidy, the last undecided Republican, announced yes on Aug 7 and was the deciding vote (CNBC/Reuters, CBS, NPR); the vote came in an overnight session before the August recess (PBS, ABC). What the premise likely described was the weeks-long hold-up of the confirmation vote, not a postponed swearing-in. |
| **C-004** (minor) | AIFC going-concern filing dated 5/19/26; market cap < $60M. | **10-Q filed 5/18/26.** "<$60M" unanchored — primary-record math gives ~$74M at 6/30/26. >90% decline confirmed (−92.2%). |

Also keep distinct, permanently: ALT5 Sigma **is** AI Financial Corp (one SEC registrant,
CIK 862861, renamed April 2026); Zach Witkoff (WLF CEO, trust-bank president, ALT5 chairman)
is not Steve Witkoff (special envoy, OGE disclosure uncertified); DT Marks DEFI LLC is not
DT Marks SC LLC.

---

## 8. Failure modes to avoid

- Rebuilding the site from scratch, or "improving" the layout. The design is settled.
- Hand-editing `site/index.html`, then rebuilding — the edit is lost.
- Rewording or dropping a corrections entry, or resetting a silence clock.
- Letting a [C] item into the record without its rejection reason.
- Adding a framework, a `package.json`, password protection or Trusted IPs to the Vercel project.
- Changing the URL shape. `/`, `/sources.html`, `/briefs/YYYY-MM-DD.html` are indexed.
