# THE ARCHITECTURE — Codex weekly run book

`AGENT_INSTRUCTIONS.md` governs preservation and evidence; `AUTOMATED_RUN_TASK.md` is the
reviewable task prompt. This procedure replaces the former Claude-specific deployment-first
workflow. Historical instructions remain recoverable in Git, beginning at the preservation
baseline's `source_commit`. The eight specialist files remain research inputs, not authority
to violate these current instructions or to claim that an unexamined record is current.

## A. Establish the actual interval and source

Run from the saved project:

```sh
python3 scripts/weekly_run.py status
python3 scripts/weekly_run.py start
```

Use the returned token and candidate path. `week_ending` is the **oldest due Sunday**, not
this machine's date or the next Sunday. `window_after` is the last verified publication,
exclusive. Sunday is due at 07:00 America/Chicago. DST, missed dispatch and late launch are
handled by the script. If current, remain quiet; if another run owns the lock, inspect and
resume that attempt rather than compete with it. Never infer successful research from
`lastRunAt`, `lastScheduledFor`, a preview date or a draft file.

The acquisition queries live remote main and creates a new exact candidate. It never pulls
Vercel as source or overwrites local work. Read all governing files and current specialist
handoffs in that candidate. A private per-run preservation baseline includes every prior
brief/correction/map record, including publications newer than the migration baseline.

## B. Research from records and challenge conclusions

Run `python3 src/research_registry.py queue` in the candidate. Review all active topic
questions, open checks and time-sensitive source windows. Plan bounded independent leaf
research responsibilities using the eight domains below as expertise, and add cross-domain
questions from the registry where the evidence warrants them. This instruction explicitly
supersedes the archived "eight agents in one message" rule and hardcoded topic allocation.
The current runtime has four total slots including the coordinator. Keep three independent
`gpt-5.6-sol` researchers at `max` reasoning on bounded assignments while research work
remains, reusing completed workers for the next uncovered question. Finish when coverage
and verification are complete; do not create filler assignments. Assign work from the registry queue, overdue checks, newly found
records and coverage gaps; cover all topic areas in a coverage ledger and say exactly which
areas could not be checked. The eight files are source-route references, not eight required
simultaneous spawns or eight immutable topic boundaries. Codex's semantic research proposes
new questions/topics and uses reviewed feedback; the term-matching helper is only a retrieval
aid and does not itself constitute neural research or evidence of a connection.
Researchers must not delegate further or write shared sources.
Each packet records successful source routes, rejected candidate matches, counterevidence,
and a next disconfirming check. Admit reviewed feedback to the registry and use access
failures to select another route. Retain a dated coverage ledger. Learning here means
improved retrieval and question selection, not model training or automatic truth promotion.

| Domain | Standing source |
|---|---|
| Elections and administration | `src/agents/1-elections.md` |
| Executive power and legal authority | `src/agents/2-executive-power.md` |
| Conflicts and official decisions | `src/agents/3-wars.md` |
| Epstein records and DOJ compliance | `src/agents/4-epstein-doj.md` |
| Detention and enforcement | `src/agents/5-detention.md` |
| Succession and official disclosures | `src/agents/6-succession.md` |
| Finance, ownership and EDGAR | `src/agents/7-money.md` |
| Dockets and court records | `src/agents/8-dockets.md` |

Each responsibility must state the actual research need, source scope, dates, identities,
expected original records, counterevidence to seek, and concrete completion evidence. Return
rows with claim, document/date/URL or accession, source type, independently counted origins,
exact attributed statement, counterevidence/denial and its scope, and unresolved limitations.
The coordinating researcher opens every material original and checks date, unit, identity,
context and alternative explanations. An agency statement establishes what it states; it
does not independently prove every underlying assertion. Syndicated copies count as one
origin. A docket access failure is an access failure, not proof that no filing exists.

Use neutral factual political reporting and no politician/party scores, election forecasts
or unsupported motive claims. Keep private positions, government actions, chronology and
causation distinct. Uncertain relationships remain explicit questions. Review documents
that challenge a priority hypothesis as carefully as those that appear to support it.

## C. Propose learning and preserve the historical corpus

The registry's `suggest` and `feedback` commands write separate proposal files. Accepted and
rejected matches may improve retrieval and topic assignment; no helper publishes by itself.
Record topic relevance as `purpose: topic_fit`, source access as `source_route`, and claim
judgments as `evidence_review`. Only topic-fit feedback changes term matching. A rejected
claim or failed source route must never suppress later retrieval about that subject.
Evaluate proposed categories, topic merges/splits, entity identities and relationship
versions. Validate a proposal against its original registry using:

