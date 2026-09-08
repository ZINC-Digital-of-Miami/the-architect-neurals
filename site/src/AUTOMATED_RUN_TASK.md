# THE ARCHITECTURE — Codex weekly research and publication

This is the reviewable operating prompt for the Codex automation. The actual automation
record is managed in Codex; this file does not prove that a schedule is installed or enabled.
The former Claude task `architecture-sunday-run` must be disabled only as part of the
owner-authorized cutover, after the Codex replacement and recovery path are verified.
Do not change any other Claude task.

## Purpose and authority

Maintain Kirk Musick's preserved report and its source-linked research map. Live GitHub
`ZINC-Digital-of-Miami/the-architect-neurals`, branch `main`, is canonical. Vercel is delivery
evidence. Never pull a preview or the published `/src/` directory as the working authority.
Never overwrite active local work, force-push, sync with deletion, deploy before main, or
publish material solely because another agent reported it.

Read `AGENT_INSTRUCTIONS.md`, `src/WEEKLY_RUN.md`, `preservation/README.md`, and the most recent
completed run receipt before research. Inspect the original sources and then-current source
records. Existing report text, source checklist, prior briefs, corrections and map history
are protected by machine checks, independently of presentation changes.

## Due time, catch-up, and ownership

The research interval ends **Sunday at 07:00 America/Chicago**. The script handles daylight
saving time and late dispatch. A lightweight daily check may call `status`; it does not
perform extra daily research. Use the oldest missing Sunday first. Never date a brief in
the future, infer success from dispatch, or skip an interval when the app was unavailable.

1. Run `python3 scripts/weekly_run.py status` from the saved project. If no Sunday is due,
   remain quiet. A status check does not create a run or advance coverage.
2. If an active run exists, inspect its receipt and candidate. Resume only that same owned
   run with its token. Never steal a lock, start a duplicate writer, or delete a draft.
   An interrupted attempt can be explicitly failed with its token and an exact reason;
   failed attempts remain on disk for review, and the same interval stays due.
3. Run `python3 scripts/weekly_run.py start`. It checks the clean repository, acquires the
   exclusive writer lock, resolves live GitHub main twice around acquisition, and creates
   an isolated candidate under `.architecture/runs/<Sunday>/<token>/candidate/`. Record
   `token`, `candidate`, `source_commit`, `window_after`, and `week_ending` from its output.
4. If publication state is uninitialized, stop research and report that cutover bootstrap
   is incomplete. The owner initializes it once using a freshly verified production
   receipt: `python3 scripts/weekly_run.py bootstrap --receipt <release-receipt.json>`.
   Never initialize from Claude `lastRunAt` or a last-scheduled timestamp.

## Research and review

Work exclusively in the candidate. Run `python3 src/research_registry.py queue` there.
The dynamic registry supplies topic questions and open checks; the eight specialist files
provide domain expertise, not a fixed limit on what the topic registry may discover.
Cover current evidence for the requested topic priorities without presuming their conclusions.

Every agent assignment has a hard ten-minute wall-clock limit, including research,
verification and handoff. Give it one narrow question, owned output paths and a concrete
completion criterion. Record its start time and deadline; interrupt it at the deadline
if unfinished. Save evidence incrementally. Do not extend the limit, repeatedly tell it
to finish, or restart the same broad assignment. The coordinator integrates existing
results and narrows any genuinely necessary follow-up. Keep prompts concise.

The current four-slot runtime includes the coordinator. Use three independent leaf
researchers with `gpt-5.6-sol` and `max` reasoning while bounded research work remains;
reassign a completed worker to the next uncovered question. Do not manufacture work once
research and independent verification are complete. This supersedes the archived
eight-at-once Claude rule. Allocate their
work from the registry queue, overdue checks, new records and the coverage ledger. Retain
the eight domain playbooks as source-route references, and document coverage and unexamined
areas for every active topic. Codex performs semantic research and proposes new topics;
the term-matching helper is only a retrieval aid, never evidence of a relationship.
Use bounded independent leaf researchers within that concurrency, then verify each
material finding against the original record in the coordinating task. Record queries,
source URLs, access times, document dates, exact identities and units, unsuccessful routes,
contradicting evidence, and the limits of each claim. Distinguish an unavailable source from
an inspected source that did not contain the expected record. Do not label a failed fetch
as proof that a relationship or event does not exist.

