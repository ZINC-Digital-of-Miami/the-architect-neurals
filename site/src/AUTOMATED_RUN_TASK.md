# THE ARCHITECTURE — Sunday automated run (task text v8 — local Claude Code Desktop)

This is the body of the weekly scheduled task, registered as a **local** Claude Code Desktop
task on Kirk's Mac (task id `architecture-sunday-run`, Sundays 07:00 local; runs on next app
launch if the Mac was asleep). It runs every Sunday (week ending Sunday) and ends with the
updated report **live on Vercel and verified**, or with an honest "not live" notification and
the deploy package left in the project folder. No preview step: the weekly update goes straight
to production. It never ends with a silent partial result.

**v8 changes from v7 (local execution):** no `VERCEL_TOKEN` — the Vercel CLI on this Mac is
already logged in (`vercel whoami` → `zincdigitalofmiami`); the working copy is pulled from the
live site exactly as before and, on success, synced back into the project folder and **pushed to
GitHub** (`ZINC-Digital-of-Miami/the-architect-neurals`, branch `main`) as the off-machine
backup; the run log is committed with it. Everything else is v7 verbatim.

Fixed facts for this task:

- Live site: `https://the-architecture-neurals.vercel.app` (old address `the-architecture-liard`
  redirects here)
- Vercel project `the-architecture`, team `zincdigitalofmiamis-projects`, no Git repository
- Drive folder "THE ARCHITECTURE": `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`
- Governing spec: `AGENT_INSTRUCTIONS.md` (pulled with the working copy each run; it governs
  wherever this text and the spec differ)
- SEC User-Agent for every EDGAR request: `TheArchitectureResearch [FILL IN: your email]`
  (SEC rejects requests without a name-plus-contact User-Agent)
- Deploy credential: **none needed.** This Mac's Vercel CLI session is persisted. First command
  of every run: `vercel whoami` must print `zincdigitalofmiami`; if it does not, stop and notify
  "NOT LIVE — Vercel CLI not logged in" (Kirk runs `vercel login` once). Never write any token
  into a file, artifact, log, notification, or commit.
- Project folder (git, remote `origin` = GitHub): `/Users/zincdigital/Documents/the architect neural`
- Prerequisites on this Mac (verified 2026-08-22): Node 22, `vercel` 53.x, Python 3.12 with
  `markdown`, `/sbin/sha256sum`, `gh` logged in as zincdigitalofmiami.

---

## 0. Dates

`RUN_DATE` = today. `BRIEF_DATE` = the Sunday that ends this week (today, if today is Sunday),
formatted `YYYY-MM-DD`. `PREV_DATE` = `current_through` from the pulled manifest (step 1). The
window is `PREV_DATE` exclusive to `BRIEF_DATE` inclusive. If `PREV_DATE` equals `BRIEF_DATE`,
this week has already run — stop and say so.

## 1. Pull the working copy (newest deployment, promoted or not)

1. `cd "/Users/zincdigital/Documents/the architect neural" && vercel whoami` (must be
   `zincdigitalofmiami`) and `git status --porcelain` (must be empty — if not, stop and notify:
   uncommitted local edits would be overwritten by the sync in step 6).
2. Move any stale `work/` aside first — a draft left by an interrupted run must never be built:
   `[ -d work ] && mv work "work.prev-$(date +%Y%m%d-%H%M%S)"` — then pull the working copy
   from the live site with the script in the repo: `bash pull_src.sh work` (`work/` and
   `work.prev-*` are git-ignored; delete `work.prev-*` after a successful run).
   The script finds the project's newest READY deployment (preview or production) with
   `vercel ls`, fetches `/src/MANIFEST.json` and every listed file from it with `vercel curl`
   verifies every SHA-256, and writes the working copy to `work/` (`work/src/…`, plus the spec,
   this text and the scripts at `work/`). Without a token it uses the live alias, which is the
   production deployment — the correct source for a straight-to-production run. It prints which
   deployment it used.
3. `PREV_DATE` = `current_through` in `work/MANIFEST.json`. If the live alias's
   `/src/MANIFEST.json` carries an older date than `PREV_DATE`, an unpromoted manual preview
   exists: build on it (the script already did) and say so in the notification.
4. If the pull fails (no manifest anywhere — the v3.2 package was never deployed — or a hash
   mismatch that survives one retry), do not improvise a working copy from memory or from
   older project files: notify what failed and stop.

Read `work/AGENT_INSTRUCTIONS.md` and `work/src/WEEKLY_RUN.md` in full before touching anything.
The spec's §6 evidence rules and §7 permanent corrections are not optional. If a
`_backups/TURNOVER_<date>.md` exists in the project folder from last week, read it next — and apply
its Part-A drift list to `work/src/WEEKLY_RUN.md` as the first edit of the run.

