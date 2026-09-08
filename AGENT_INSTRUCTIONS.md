# THE ARCHITECTURE — Preservation and Codex operating instructions

These instructions govern research and publication. The owner's current directions take
precedence. The approved responsive site, Topics navigation and evidence map are a new
presentation of a protected accumulated report, not permission to rewrite that report.

## 1. Authority and identity

- Canonical repository: `https://github.com/ZINC-Digital-of-Miami/the-architect-neurals.git`,
  **live remote main**, queried with `git ls-remote origin refs/heads/main` before decisions.
- Live delivery: `https://the-architecture-neurals.vercel.app/`.
- Vercel project: `the-architecture`; scope: `zincdigitalofmiamis-projects`.
- Saved project: `/Users/zincdigital/Documents/the architect neural`.
- The report is Kirk Musick's accumulated work. Read its original source before making a
  claim about it; distinguish its historical assertions from newly verified findings.

Local refs, plans, agent summaries, preview deployments and published source copies are
leads and delivery evidence. They never replace live main as repository authority. Do not
copy older deployed instructions over current repository instructions. Only release an
artifact whose source change has already landed on main through the repository release path.

## 2. Preservation contract

`preservation/baseline.json` freezes the original commit and content hashes of the master,
source index and existing briefs, plus exact correction blocks and historical map records.
`python3 scripts/preservation.py check` is mandatory. Never recreate or weaken the baseline
to make a change pass. The original commit is the recovery source; the baseline is the
integrity inventory. A future numbered master edition requires a separate, explicit owner
decision and preservation of the preceding edition.

Every run also captures `.architecture/base-preservation.json` in its isolated candidate,
so all briefs and corrections present on that run's base main remain protected, including
those created after the initial migration. Existing correction HTML stays verbatim and in
order. Context is a new dated sibling block, never an inline rewrite. New sources go into
`src/research_registry.json`; do not rewrite the historical source checklist. Existing map
nodes, edges, labels and grades remain as historical records; use reviewed registry versions
for later evidence or a changed interpretation.

## 3. Files and responsibilities

- `src/master_report.md`, `src/sources_manifest.md`, dated `src/briefs/`: preserved sources.
- `src/update_part2.html`: current summary, permanent correction ledger, clocks, open checks.
- `src/map_source.json`: preserved legacy node and edge records.
- `src/research_registry.json` and `src/research_registry.py`: versioned topics, sources,
  entities, claims, relationships, watchpoints and reviewable retrieval feedback.
- `src/build_site3.py`, `src/build_neural_map.js`, `src/build_research.py`: generators.
- `src/final.css`, `src/neural_map.html`, `src/research_ui.js`: presentation and interactions.
- `site/`: generated, reviewed static artifact committed before deployment. Never hand-edit.
- `scripts/preservation.py`, `scripts/weekly_run.py`, `scripts/release.py`: integrity, durable
  run ownership/coverage, exact-main publication and live-byte verification.
- `.architecture/`: private candidates, run state, locks and release receipts; git-ignored
  and excluded from public export. No credentials belong in its logs or anywhere in source.

Use existing installed Python/Node/CLI capabilities. Scripts do not install dependencies,
create alternative remotes, overwrite drafts or synchronize with deletion.

## 4. Scheduling and release

The authoritative Codex task prompt is `AUTOMATED_RUN_TASK.md`; the in-run procedure is
`src/WEEKLY_RUN.md`. The actual scheduler record is separate and must be freshly inspected.
Sunday 07:00 **America/Chicago** is the due boundary, including DST. A daily status check
permits catch-up without daily research. The oldest uncovered Sunday is processed first.
A dispatch timestamp, a written draft, a preview, or a successful push does not advance
successful-publication coverage.

Start through `scripts/weekly_run.py start`; its persistent token lock protects a single
writer across tool calls. Never steal another run's token or automatically discard a stale
attempt. Resume that run, or explicitly record its failure and reason before retrying.

`pull_src.sh NEW_DIRECTORY` acquires exact live main into a new candidate without overwriting
anything. Build, check, inspect the full diff and original evidence, and stage its hashes.
Integrate only reviewed changes; account for every intervening main change. Land on main,
then `./deploy.sh --prod --run-token TOKEN` uploads its committed artifact from an isolated
copy. Main is checked before upload and promotion and after live verification. Public
`release.json` is generated only in the isolated artifact to identify the already-existing
main commit; no circular commit hash is written into tracked files.

`weekly_run.py complete` independently verifies the receipt against current main, all public
bytes and the exact staged candidate before advancing coverage. Failures retain evidence.
The script never treats deployment success as permission to overwrite the repository.

## 5. Research, learning and presentation

Topics/categories, not hardcoded menu lists, drive discovery and the map. Registry helpers
may suggest topic membership from explicit retrieval feedback and propose new questions.
They never autonomously change historical prose, erase evidence, promote grades, or turn
co-occurrence into a causal link. Validate transitions against the original registry and
require an evidence review before accepting claims or publishing new relationships.

Political research must be neutral, factual and attributed. Distinguish official actions,
stated reasons, and hypotheses. Do not invent private motives, collective control, political
probabilities, recommendations, or quantitative scores for officials, parties or candidates.
Respect legal-entity identities and dates; former employment alone proves no current mandate.

The approved redesign may change layout, responsive navigation, Topics, search, accessible
controls and map exploration. Preserve existing anchor URLs and archived reading routes.
Keep all old content recoverable, keyboard operation, reduced motion and mobile readability.
No source credential, private retrieval log or runtime lock may enter the public source export.

The following historical evidence rules and correction descriptions are retained for
continuity. They describe the existing corpus; they do not establish that an assertion was
freshly reverified in this run. Prospective structured records must satisfy registry validation
and actual original-source inspection as well.

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
is not Steve Witkoff (special envoy; preserve the dated agency/OGE certification distinction in C-010); DT Marks DEFI LLC is not
DT Marks SC LLC.

---

## 8. Failure boundaries

Stop publication on preservation failure, a missing original source needed for a claim,
identity ambiguity, changed main, mismatched candidate, failed live-byte verification, or
another writer's active lock. A limited research return must state the unmeasured scope;
it must not declare a comprehensive audit or a verified absence from a blocked fetch.
Never weaken a check to admit a desired conclusion. Keep failed candidates and receipts,
report the exact stage, and preserve the last verified publication watermark.
