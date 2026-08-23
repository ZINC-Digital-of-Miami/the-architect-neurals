# THE ARCHITECTURE — WEEKLY RUN BOOK (v2, 2026-08-22)

## Exact spawn prompts + exact actions. Companion to AGENT_INSTRUCTIONS.md and AUTOMATED_RUN_TASK.md.

AGENT_INSTRUCTIONS.md is the **policy** (what the site is, the design tokens, the evidence rules, the permanent corrections). AUTOMATED_RUN_TASK.md is the **run** (dates, pull, deploy, verify, push, archive, notify — v8, local Claude Code Desktop). This file is the **procedure inside the run**: the literal text to send to the eight research agents, and the literal commands, in order. Where they disagree: AGENT_INSTRUCTIONS.md wins on policy; AUTOMATED_RUN_TASK.md wins on the pull/deploy/push mechanics; this file wins on the spawns and the editing sequence.

**Provenance.** Part A below is carried **verbatim** from the original WEEKLY_RUN.md (Google Doc 15bguyjbq2gxwwowpBglyOhLnzIDtBCzUdt2VHOXe7Iw, retrieved 2026-08-22). Nothing in Part A was rewritten. Part B was revised on 2026-08-22 to match the v3.2 package: hash-verified pull (`pull_src.sh`), `node src/build_neural_map.js` as the map step, `check.sh` as the guard, `deploy.sh --no-build --prod`, git push as the backup of record, and the zip produced only when the site could not be verified live. Each revision is marked **[v2]** with the reason.

**Substitutions used throughout.** Resolve these once at the top of the run, then use them literally everywhere below:

| Token | Meaning | Example (run of 2026-08-23) |
|---|---|---|
| {{SUNDAY}} | week-ending Sunday, ISO | 2026-08-23 |
| {{WINDOW}} | the seven-day window | August 17–23, 2026 |
| {{TODAY}} | run date, long form | August 23, 2026 |
| {{SITE}} | live site root | https://the-architecture-neurals.vercel.app |

---

# PART A — THE SPAWNS

## A.0 How to spawn

- Tool: **Agent**. subagent_type: "general-purpose" for all eight (they need WebSearch + WebFetch + Bash; Explore is read-only over local files and will not work).
- **All eight Agent calls go in ONE assistant message** so they run concurrently. Sending them one at a time serializes the run and wastes the window.
- Do not spawn a ninth agent to "check" the others. Verification is B.3, done in the main thread against primary records.
- Expect ~10–20 min wall clock and ~60–140k tokens per agent. If one returns null (killed or API-dead), re-spawn that one agent alone with the identical prompt.

## A.1 The preamble — paste VERBATIM at the top of all eight prompts

You are a research agent for a tiered-evidence investigative brief on US politics. Today is {{TODAY}}. Your knowledge cutoff predates these events — you MUST use WebSearch/WebFetch for everything; do not rely on training priors. Window of interest: developments {{WINDOW}}. For standing items, also report current status even if the last development is older, with its date.

EVIDENCE STANDARD (hard gate). Tier every finding: **[A]** primary record cited directly — court docket entry, SCOTUS order, Federal Register document, official agency release or decision document, roll-call vote, SEC filing with accession number, contract record — or an on-the-record admission by the principal. **[B]** two or more GENUINELY INDEPENDENT named outlets AND the primary record identified, even if you could not fetch it. **[C]** single outlet, anonymous-sourced only, or aggregator — mark REJECTED WITH REASON, and still report it so the rejection is visible. Escalate every secondary report to its primary record: a vote → the roll call; a filing → the docket entry; a disclosure → the filing itself. Use supremecourt.gov, courtlistener.com, congress.gov, senate.gov, federalregister.gov, efts.sec.gov (EDGAR full-text), sam.gov, usaspending.gov, justice.gov, occ.gov, ice.gov, centcom.mil.

