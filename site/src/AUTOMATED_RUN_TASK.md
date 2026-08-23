# THE ARCHITECTURE — Sunday automated run (task text v7)

Paste this as the body of the weekly scheduled task. It runs every Sunday (week ending Sunday)
and ends with the updated report **live on Vercel and verified**, or with an honest "not live"
notification and the deploy package attached to the run. No preview step: the weekly update
goes straight to production. It never ends with a silent partial result.

Fixed facts for this task:

- Live site: `https://the-architecture-neurals.vercel.app` (old address `the-architecture-liard`
  redirects here)
- Vercel project `the-architecture`, team `zincdigitalofmiamis-projects`, no Git repository
- Drive folder "THE ARCHITECTURE": `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`
- Governing spec: `AGENT_INSTRUCTIONS.md` (pulled with the working copy each run; it governs
  wherever this text and the spec differ)
- SEC User-Agent for every EDGAR request: `TheArchitectureResearch [FILL IN: your email]`
  (SEC rejects requests without a name-plus-contact User-Agent)
- Deploy credential: a Vercel token stored as the Drive file named `VERCEL_TOKEN` inside the
  THE ARCHITECTURE folder (one line, the token only). Read it with the Drive connector at
  deploy time, export it to the shell, and never write it into any file, artifact, log or
  notification. If the scheduler offers a secrets/environment feature, prefer that and skip
  the Drive file.

---

## 0. Dates

`RUN_DATE` = today. `BRIEF_DATE` = the Sunday that ends this week (today, if today is Sunday),
formatted `YYYY-MM-DD`. `PREV_DATE` = `current_through` from the pulled manifest (step 1). The
window is `PREV_DATE` exclusive to `BRIEF_DATE` inclusive. If `PREV_DATE` equals `BRIEF_DATE`,
this week has already run — stop and say so.

## 1. Pull the working copy (newest deployment, promoted or not)

1. Read the `VERCEL_TOKEN` Drive file now (connector `download_file_content`; base64-decode;
   strip whitespace); export it to the shell for the rest of the run. `npm i -g vercel`.
2. Bootstrap the pull script from the live site, then let it do the rest:
   `curl -sf https://the-architecture-neurals.vercel.app/src/pull_src.sh -o pull_src.sh && bash pull_src.sh work`
   The script finds the project's newest READY deployment (preview or production) with
   `vercel ls`, fetches `/src/MANIFEST.json` and every listed file from it with `vercel curl`
   (which bypasses deployment protection), verifies every SHA-256, and writes the working copy
   to `work/` (`work/src/…`, plus the spec, this text and the scripts at `work/`). If the
   token is unavailable it falls back to the live alias. It prints which deployment it used.
3. `PREV_DATE` = `current_through` in `work/MANIFEST.json`. If the live alias's
   `/src/MANIFEST.json` carries an older date than `PREV_DATE`, an unpromoted manual preview
   exists: build on it (the script already did) and say so in the notification.
4. If the pull fails (no manifest anywhere — the v3.2 package was never deployed — or a hash
   mismatch that survives one retry), do not improvise a working copy from memory or from
   older project files: notify what failed and stop.

Read `work/AGENT_INSTRUCTIONS.md` in full before touching anything. Its §6 evidence rules and
§7 permanent corrections are not optional.

## 2. Evidence sweep — primary records only, for the window

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
pip install markdown --break-system-packages
cd work && python3 src/build_site3.py && ./check.sh
```

`check.sh` must exit 0. If it fails, fix the cause in `work/src/` and rebuild; never patch
`work/site/` by hand. Record `sha256sum work/site/index.html`.

## 5. Deploy to production and verify

1. From `work/`: `VERCEL_TOKEN=<token> ./deploy.sh --no-build --prod`. This links `site/` to
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
   `THE_ARCHITECTURE_deploy_BRIEF_DATE.zip`, present it as this run's output file, and mark
   the run **NOT LIVE** with the exact error. The manual path is then: unzip,
   `./deploy.sh --no-build --prod` (it prompts for the Vercel login once if no token is set).

## 6. Archive to Drive (folder `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`)

Use `create_file` with `parentId` set to the folder (never `copy_file`). Text only — the
connector is not a transport for large or binary files:

- the brief as a Google Doc: `THE ARCHITECTURE — Brief BRIEF_DATE` (content type `text/html`,
  converted);
- a short run log `RUN_LOG BRIEF_DATE` (plain text, conversion disabled): source deployment
  used, deployment URL, live status, index.html SHA-256, brief count, corrections and context
  lines added, clocks as of, and the exact error if anything failed.

The newest READY deployment's `/src/` is the working copy of record; the deploy zip is only
produced and attached when the site could not be verified live.

## 7. Republish the in-app artifact and notify

Republish `work/site/index.html` as the report artifact so the in-app copy matches the live
site. Then notify with:

1. the lede, verbatim from the brief;
2. one line: `LIVE — verified BRIEF_DATE at https://the-architecture-neurals.vercel.app/` or
   `NOT LIVE — <error>; deploy zip attached`;
3. what changed: corrections and context lines added (IDs), threads retired/added, map edges changed or "none",
   clocks as of;
4. next checks (the rail's nearest dates).

Hard rules for the whole run: never report a launch that was not verified live; never reword
or drop a corrections entry; never reset a clock; never let a single-outlet item in as a
finding; never edit generated files by hand; never paste the SEC User-Agent contact or the
Vercel token into the published site, a log, or a notification.