```sh
python3 src/research_registry.py validate --registry PROPOSAL.json --previous ORIGINAL.json
```

A new topic or adjacency is a research lead until its source and claim are reviewed. Preserve
all historical IDs, grades and records; do not silently reassign or erase an edge. Store new
source URLs and structured evidence in the registry, leaving `sources_manifest.md` unchanged.
Retain prior master text and every existing brief byte for byte.

Write one new dated brief with the existing template and eight section headings. Use dated,
attributed paragraphs, supporting records and specific limits. Do not add unverified filler
to satisfy length or source-count expectations; if evidence cannot support the required
brief shape, retain the candidate and report the editorial gate needing attention. Every
rejection needs a reason; an absence must identify the actual search and its coverage.

Update only the current weekly summary, node summary, clocks and open checks as appropriate.
Keep original correction HTML exactly intact and in order. Append context as a separate
`.correction` block carrying an ISO date and the existing correction ID; new correction IDs
must be unique except for explicitly labeled context blocks. Never fold context into the
original correction, or lower/reset an unanswered clock to conceal a missed run.

## D. Build, review and stage

In the isolated candidate, regenerate with the existing source builders, then run:

```sh
python3 src/research_registry.py validate
bash check.sh
python3 scripts/test_guards.py
```

Inspect the complete diff and the actual report, Topics, sources, archived briefs and map on
desktop and mobile. Verify keyboard selection, search/filter behavior and back-to-top/menu
controls. Check each new public claim against its original record. Confirm preserved text,
correction blocks, old map records, dates and source coverage. A passing linter is not
validation of a claim or of complete research coverage.

From the saved project, stage the candidate:

```sh
python3 scripts/weekly_run.py ready --token TOKEN
```

This verifies the dated brief and current-through value and records exact artifact hashes.
If any candidate file changes after review, rerun checks and `ready` before release.

## E. Land main, publish exactly, then record coverage

Integrate reviewed changes on a `codex/` feature branch through the repository release path.
Query live main again and account for intervening changes. Never overwrite another writer's
work or use a deleting sync. Only a clean checkout whose HEAD equals freshly queried live
main may deploy. Generated `site/` must already be reviewed and committed; the deploy wrapper
does not rebuild or install anything.

```sh
./deploy.sh --prod --run-token TOKEN
python3 scripts/weekly_run.py complete --token TOKEN --receipt RELEASE_RECEIPT.json
```

The release wrapper deploys an isolated exact-main artifact without automatically promoting
it, checks its bytes, rechecks main, promotes it, and verifies the live alias. Its private
receipt contains source/deployment identity and every public hash. `complete` rechecks that
receipt against the staged candidate, live main and served bytes before advancing successful
coverage. Only then may another interval begin. A failure after main or deployment is
reported at that exact stage; do not relabel it as a completed week or erase its candidate.

## F. Failure, recovery and handoff

Keep the active candidate during a recoverable interruption. `status` returns its token,
phase and path. Resume the same attempt. Only before `completion.json` exists may a failed
attempt be explicitly abandoned:

```sh
python3 scripts/weekly_run.py fail --token TOKEN --note 'Exact measured failure and next action'
```

The attempt receipt remains; the publication watermark does not change. `start` retries the
same oldest missing interval in a new directory. Never auto-delete an abandoned draft or
steal a live run's lock. Record research routes, rejected premises, unresolved questions,
source-access limits, topic proposals, reviewer decisions, changed anchors, and the next
source check in the run receipt and reviewed specialist handoff. External Drive/artifact
writes and messages require explicit authorization for that destination.

Notify only on meaningful review-ready findings, verified publication, failure or required
owner action. Include the actual covered Sunday, canonical SHA and receipt path. Never call
an unchanged status check a weekly pull, or a dispatch a completed publication.

If the attempt has `completion.json`, publication completion is already in progress. Do not
abandon it with `fail`: rerun `complete` with the same token and receipt. Its durable intent
records the exact staged artifact and before/after watermark; fresh main/served-byte checks
must pass again before recovery finishes remaining receipt and lock writes. Failure evidence
is retained under `completion-errors/`, and another interval cannot begin until recovery.
An advanced watermark alone is insufficient. If main or the exact receipt has changed,
retain the pending intent for explicit reconciliation rather than failing/restarting it.