FALSE-CORROBORATION TRAP: syndications and aggregator repostings of ONE wire story are ONE source, not many. Count origins, not headlines. Watch for number drift across hops ($500M → "half a billion" → $550M; ">90%" → "93%") and always anchor to the origin document. Note explicitly when a major outlet's own domain is fetch-restricted and you are reading it via syndication.

Report the private position and the government action as SEPARATE dated facts with separate records. NEVER assert the causal link yourself — keep dotted edges dotted. Attach every denial to its allegation and record the denial's EXACT SCOPE: a knowledge-qualified denial, a motive-only denial, and a narrow personal denial standing beside a broad spokesperson denial are each findings in themselves. Where evidence for an expected edge does not exist, report it ABSENT and say what you searched — a verified absence is a result, not a gap.

RETURN FORMAT: raw structured data, not prose for a reader. One row per finding: DATE | FACT (one declarative sentence) | TIER | PRIMARY RECORD (name + URL/accession) | ORIGIN SOURCES (count origins) | DENIALS & exact scope | NOTES (drift, syndication, absence). End with two lists: (1) items you checked that produced NO qualifying evidence — the absences; (2) sub-[B] items rejected, each with its reason. Be exhaustive within your areas; run many searches. Do not summarize away specifics: exact dates, exact numbers, exact quotes.

## A.2 The eight sweep blocks — append ONE to the preamble per agent

### SPAWN 1 — Elections & election machinery

description: "Elections and machinery sweep"

YOUR SWEEP AREAS:

1. November 3, 2026 midterms & election administration: DOJ or DHS involvement, federal monitors and where deployed, certification disputes, candidate-filing disputes, litigation over election procedures. DOJ's own releases are primary — its standing position is that monitoring "continues through the general election on November 3, 2026."
2. Election machinery: post-*Louisiana v. Callais* redistricting (new maps, mid-decade redistricting, state supreme court action), SAVE Act status in Congress (last action: cloture on the HAVA photo-ID variant failed 52–46, 4:36 a.m. Aug 8, 2026, Senate roll call #231; Congress returned Sept 14), DHS/FEMA notices and grant conditions to states and the 26-state suit in D.R.I., suspended/moved/postponed primaries, the Missouri redistricting referendum fight in Cole County (ballot-print deadline was Sept 8).
3. SCOTUS emergency applications **26A124** and **26A139** (mail-ballot executive order, 23 states + DC): any order, briefing, or disposition. Pending without order since July 27, 2026 as of the last brief — an order EITHER WAY is a lead, and continued silence is itself reportable with the day count. Also any OTHER direct SCOTUS order to the president and documented compliance or defiance.

### SPAWN 2 — Insurrection Act & executive power

description: "Insurrection Act / executive power sweep"

YOUR SWEEP AREAS:

1. Insurrection Act: any invocation, proclamation, or new explicit threat to deploy troops against a US city; National Guard federalization or military deployment in US cities; related litigation and compliance. **Verify absence against the primary record**: query the Federal Register presidential-documents API for the window and report what it returned.
2. Direct court orders to the president or executive branch and compliance/defiance — especially any SCOTUS order and the administration's response. Contempt ledger: the DHS civil contempt in C.D. Cal. (Vasquez Perdomo, $500/day since Aug 4, 2026) and the Boasberg contempt inquiry (en banc pending since June 22, 2026).
3. Executive orders signed this window with structural significance (elections, law enforcement, emergency powers, civil service, citizenship). Cite the Federal Register document number, not the press coverage.
4. Trial balloons on executive power: third-term/2028 statements, election-emergency statements, habeas suspension. Get the exact quote, date, venue, and primary source (official transcript, video, Truth Social post). The two standing poles: "Let me just say stranger things have happened" (Aug 11, 2026, on an election national-security emergency) and "I'd love to run, but the law is very strong" (Aug 11, 2026, on 2028).

### SPAWN 3 — The wars, the count

description: "Wars and Iran/Hormuz sweep"

YOUR SWEEP AREAS:

1. Iran / Strait of Hormuz: US or Iranian military action, strikes, naval blockade enforcement (vessels redirected/disabled/boarded — anchor the running tally to CENTCOM's own releases and flag drift), ceasefire status, escalation or de-escalation. The tempo of presidential statements: collect EACH with exact date, venue, and verbatim quote; note market-relevant statements and the market move as SEPARATE dated facts, asserting no causation.
2. Congressional war powers: authorization votes, war-powers resolutions, discharge motions — escalate to the actual roll call at senate.gov/congress.gov. Standing: H.Con.Res. 89 passed the House 214–208 (July 23); S.J.Res. 181 discharge failed 49–50 (July 30).
3. Casualty figures and any RECATEGORIZATION of them. Standing finding: in July 2026 the Pentagon moved Iran-war casualties from "Operation Epic Fury" to a new "Overseas Operations" category, restarting the count (displayed KIA 18→14; 600+ wounded became "207 since July 7"). Track: DoD/DCAS changes, Sen. Rosen's Aug 14 bill barring "manipulating casualty records" (GET THE BILL NUMBER — it was not yet posted), and the USS Lincoln conditions with each denial's exact scope (CENTCOM denies deaths aboard; the Navy denies an *increase in reported* suicidal ideation; Hegseth's is broad and evidence-free).
4. Other active US hostilities (Yemen, Venezuela/Caribbean, elsewhere): strikes, claimed legal authorities, congressional notifications, civilian-casualty reviews, casualty counts.

### SPAWN 4 — Epstein files & DOJ

description: "Epstein/DOJ compliance sweep"

YOUR SWEEP AREAS:

1. **Phang v. Blanche, D.D.C. No. 1:26-cv-01417 (Sullivan)** — the compliance case. At the Aug 13, 2026 hearing Sullivan warned of contempt: "I don't want to do it, but I will do it… That isn't a threat. That's a promise." Plaintiff's proposed compliance orders were due ~Aug 23. PULL THE DOCKET: any contempt order, compliance filing, redaction log, or new deadline. **Any contempt order is the lead finding of the week.** CourtListener has been blocking fetches — try storage.courtlistener.com PDFs, the court's own site, and PACER-derived reporting, and say which route worked.
2. Epstein Files Transparency Act compliance: DOJ's disclosure page (justice.gov/epstein) — any release after the standing last-activity date of April 3, 2026. The DOJ OIG audit of EFTA compliance. Withholding grounds asserted, and whether the withheld handwritten FBI interview notes (the 2019 trafficking allegation) are addressed by any DOJ statement.
3. **Preska unsealing, S.D.N.Y. (Giuffre v. Maxwell, 15-cv-07433 / US v. Maxwell)** — she rejected all of Maxwell's objections Aug 11–12, 2026 and ordered materials unsealed. Has the release actually EXECUTED? Any newly named individuals qualify only at [A]/[B].
4. Survivor litigation (including the Jane Does suit against DOJ and Google), and any DOJ leadership changes, resignations-in-protest, or whistleblower letters this window.
5. Attorney General Blanche's department: new OLC opinions, policy memos, personnel actions. Standing: the ~Aug 10–11 OLC opinion extending executive privilege to presidential communications with "private advisers" outside government.

DENIAL-SCOPE DISCIPLINE IS THE POINT HERE: DOJ's institutional line is that it has "not KNOWINGLY violated, nor has it ever ACKNOWLEDGED violating" the Act — a knowledge-qualified denial that concedes nothing about the withholding. Blanche's December 2025 line — "There's no effort to hold anything back because there's the name Donald J. Trump" — is a MOTIVE denial, not a withholding denial. Record whether any new statement finally covers the allegation.

### SPAWN 5 — Immigration detention & enforcement

description: "Immigration detention sweep"

YOUR SWEEP AREAS:

1. Detention population: the most recent official ICE detention statistics release — anchor to the dataset and its as-of date; do NOT merge point-in-time figures with average-daily-population figures. Standing anchors: ~68,000 in early Aug 2026; record 70,766 on Jan 24, 2026; TRAC's 65,765 is a July 11 point-in-time.
2. Contracts, especially no-bid/sole-source: the up-to-$10B "Mega Hub" IDC solicitation (seven concurrent sites incl. Guantánamo; bids closed Aug 31, 2026 — **find the award**), the ~$1.5B CoreCivic facility PURCHASES (California City, Otay Mesa), GEO awards, the Camp East Montana no-bid extension. Escalate to SAM.gov notice IDs and USAspending award IDs.
3. Deaths in custody: new ICE death notifications (ICE must publish them), plus deaths ICE declines to count. Standing finding: Jose Chajon-Raxon, third Delaney Hall-linked death, where ICE stated "when an individual is no longer in ICE custody, then ICE will no longer be responsible for monitoring or reviewing deaths that may occur" — a denial whose scope is the accounting category, not the death. Keep the competing YTD tallies (AILA, NIPNLG, Kocher) separate and labeled; do not merge them.
4. Court blocks: injunctions/TROs on detention and removal practice, appellate developments, third-country removal agreements and flights, Guard/military use in immigration enforcement.
5. Abrego Garcia: CA4 No. 26-6466 (briefing was due Sept 21 / Oct 21), D. Md. habeas 8:25-cv-02780, M.D. Tenn. 3:25-cr-00115 dismissal appeal.

### SPAWN 6 — Succession, health, 2028

description: "Succession and health sweep"

YOUR SWEEP AREAS — **sourced facts only; offer NO diagnosis and no clinical inference in your own voice. Report what named people and official documents say, and nothing beyond it.**

1. Presidential fitness: statements by the White House physician (official memos — the last was May 29–30, 2026), named-outlet visible-event reporting, schedule anomalies documented in official schedules or pool reports. Standing: Dr. Jonathan Reiner's on-record NYT op-ed of Aug 12, 2026 seeking a congressional commission (NOT the 25th Amendment), and the named White House response, which is rhetorical in scope with no clinical content.
2. 25th Amendment: any on-the-record statement by a member of Congress or an official.
3. VP positioning: Vance's schedule, delegated authorities, any "acting" role, 2028 statements.
4. 2028 trial balloons: exact quote, date, venue, primary source. Merchandise/organizational signals only if 2+ independent outlets.
5. Any succession-relevant legal or constitutional maneuver.
6. Senior personnel changes in the White House and Cabinet this window.

### SPAWN 7 — The money (EDGAR-first)

description: "Family money and crypto sweep"

**DO THE DOCUMENT PULLS FIRST — they outrank news coverage.** Use EDGAR full-text search (efts.sec.gov/LATEST/search-index?q=) and browse-edgar. Report accession numbers.

1. **AI Financial Corp / ALT5 Sigma — CIK 0000862861** (ONE registrant, renamed Apr 28, 2026; ALTS→AIFC). Pull every new filing: the Q2 10-Q that followed the Aug 12 NT 10-Q, any 8-K, going-concern language, Nasdaq deficiency status, and the marks on its WLFI tokens after the scheduled Aug 12, 2026 unlock of 3.58B tokens (was the unlock executed on-chain?). Standing at [A]: $348.3M one-quarter unrealized WLFI loss; a $15M loan FROM WLFI with 378M tokens pledged; −92.2% from the $7.50 offering.
2. **World Liberty Trust Company, N.A.** — OCC Corporate Decision #1385, Control No. 2026-Charter-344521, preliminary conditional approval Aug 14, 2026. Follow-on: comment letters, conditions satisfied or not, final approval, GENIUS Act compliance, any change to the passive indirect investors named in the decision (DT Marks SC LLC, StringZ Holding RSC (DE) LLC, AMGUS, LLC).
3. **Warren–Reed letter (Nov 17, 2025) to Bessent and Bondi** on WLFI buyers tied to sanctioned/DPRK/A7A5/Tornado Cash wallets — deadline Dec 1, 2025. Any Treasury or DOJ response. **A continued non-answer IS the finding** — establish the current day count. Same for the Dec 15, 2025 USD1/PancakeSwap follow-up (deadline Jan 12, 2026) and the July 6, 2026 Warren/Wyden/Schumer letters to ten Trump-orbit entities about the alleged May 2026 DOJ–IRS immunity settlement (deadline July 20, 2026; 0 of 10 had replied). Also: has the settlement document itself surfaced? It remains unobtained.
4. **Steve Witkoff's OGE 278e** — uncertified for roughly a year against a ~60-day norm. Check OGE and ProPublica's disclosure database for a certification date.
5. **Point72 and ExodusPoint 13F/13D/13G** for any AIFC position change (CUSIP 47089W104). Q2 2026: Point72 held NO position; ExodusPoint held 2,170,301 shares / $1,269,843.
6. This window's sweep: WLFI/USD1/$TRUMP developments and the Warren–Blumenthal SEC referral; Trump Media (DJT) filings and the Truth Social API business that sells post feeds to ~10 customers, "primarily high-frequency trading firms" per its interim CEO on the record; American Bitcoin; Kushner–Affinity; Witkoff positions; new foreign-state deals; pardons where the recipient or associates had financial ties (report the pardon and the money as SEPARATE dated facts); 1789 Capital; no-bid enforcement contracts; OGE/ethics filings.
7. **The un-drawn edge — confirm the absence:** any subpoena identifying Polymarket wallet holders, WLFI stake buyers, or an envoy's market position. This has been ABSENT every week; say what you searched and confirm it is still absent.

DO NOT merge these entities: DT Marks DEFI LLC (receives 75% of token-sale proceeds) is not DT Marks SC LLC (passive investor in the trust bank). Zach Witkoff (WLF CEO, trust-bank president, ALT5 chairman) is not Steve Witkoff (special envoy).

### SPAWN 8 — The dockets

description: "Docket sweep: prosecutions and appeals"

YOUR SWEEP AREAS — identify every case number; pull the docket entry, not the coverage:

1. **US v. Comey** — CA4 Nos. 25-4673(L)/25-4674 (argument was set for Sept 15, 2026, Richmond): argument held? opinion? And the separate E.D.N.C. No. 4:26-cr-00016-FL ("86 47" threat case): rulings on the four dismissal motions, arraignment, trial set for Oct 21, 2026.
2. **US v. Letitia James** — the consolidated CA4 appeal; any new indictment attempt.
3. **US v. Bolton** — D. Md. 8:25-cr-00314-TDC, sentencing set Oct 28, 2026. NOTE: the plea was to **Count 12 only**, per the docket minute entry — coverage claiming "all 18 counts" is wrong; the docket controls.
4. Any grand jury or probe targeting Gavin Newsom.
5. Press subpoenas: new DOJ subpoenas to journalists or outlets, and litigation over them.
6. **Harvard** — CA1 No. 25-2230 (funding appeal; government reply filed Aug 12, 2026; watch for an argument date) and D. Mass. 1:26-cv-10844-MJJ (Title VII; MTD hearing Sept 24, 2026). The Title VI suit was dismissed Aug 13, 2026 (D. Mass. 1:26-cv-11352-RGS) — any appeal?
7. **AAP v. Kennedy** — CA1 No. 26-1503; the government moved Aug 14, 2026 to expedite argument or submit on the briefs. Any ruling, argument date, or district-court movement.
8. **Abrego Garcia** — CA4 26-6466, D. Md. 8:25-cv-02780, M.D. Tenn. 3:25-cr-00115.
9. NEW indictments of political adversaries (former officials, prosecutors, judges, governors) and any grand jury refusals to indict.
10. Contempt proceedings against DOJ or administration officials.

---

# PART B — THE EXACT ACTIONS

Everything below is run in the main thread. Commands are literal. Steps that AUTOMATED_RUN_TASK.md already specifies (dates, pull, deploy, verify, push, Drive archive, notify) are referenced, not duplicated, so the two texts cannot drift.

## B.1 Fetch the working copy from the live site

**[v2 — replaced the ad-hoc curl loop: the package now self-hosts a manifest with SHA-256s and a script that verifies every file. An unverified curl loop silently accepts a 404 HTML page as a source file.]**

```
cd "/Users/zincdigital/Documents/the architect neural"
vercel whoami                 # must print zincdigitalofmiami — else stop, notify NOT LIVE
git status --porcelain        # must be empty — else stop, notify (local edits would be overwritten in B.12)
bash pull_src.sh work         # pulls /src/MANIFEST.json + every listed file, verifies every hash
```

Then read `work/AGENT_INSTRUCTIONS.md` and `work/AUTOMATED_RUN_TASK.md` in full before editing anything. `PREV_DATE` = `current_through` in `work/MANIFEST.json`; if it equals {{SUNDAY}}, the week has already run — stop and say so. If the pull fails (no manifest, or a hash mismatch that survives one retry), do not improvise a working copy: notify what failed and stop.

## B.2 Spawn — one message, eight Agent calls

Preamble (A.1) + sweep block (A.2) per agent, subagent_type: "general-purpose". Do not paraphrase the preamble; the tiering discipline is load-bearing. Resolve {{TODAY}} / {{WINDOW}} before pasting.

## B.3 Verify before writing (main thread)

For every finding you intend to publish at [A]: open the primary record yourself. For [B]: confirm the two origins are genuinely independent — check whether both trace to one wire. Demote anything that fails. Reconcile conflicting dates and numbers against the origin document and record the drift in the notes. Anything that survives only as [C] goes in the rejected list with its reason — published, not hidden.

**Context, not claims (AGENT_INSTRUCTIONS §6):** every rejected item and every verified absence is followed by sourced context — what the primary record does show [A], then what two or more independent named outlets report about the circumstances the claim was pointing at [B], each outlet named with its date. Never restate the rejected claim as fact; never supply a motive. If no sourced context exists, say so.

## B.4 Write the brief

```
cp work/src/briefs/_TEMPLATE.html work/src/briefs/{{SUNDAY}}.html
```

Keep the `<body>` wrapper (the build strips everything outside it). Structure: lede → Power / Money / Ideology → rejected-this-week → checked-for-and-not-found → sourcing notes. Narrative prose in plain declarative sentences, with the documents doing the accusing. Never a bulleted findings dump. Tier chips inline: `<span class="tier a">A</span>` (and b, c, abs). "No material change" is a legitimate brief on a quiet week.

## B.5 Edit work/src/update_part2.html — anchor by anchor

| Anchor | Exact action |
|---|---|
| `#u-week` | Replace with the new week. The outgoing week's substance already lives in its brief; keep only what still carries forward. Update the `<h4>` window label. |
| `#u-node` | Only if the week changed the node. Edit the inline SVG's box labels/tiers. Edges stay dashed (class="nf-edge") unless a document closed one — and if one closes, that is a lead. |
| `#u-corrections` | **APPEND ONLY.** Next ID in sequence (the log stands at C-008 as of 2026-08-22; next is C-009). Never delete, reword, or renumber an existing entry. Context for an existing entry is a new dated `correction` block ("C-00N · context added"), never an edit. Format: `<div class="correction"><div class="mono">DATE · C-00N</div><p><span class="was">…</span><br><span class="now">…</span> <span class="tier a">A</span></p></div>` |
| `#u-silence` | Advance EVERY clock's `.num` and the `.clocks-asof` date to {{SUNDAY}}. A week with no answer is a finding: the number goes up, the entry stays. If one is answered, replace the clock with the answer and log the date it arrived. Nine clocks as of 2026-08-22 — `check.sh` fails below nine. |
| `#u-threads` | Retire resolved threads (state how they resolved), add the new next checks, keep the table in date order. |

## B.6 Neural map — only if nodes or edges changed

**[v2 — `python3 build_neural_map.py` replaced. That file is legacy: hardcoded 21-node tables, never reads map_source.json, writes nothing the site uses. Running it leaves the map silently stale.]**

```
# edit work/src/map_source.json (nodes / edges / flags / "current"), then:
node work/src/build_neural_map.js      # regenerates neural_svg.frag + neural_data.json, prints the counts
```

Then in `work/src/neural_map.html` update: the data-state date in the kicker and stamp, the node/edge counts (they must match what the script printed — `check.sh` compares them to data.json), the "This window" chip strip, and the week ledger at the foot. Grades are [A]/[B]/[C]/[Ø]; **[Ø] adjacency stays dotted until a document closes it.** If nothing changed, still set `"current"` and the data-state date to {{SUNDAY}} and add a ledger line "no edge changes this window".

## B.7 Rotate the dates rail

In `work/src/build_site3.py`, edit `rail_stops`: drop dates that have passed, add newly docketed ones, keep NOV 3 flagged `big` until it passes.

## B.8 Build

```
cd work && python3 src/build_site3.py
```

The build derives brief numbering, the edition number, the masthead date, the archive list, per-brief pages, sitemap.xml, MANIFEST.json and site/src/ from the contents of src/. Nothing is bumped by hand. `ARCH_SITE_URL` defaults to {{SITE}}; set it only if the address moves.

## B.9 The verification gauntlet — all of it must pass

**[v2 — the inline gauntlet is now `check.sh`, a superset of it: the original guards plus C-005–C-008, the eleven consolidated-edition chapters, both appendices, the clock-count floor, and the map prose-vs-data check. The original used GNU `stat -c`, which fails on macOS.]**

```
cd work && ./check.sh          # exit 0 or do not deploy
test -s "site/briefs/{{SUNDAY}}.html"
grep -q "{{SUNDAY}}" site/index.html
```

A failure here stops the run. Do not deploy a build that fails a guard; fix the source and rebuild. Record `shasum -a 256 site/index.html`.

## B.10 Deploy and verify live

**[v2 — the Vercel connector probe and its failure signature are removed: AGENT_INSTRUCTIONS §3 rules the connector out as the transport. The CLI on this Mac is logged in; no token.]**

Exactly AUTOMATED_RUN_TASK.md §5: `cd work && ./deploy.sh --no-build --prod`, wait 30 s, then from the public address (plain `curl`, up to 5 tries at 20 s): `/` is 200 and contains {{SUNDAY}}; `/briefs/{{SUNDAY}}.html` is 200; `/src/MANIFEST.json` is 200 with `current_through` = {{SUNDAY}}. **Only if all three pass** is the site live.

## B.11 The package — only when the site could not be verified live

**[v2 — the original shipped a zip every week regardless. AGENT_INSTRUCTIONS §5 step 7 and AUTOMATED_RUN_TASK §5.3 govern: the newest READY deployment's `/src/` is the working copy of record; the zip exists only as the fallback when verification fails.]**

If B.10 did not pass: `zip -qr "THE_ARCHITECTURE_deploy_{{SUNDAY}}.zip" work/site work/src work/*.sh work/*.md` in the project folder, name its path in the notification, and mark the run **NOT LIVE** with the exact error. Do not run B.12.

## B.12 Sync back, commit, push — the backup of record

**[v2 — new. The project folder is a git repository with `origin` = github.com/ZINC-Digital-of-Miami/the-architect-neurals. Until 2026-08-22 there was no off-machine copy of the sources except the live site itself.]**

Exactly AUTOMATED_RUN_TASK.md §6: rsync `work/src/` → `src/`, `work/site/` → `site/` (excluding `.vercel`), copy the five root files, run `./check.sh` on the synced tree, write `_backups/RUN_LOG_{{SUNDAY}}.txt`, then `git add -A && git commit -m "Weekly Brief NNN — week ending {{SUNDAY}}" && git push origin main`; verify `git ls-remote origin main` equals `git rev-parse HEAD`. Never `--force`; never commit `work/`. If the push fails the site is still live — report `LIVE — NOT PUSHED: <error>`.

## B.13 Archive to Drive, republish the artifact, notify

Drive: exactly AUTOMATED_RUN_TASK.md §6 (folder `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`, `create_file` with `parentId`, text only: the brief as a Google Doc and `RUN_LOG {{SUNDAY}}`).

Artifact: **[v2]** the original republished in place at `https://claude.ai/code/artifact/43bad372-6bd6-4ce6-a2e8-c1d5a06589f4`. That artifact belongs to the account the original task ran under; from this machine, republish it in place only if `Artifact action:list` shows it as owned — otherwise skip the artifact step and say so. Never create a duplicate. If republishing: file_path `work/src/artifact.html`, favicon stable, label `edition-NNN-{{SUNDAY}}`.

Notify: exactly AUTOMATED_RUN_TASK.md §7 — the lede verbatim; one status line (`LIVE — verified {{SUNDAY}} at {{SITE}}/ — pushed <sha>` / `LIVE — NOT PUSHED: <error>` / `NOT LIVE — <error>; deploy zip at <path>`); what changed (correction IDs, context lines, threads retired/added, map edges changed or "none", clocks as of); next checks (the rail's nearest dates). Intended recipients once an email connector is wired: kirk@zincdigital.co, jaymie@zincdigital.co.

A quiet week still ships: the clocks changed, so the site changed. Say "no material change," advance the clocks, rebuild, deploy, push, notify.

---

# PART C — THE SCHEDULED-TASK PROMPT

**[v2]** The trigger is the local Claude Code Desktop task `architecture-sunday-run` (Sundays 07:00 local). Its prompt is deliberately short: it tells the run to open AUTOMATED_RUN_TASK.md, AGENT_INSTRUCTIONS.md, and this file, and to follow them — so the files, which ship with the site and are hash-verified on every pull, are the only place the procedure lives. The original Part C prompt is preserved in the Google Doc named under Provenance; its substance (spawn all eight in one message; verify [A] yourself; anchor-by-anchor edits; regenerate the map only on change; rotate the rail; rebuild; full gauntlet; deploy; notify; the non-negotiables) is carried in Parts A and B above and in AUTOMATED_RUN_TASK.md.

---

# PART D — TURNOVER (written AFTER the work, every week)

**[v2 — formalized. The owner's standing rule: the turnover for the following week is written after the work is done, not before. It is the last edit of the run and ships with the push.]**

At the end of every run, before the commit in B.12, write `_backups/TURNOVER_{{SUNDAY}}.md` — short, facts only, for the agent that runs next Sunday:

1. **What moved** — each correction/context ID added, each thread retired (how) or added, each clock answered, each map edge changed. IDs and dates, no prose.
2. **What did not resolve** — every fetch-restricted origin this week (which domains 403'd; which route worked), every docket that could not be read and why, every "find the award / find the bill number" item that is still open.
3. **Standing anchors to carry** — the exact current numbers the next run must advance from: clock day-counts as of {{SUNDAY}}, detention as-of figure and its date, the last statutory Epstein release date, the newest roll-call number recorded, the newest correction ID.
4. **Spawn-prompt drift to fix** — any "standing" sentence inside Part A that the week's record superseded (e.g. a date that has passed, a figure the docket corrected). List it here; **do not edit Part A mid-run.** The next run applies the listed edits to Part A as its first action, commits them, and notes "Part A updated per TURNOVER_<date>" in its own turnover.
5. **Environment facts** — `vercel whoami`, Node/Python versions if they changed, the pushed SHA, anything that blocked a tool.

The turnover replaces nothing: Parts A–C stay as they are; the turnover is the delta the next run reads first after the three governing files.