## 2. Evidence sweep — primary records only, for the window

**The sweep is the eight research agents of `WEEKLY_RUN.md` §A, spawned in ONE message
(§A.0–A.2), each a LEAF — no nested spawns, no delegation — verified in the main thread against
primary records (§C.3). The gates and stop conditions are `WEEKLY_RUN.md` §0; the writing
standard is §B and is enforced by `src/brief_lint.py` through `check.sh`.** The endpoints below
are the ones the agents and the verification use.

Work from the open threads (`#u-threads`), the silence ledger (`#u-silence`), the nearest-dates
rail, and the standing watch-list. Primary sources first; a secondary source never carries a
finding. If a primary endpoint blocks, wait 8–10 seconds and retry politely with a realistic
User-Agent; do not substitute a news article for the record.

- **Federal Register API** — presidential documents and significant rules in the window.
  Bracket parameters must be URL-encoded:
  `https://www.federalregister.gov/api/v1/documents.json?conditions%5Btype%5D%5B%5D=PRESDOCU&conditions%5Bpublication_date%5D%5Bgte%5D=PREV_DATE&per_page=100`
- **Senate roll calls** — `https://www.senate.gov/legislative/LIS/roll_call_votes/vote_119_2/vote_119_2_000NN.xml`
  for every vote number since the last one recorded; this endpoint is intermittently WAF-blocked
  and needs the polite-retry pattern.
- **EDGAR full-text search** — `https://efts.sec.gov/LATEST/search-index?q=TERM&dateRange=custom&startdt=PREV_DATE&enddt=BRIEF_DATE`
  for each watch-list term: `"ALT5 Sigma"`, `"AI Financial"`, CIK `862861`, `"World Liberty"`,
  `"DT Marks"`, `"Witkoff"`, `"USD1"`, `"EMAT"`, `"REEMF"`, `"Point72"`, `"ExodusPoint"`, plus any
  registrant named in the open threads. For filings that matter, open the filing index under
  `https://www.sec.gov/Archives/edgar/data/<CIK>/<accession-no-dashes>/` and read the primary
  document; cite the accession number. Forms to sweep by name: 4, 8-K, 10-Q, 13D, 13G, 13F-HR,
  S-1, S-3, 424B.
- **CourtListener / RECAP** — docket entries in the window for every case named in the open
  threads (Phang v. Blanche, the Comey and James matters, US v. Harvard, the ballroom case, and
  any others carried forward).
- **Agency decision documents** — OCC, Treasury, DOJ and ICE documents named in the threads;
  the OCC conditional-approval record for World Liberty Trust Company is the model of what
  counts.
- **Verified absences** — for every thread where nothing was found, record what was searched
  and where. An absence is a result and goes in the brief.

Grade every item [A] / [B] / [C] / ABSENT per spec §6. [C] items are published as rejections
with the reason, never as findings. Dotted edges stay dotted until a document closes them.

## 3. Write the week

1. **Brief.** Copy `work/src/briefs/_TEMPLATE.html` to `work/src/briefs/BRIEF_DATE.html`, keep
   the `<body>` wrapper, and write: lede; Power / Money / Ideology; rejected this week; checked
   for and not found; sourcing notes. Declarative, dated, sourced; no motive speculation; no
   adjectives doing an evidence tier's work.
   **Context, not claims (spec §6):** every rejected item and every verified absence is
   followed by sourced context — what the primary record does show [A], then what two or
   more independent named outlets report about the circumstances the claim was pointing at
   [B], each outlet named with its date. Never restate the rejected claim as fact, never
   supply a motive. If no sourced context exists, the entry says so. The template carries
   the shape. Corrections get context the same way: a new dated line appended under the
   entry, never a rewording of it.
2. **`work/src/update_part2.html`**, exactly as spec §5 step 3:
   `#u-week` replaced; `#u-node` only if the map changed; `#u-corrections` **append only**,
   next sequential `C-00N`, was/now, date, tier; `#u-silence` every clock advanced by the days
   elapsed and `clocks-asof` set to `BRIEF_DATE`; `#u-threads` resolved threads retired with
   how, new checks added.
3. **Neural map.** If any node or edge changed: edit `work/src/map_source.json`, run
   `node work/src/build_neural_map.js` to regenerate `neural_svg.frag` and `neural_data.json`
   (it prints the node/edge counts to copy across; `build_neural_map.py` is legacy — running
   it regenerates nothing and leaves the map silently stale),
   and update the data-state date, counts, "This window" chips and the week ledger in
   `work/src/neural_map.html`. If nothing changed, still set the data-state date to
   `BRIEF_DATE` and add a ledger line "no edge changes this window".
