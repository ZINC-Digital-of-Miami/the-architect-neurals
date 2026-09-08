# Preserved edition and publication proof

`baseline.json` was frozen from commit
`6521a38f30be473e77aded87e318e24a6f7b6568`, then verified against the original Git objects
before any protected source change. It records the master, source index and three prior
briefs by SHA-256 and byte length; the 17 original correction blocks as exact HTML; and
all 31 original map nodes and 62 original map edges with their grades and labels.

The Git commit is the recoverable original content. This manifest is an integrity inventory,
not a replacement for the original files or an independent off-machine backup. Do not
re-freeze or update it to authorize a rewrite. A new edition requires explicit owner review
and preservation of the preceding edition. The `freeze` command refuses an existing file.

Run `python3 scripts/preservation.py check` to compare the current source. Every build gate
also checks it. Existing prose and archived briefs are byte-protected. A dated correction
context may be appended as a new sibling `.correction` block after existing entries; adding
text inside an existing entry, changing its HTML, deleting it or reordering it fails. New
map records may be added, but original node fields and complete edge tuples cannot change
or disappear. Later relationship evidence belongs in the versioned research registry.

Each weekly candidate additionally freezes **its own base main**, including all then-current
briefs, corrections and map records, under private `.architecture/base-preservation.json`.
The original research registry is copied to `.architecture/base-registry.json` so the
registry validator can reject historical deletions or unsupported transitions. This guards
future archives as well as the initial three briefs.

Private `.architecture/` run state stays outside Git and public exports. `publication.json`
is the last successfully verified coverage watermark; `active.json` is the exclusive
writer's token and candidate reference; `runs/<Sunday>/<token>/run.json` retains each attempt;
`releases/` records exact-main deployment and public-file verification outcomes. A dispatch
or failed attempt never advances `publication.json`. Lock ownership is not automatically
stolen after a timeout: inspect and resume the same run. Only before completion intent is
persisted may it be explicitly failed with its token and a measured reason. Interrupted
candidates remain available.

Completion is a recoverable transaction: `completion.json` is flushed before the publication
watermark changes and binds the token, exact receipt digest, staged artifact and before/after
coverage. If interrupted after that point, rerun `complete` with the same token and receipt.
It freshly verifies main and live bytes again before finishing missing receipt/lock writes.
Pending completion cannot be abandoned with `fail`; its failure records are retained under
`completion-errors/`. Bootstrap
rejects coverage after the latest due Sunday, including a future Sunday date.
An advanced watermark alone is insufficient proof. If current main or the exact receipt
has changed during recovery, retain the intent for explicit reconciliation; never abandon
it with `fail` or silently restart the interval.

`deploy.sh` refuses dirty/uncommitted files and any HEAD that differs from live GitHub main.
It uploads the committed `site/` directory from an isolated Git archive, writes `release.json`
there to identify the already-existing main SHA, verifies the unpromoted deployment, rechecks
main, promotes, and verifies every publicly served file with TLS verification enabled.
Vercel's configuration file is not treated as a public route. No arbitrary preview URL can
be promoted by this wrapper. The publication receipt remains private.

Before release, the artifact gate runs both current builders against a temporary copy of the
source and compares every generated path and byte, including HTML, JavaScript, CSS, JSON and
map SVG. Missing and unexpected outputs fail, as does an ungenerated `vercel.json` that could
change routing. Only `.vercel/` CLI metadata and an exact `.gitignore` containing `.vercel`
are exempt; arbitrary ignore rules are rejected. The worktree is never rebuilt by this check.

At cutover, bootstrap once from the new verified production receipt:

```sh
python3 scripts/weekly_run.py bootstrap --receipt .architecture/releases/RECEIPT.json
```

This performs fresh main and live-file checks. It must not be initialized from the old
Claude dispatch metadata. Confirm the owner-authorized Claude task is disabled and the Codex
replacement exists separately; this file or a local test is not evidence of scheduler cutover.

The guard suite uses temporary fixtures and failure injection:

```sh
python3 scripts/test_guards.py
```

It exercises destructive source edits, missing/reworded corrections, edge/grade changes,
permitted append-only records, protection of a newly archived brief, Chicago/DST boundaries,
late dispatch, ordered catch-up, writer ownership, failed acquisition, retained retries,
stale or preview receipts, and live-byte mismatch. It does not deploy or alter schedules.