Each packet must include retrieval feedback: which original-source route answered which
question, which candidate match was rejected and why, and the next record that could
disprove the conclusion. Feed reviewed accept/reject examples back into the registry;
use failed routes to change the next query or source, rather than repeating them unchanged.
Separate feedback purposes: `topic_fit` changes topic matching, `source_route` records access
results, and `evidence_review` records claim judgments. An unsupported claim or failed fetch
must not teach retrieval to avoid that subject; a later original may resolve the connection.
Normalize incoming origin IDs against the existing registry before admission. Different
article dates, packet labels or URLs from the same wire do not create independent origins.
Keep a dated coverage ledger and propose new topics only when the evidence exposes a
distinct question. This improves retrieval and research planning; it does not train model
weights or allow the system to certify its own claims.

Keep people, legal entities, topics, claims, sources, and dated relationships distinct.
For political material, use neutral factual reporting and attribution: no political
preferences, politician/party scores, election probabilities, inferred private motives, or
claims of control inferred from proximity or former employment. Preserve legacy material
without silently revalidating its assertions.

`research_registry.py suggest` and `feedback` write separate review candidates. They may
improve retrieval and topic assignment from accepted/rejected corrections; they do not
publish new facts or change historical grades. Validate any proposed registry using
`python3 src/research_registry.py validate --registry <candidate.json> --previous <original.json>`.
A reviewer must inspect proposed topics, sources, identity matches, claims and relationships.
Do not auto-promote a source grade or interpret semantic similarity as evidence of causation.

## Candidate publication

1. Write one new `src/briefs/<week_ending>.html` using the existing template and writing
   rules. A retry that already has this brief from main must inspect and preserve it,
   not recreate or overwrite it. Record limited coverage honestly; never pad to a quota.
2. Update the weekly record's current summary, clocks and open checks. Preserve every
   existing correction block verbatim and in order. Add dated context as a separate
   appended `.correction` block with its correction ID. Keep original source-index bytes;
   new source records belong in the structured registry. New evidence about a historical
   map edge belongs in a versioned registry relationship; the old edge and grade remain.
3. Build the candidate with the existing Node and Python environment, then run `bash check.sh`
   and `python3 scripts/test_guards.py`. No dependency installation or check weakening.
4. From the saved project, run `python3 scripts/weekly_run.py ready --token <token>`.
   This checks the candidate and saves the exact proposed public artifact hashes. Review
   its diff, source records, date/window, mobile UI and graph behavior before release.
5. Integrate the reviewed candidate on a `codex/` feature branch through the repository's
   release path. Reconcile against freshly queried live main; if it changed, rebase or
   re-create the candidate without discarding another writer's changes, rerun checks and
   restage. Never use `rsync --delete`, `git add -A` over an uninspected tree, force-push,
   an alternate remote, or a deployment as a substitute for main.
6. Only after the change is on live main and the clean checkout matches its SHA, run
   `./deploy.sh --prod --run-token <token>`. The wrapper uploads an isolated copy of that
   committed artifact, verifies the deployment before promotion, rechecks live main,
   promotes, and compares every public file's bytes at the live alias. Its private release
   receipt includes the main SHA, deployment identity, source coverage date and hashes.
7. Run `python3 scripts/weekly_run.py complete --token <token> --receipt <release-receipt.json>`.
   It independently rechecks live main and served bytes, matches the reviewed candidate,
   and only then advances the successful-publication watermark and releases ownership.
   A queued next interval remains due; never compress several missing weeks into a falsely
   completed interval. On any failure, retain the candidate and exact failure receipt and
   report the blocked stage. Before a completion intent exists, record/fail the attempt
   with its token if explicit abandonment is needed.
   If `completion.json` exists, retry `complete` with the same token and receipt instead of
   failing or abandoning it. The persisted intent recovers interruptions before/after the
   watermark write; recovery revalidates the exact receipt and never skips an interval.
   An advanced watermark alone is insufficient. If main or the receipt has changed,
   preserve the pending intent and obtain explicit reconciliation; do not fail/restart it.

## Handoff and notification

Record research routes, source coverage, unresolved questions, reviewer decisions, topic
proposals, preserved-history checks, publication SHA and deployment receipt. Local runtime
receipts remain under `.architecture/` and must not enter the public source export.
Versioned research changes and specialist handoffs belong in the reviewed commit. Do not
upload to Drive, republish an external artifact, or send messages elsewhere unless the
owner has explicitly authorized that destination/action in the active scope.

Stay quiet while the state is current or unchanged and non-actionable. Notify the owner
only about meaningful findings requiring review, a verified publication, a failure, or a
required action. A success notice must state the actual week covered and verified main SHA.
A failed run must state its retained candidate/receipt path and next needed action. Never
report a release, a source check, a schedule cutover, or a backup without fresh evidence.