4. **Rail.** In `work/src/build_site3.py`, `rail_stops`: drop dates that have passed, add newly
   docketed ones, keep `NOV 3` flagged `big` until it passes.
5. **Never** edit `work/src/master_report.md`, `work/site/index.html`, or the look (`final.css`).

## 4. Rebuild and guard

```
cd work && python3 src/build_site3.py && ./check.sh
```
(`markdown` is already installed here; `deploy.sh` installs it only if missing.)

`check.sh` must exit 0. If it fails, fix the cause in `work/src/` and rebuild; never patch
`work/site/` by hand. Record `sha256sum work/site/index.html`.

## 5. Deploy to production and verify

1. From `work/`: `./deploy.sh --no-build --prod` (no token — persisted CLI login). This links `site/` to
   project `the-architecture` in team `zincdigitalofmiamis-projects` (explicitly — the folder
   name differs from the project name) and uploads it as a production deployment. The payload
   never passes through the model; the Vercel connector is not used for the upload because
   its file-tree call cannot carry ~1.7 MB of site.
2. Wait 30 seconds, then verify from the live address, retrying up to 5 times at 20-second
   intervals:
   - `GET /` is 200 and contains `BRIEF_DATE` in the masthead;
   - `GET /briefs/BRIEF_DATE.html` is 200;
   - `GET /src/MANIFEST.json` is 200 and its `current_through` equals `BRIEF_DATE`.
   **Only if all three pass** is the site live. Say "live and verified" only then.
3. If the token is missing or rejected, the CLI errors, or verification never passes: zip
   `work/` (with `site/`, `src/`, the scripts, the spec, this text) as
   `THE_ARCHITECTURE_deploy_BRIEF_DATE.zip` in the project folder, name its path in the
   notification, and mark the run **NOT LIVE** with the exact error. The manual path is then:
   `cd work && ./deploy.sh --no-build --prod`.

## 6. Sync back, commit, push (the backup of record), then archive to Drive

**Only after step 5 verified live.** From the project folder:
`rsync -a --delete work/src/ src/ && rsync -a --delete --exclude .vercel work/site/ site/ && cp work/AGENT_INSTRUCTIONS.md work/AUTOMATED_RUN_TASK.md work/check.sh work/deploy.sh work/pull_src.sh .`
then `./check.sh` again on the synced tree (must exit 0), then
`git add -A && git commit -m "Weekly Brief NNN — week ending BRIEF_DATE" && git push origin main`,
and verify `git ls-remote origin main` equals `git rev-parse HEAD`. Record both SHAs in the run
log. If the push fails, the site is still live — say so, and mark the notification
"LIVE — NOT PUSHED: <error>" so Kirk pushes by hand.

Then archive to Drive (folder `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`, connector account
kirk@zincdigital.co). Use `create_file` with `parentId` set to the folder (never `copy_file`).
Text only — the connector is not a transport for large or binary files:

- the brief as a Google Doc: `THE ARCHITECTURE — Brief BRIEF_DATE` (content type `text/html`,
  converted);
- a short run log `RUN_LOG BRIEF_DATE` (plain text, conversion disabled): source deployment
  used, deployment URL, live status, index.html SHA-256, git commit SHA and push result, brief
  count, corrections and context lines added, clocks as of, and the exact error if anything
  failed. Also write the same log to `_backups/RUN_LOG_BRIEF_DATE.txt` in the project folder
  before the commit in this step so it ships with the push.

The newest READY deployment's `/src/` is the working copy of record; the deploy zip is only
produced and attached when the site could not be verified live.

## 7. Turnover, artifact, notify

Before the commit in §6, write `_backups/TURNOVER_BRIEF_DATE.md` per `WEEKLY_RUN.md` §D —
what moved, what did not resolve, standing anchors, spawn-prompt drift to fix next week, environment
facts. It ships with the push.

Republish `work/site/index.html` as the report artifact so the in-app copy matches the live
site. Then notify with:

1. the lede, verbatim from the brief;
2. one line: `LIVE — verified BRIEF_DATE at https://the-architecture-neurals.vercel.app/ — pushed <sha>`,
   `LIVE — NOT PUSHED: <error>`, or `NOT LIVE — <error>; deploy zip at <path>`;
3. what changed: corrections and context lines added (IDs), threads retired/added, map edges changed or "none",
   clocks as of;
4. next checks (the rail's nearest dates).

Hard rules for the whole run: never report a launch that was not verified live; never reword
or drop a corrections entry; never reset a clock; never let a single-outlet item in as a
finding; never edit generated files by hand; never paste the SEC User-Agent contact or the
Vercel token into the published site, a log, a notification, or a commit; never `git push --force`;
never commit `work/`.
