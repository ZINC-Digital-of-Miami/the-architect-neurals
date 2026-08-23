# THE ARCHITECTURE — WEEKLY RUN BOOK (v3, 2026-08-22)

Companion to `AGENT_INSTRUCTIONS.md` (policy) and `AUTOMATED_RUN_TASK.md` (the run). This file is the procedure **inside** the run: the gates, the eight research agents and the leash they run on, the writing standard, the exact in-run actions, and the turnover. Where files disagree: policy → `AGENT_INSTRUCTIONS.md`; pull/deploy/push mechanics → `AUTOMATED_RUN_TASK.md`; everything between → this file.

**Provenance, stated plainly.** §A.1 (the preamble) is the owner's text, verbatim, from the original WEEKLY_RUN.md (Google Doc `15bguyjbq2gxwwowpBglyOhLnzIDtBCzUdt2VHOXe7Iw`), plus one marked paragraph added 2026-08-22 (the leaf rule — see §A.0 for why). §A.2 (the eight sweep blocks) is the owner's text with dated anchor corrections marked `[upd 08-22]`; the marks stay so the original is recoverable from the Doc. Everything else in this file — §0, §A.0, §B, §C, §D — was written 2026-08-22 on the owner's instruction to replace a procedure that had no gates, no budgets, no writing standard, and no stop conditions, after a run spawned 15 unauthorized nested agents and drafted a brief in the wrong structure.

**Substitutions.** Resolve once at the top of the run; use literally everywhere.

| Token | Meaning | Example (run of 2026-08-23) |
|---|---|---|
| {{SUNDAY}} | week-ending Sunday, ISO | 2026-08-23 |
| {{WINDOW}} | the seven-day window | August 17–23, 2026 |
| {{TODAY}} | run date, long form | August 23, 2026 |
| {{SITE}} | live site root | https://the-architecture-neurals.vercel.app |
| {{PREV}} | `current_through` from the pulled MANIFEST.json | 2026-08-16 |
| {{NNN}} | this brief's edition number = previous count + 1 | 002 |

---

# §0 — GATES AND STOP CONDITIONS

The run is a sequence of gates. Each gate has a measured pass condition. A gate that fails **stops the run** with the notification named; it never improvises past the failure.

| Gate | Pass condition (measured) | On failure |
|---|---|---|
| G0 login | `vercel whoami` prints `zincdigitalofmiami` | stop: `NOT LIVE — Vercel CLI not logged in` |
| G1 clean | `git status --porcelain` empty in the project folder | stop: `NOT RUN — uncommitted local edits` |
| G2 pull | `pull_src.sh work` exits 0; every hash verified | one retry, then stop: `NOT RUN — pull failed: <reason>` |
| G3 window | {{PREV}} < {{SUNDAY}} | stop: `ALREADY RAN — current_through = {{SUNDAY}}` |
| G4 spawn | exactly 8 `Agent` calls in one message; each returns non-null | re-spawn the null one alone, identical prompt; if it nulls twice, proceed with 7 and say so |
| G5 verify | every `[A]` in the draft was opened by the main thread; every `[B]` has two named origins that are not one wire | demote; nothing unverified reaches the brief |
| G6 write | `brief_lint.py` exits 0 on the new brief | fix the brief; never the linter |
| G7 anchors | `update_part2.html` edited only at its five anchors; `#u-corrections` longer or equal; every clock advanced to {{SUNDAY}} | fix |
| G8 build | `build_site3.py` exits 0; `check.sh` exits 0 (includes monotonic guards vs the pulled manifest) | fix the source, rebuild; never `site/` by hand |
| G9 live | `/`, `/briefs/{{SUNDAY}}.html`, `/src/MANIFEST.json` all 200 from the public address; manifest `current_through` = {{SUNDAY}} | zip; `NOT LIVE — <error>` |
| G10 push | `git ls-remote origin main` == `git rev-parse HEAD` | `LIVE — NOT PUSHED: <error>` |
| G11 turnover | `_backups/TURNOVER_{{SUNDAY}}.md` exists and passes §D's checklist | the run is not finished until it does |

**Budgets.** Eight research agents, no more, no nesting. Each agent: one prompt, one return. Main thread: verification is bounded by the agents' rows — you verify what they found; you do not open a ninth sweep. If the window closes with a section thin, the honest output is a thin section with its absences stated, not a second sweep.

**Never, anywhere in the run:** edit `src/master_report.md` or `src/final.css`; edit `site/`; reword or drop a corrections entry; reset a clock; let a single-origin item in as a finding; assert a causal edge; spawn from inside a research agent; `git push --force`; commit `work/`; write a credential anywhere.

---

# §A — THE EIGHT RESEARCH AGENTS

## A.0 How to spawn, and the leash

- Tool: **Agent**, `subagent_type: "general-purpose"` (they need WebSearch, WebFetch, Bash). **All eight calls in ONE assistant message.** One at a time serializes the run.
- **Each agent is a leaf.** `general-purpose` agents carry the Agent tool themselves; on 2026-08-22 six of eight used it and spawned fifteen children nobody asked for. The preamble now forbids it in so many words (§A.1, last paragraph). If an agent's return shows it delegated anyway, its rows are still usable — but note it in the turnover (§D.4) so the prompt is tightened again.
- No ninth agent "to check the others." Verification is §C.3, main thread, against the primary record.
- Expected: 10–20 min wall clock per agent. If one returns null, re-spawn that one alone with the identical prompt. Twice null → proceed with seven and say so in the brief's method line and the turnover.
- Resolve {{TODAY}} and {{WINDOW}} before pasting. Paste §A.1 verbatim, then one §A.2 block. Do not paraphrase, trim, or "improve" either.

## A.1 The preamble — paste VERBATIM at the top of all eight prompts

You are a research agent for a tiered-evidence investigative brief on US politics. Today is {{TODAY}}. Your knowledge cutoff predates these events — you MUST use WebSearch/WebFetch for everything; do not rely on training priors. Window of interest: developments {{WINDOW}}. For standing items, also report current status even if the last development is older, with its date.

EVIDENCE STANDARD (hard gate). Tier every finding: **[A]** primary record cited directly — court docket entry, SCOTUS order, Federal Register document, official agency release or decision document, roll-call vote, SEC filing with accession number, contract record — or an on-the-record admission by the principal. **[B]** two or more GENUINELY INDEPENDENT named outlets AND the primary record identified, even if you could not fetch it. **[C]** single outlet, anonymous-sourced only, or aggregator — mark REJECTED WITH REASON, and still report it so the rejection is visible. Escalate every secondary report to its primary record: a vote → the roll call; a filing → the docket entry; a disclosure → the filing itself. Use supremecourt.gov, courtlistener.com, congress.gov, senate.gov, federalregister.gov, efts.sec.gov (EDGAR full-text), sam.gov, usaspending.gov, justice.gov, occ.gov, ice.gov, centcom.mil.

FALSE-CORROBORATION TRAP: syndications and aggregator repostings of ONE wire story are ONE source, not many. Count origins, not headlines. Watch for number drift across hops ($500M → "half a billion" → $550M; ">90%" → "93%") and always anchor to the origin document. Note explicitly when a major outlet's own domain is fetch-restricted and you are reading it via syndication.

Report the private position and the government action as SEPARATE dated facts with separate records. NEVER assert the causal link yourself — keep dotted edges dotted. Attach every denial to its allegation and record the denial's EXACT SCOPE: a knowledge-qualified denial, a motive-only denial, and a narrow personal denial standing beside a broad spokesperson denial are each findings in themselves. Where evidence for an expected edge does not exist, report it ABSENT and say what you searched — a verified absence is a result, not a gap.

RETURN FORMAT: raw structured data, not prose for a reader. One row per finding: DATE | FACT (one declarative sentence) | TIER | PRIMARY RECORD (name + URL/accession) | ORIGIN SOURCES (count origins) | DENIALS & exact scope | NOTES (drift, syndication, absence). End with two lists: (1) items you checked that produced NO qualifying evidence — the absences; (2) sub-[B] items rejected, each with its reason. Be exhaustive within your areas; run many searches. Do not summarize away specifics: exact dates, exact numbers, exact quotes.

**[Added 2026-08-22 — the leash.]** You are a LEAF agent. Do NOT spawn subagents, do NOT delegate, do NOT use the Agent tool under any name — every search and every fetch is done by you, in this context. Work you cannot complete yourself is reported in list (1) as an absence with what you tried, never handed to another agent. Stop when your sweep areas are covered or when you have made roughly sixty tool calls, whichever comes first, and return your rows then; a partial return with stated gaps beats an exhaustive one that never arrives.

## A.2 The eight sweep blocks — append ONE to the preamble per agent

Owner's text with dated anchor corrections marked `[upd 08-22]`. Do not edit these blocks during a run; list drift in the turnover (§D.4) and apply it at the start of the next run.

### SPAWN 1 — Elections & election machinery

description: "Elections and machinery sweep"

YOUR SWEEP AREAS:

1. November 3, 2026 midterms & election administration: DOJ or DHS involvement, federal monitors and where deployed, certification disputes, candidate-filing disputes, litigation over election procedures. DOJ's own releases are primary — its standing position is that monitoring "continues through the general election on November 3, 2026."
2. Election machinery: post-*Louisiana v. Callais* redistricting (new maps, mid-decade redistricting, state supreme court action), SAVE Act status in Congress (last action: cloture on the HAVA photo-ID variant failed 52–46, 4:36 a.m. Aug 8, 2026, Senate roll call #231; both chambers are in recess until Sept 14 **[upd 08-22]**), DHS/FEMA notices and grant conditions to states and the 26-state suit in D.R.I., suspended/moved/postponed primaries, the Missouri redistricting referendum fight in Cole County (hearing was Aug 18 — find the ruling; ballot-print deadline is Sept 8 **[upd 08-22]**).
3. SCOTUS emergency applications **26A124** and **26A139** (mail-ballot executive order, 23 states + DC): any order, briefing, or disposition. Pending without order since July 27, 2026 as of the last brief (27 days at Aug 23 **[upd 08-22]**) — an order EITHER WAY is a lead, and continued silence is itself reportable with the day count. Also any OTHER direct SCOTUS order to the president and documented compliance or defiance.

### SPAWN 2 — Insurrection Act & executive power

description: "Insurrection Act / executive power sweep"

YOUR SWEEP AREAS:

1. Insurrection Act: any invocation, proclamation, or new explicit threat to deploy troops against a US city; National Guard federalization or military deployment in US cities; related litigation and compliance. **Verify absence against the primary record**: query the Federal Register presidential-documents API for the window and report what it returned.
2. Direct court orders to the president or executive branch and compliance/defiance — especially any SCOTUS order and the administration's response. Contempt ledger: the DHS civil contempt in C.D. Cal. (Vasquez Perdomo, $500/day since Aug 4, 2026) and the Boasberg contempt inquiry (en banc pending since June 22, 2026).
3. Executive orders signed this window with structural significance (elections, law enforcement, emergency powers, civil service, citizenship). Cite the Federal Register document number, not the press coverage.
4. **[upd 08-22]** Director of National Intelligence: Walter (Jay) Clayton was confirmed 51–47 on July 28, 2026 (Senate roll call #211); Pulte's acting tenure is over (Corrections Log C-007). Report only new DNI/FHFA developments; do not re-report the acting stint as current.
5. Trial balloons on executive power: third-term/2028 statements, election-emergency statements, habeas suspension. Get the exact quote, date, venue, and primary source (official transcript, video, Truth Social post). The two standing poles: "Let me just say stranger things have happened" (Aug 11, 2026, on an election national-security emergency) and "I'd love to run, but the law is very strong" (Aug 11, 2026, on 2028).

### SPAWN 3 — The wars, the count

description: "Wars and Iran/Hormuz sweep"

YOUR SWEEP AREAS:

1. Iran / Strait of Hormuz: US or Iranian military action, strikes, naval blockade enforcement (vessels redirected/disabled/boarded — anchor the running tally to CENTCOM's own releases and flag drift), ceasefire status, escalation or de-escalation. The tempo of presidential statements: collect EACH with exact date, venue, and verbatim quote; note market-relevant statements and the market move as SEPARATE dated facts, asserting no causation.
2. Congressional war powers: authorization votes, war-powers resolutions, discharge motions — escalate to the actual roll call at senate.gov/congress.gov. Standing: H.Con.Res. 89 passed the House 214–208 (July 23); S.J.Res. 180 discharge failed 47–49 (July 23, roll call #207); S.J.Res. 181 discharge failed 49–50 (July 30, roll call #216). The report now carries this as a tier change — the check survives in one chamber only (C-008) **[upd 08-22]**. No floor votes are possible before Sept 14.
3. Casualty figures and any RECATEGORIZATION of them. Standing finding: in July 2026 the Pentagon moved Iran-war casualties from "Operation Epic Fury" to a new "Overseas Operations" category, restarting the count (displayed KIA 18→14; 600+ wounded became "207 since July 7"). Track: DoD/DCAS changes, Sen. Rosen's Aug 14 bill barring "manipulating casualty records" (GET THE BILL NUMBER — it was not yet posted), and the USS Lincoln conditions with each denial's exact scope (CENTCOM denies deaths aboard; the Navy denies an *increase in reported* suicidal ideation; Hegseth's is broad and evidence-free).
4. Other active US hostilities (Yemen, Venezuela/Caribbean, elsewhere): strikes, claimed legal authorities, congressional notifications, civilian-casualty reviews, casualty counts.

### SPAWN 4 — Epstein files & DOJ

description: "Epstein/DOJ compliance sweep"

YOUR SWEEP AREAS:

1. **Phang v. Blanche, D.D.C. No. 1:26-cv-01417 (Sullivan)** — the compliance case. At the Aug 13, 2026 hearing Sullivan warned of contempt: "I don't want to do it, but I will do it… That isn't a threat. That's a promise." Plaintiff's proposed compliance orders were due ~Aug 23 — i.e. this window **[upd 08-22]**. PULL THE DOCKET: any contempt order, compliance filing, redaction log, or new deadline. **Any contempt order is the lead finding of the week.** CourtListener has been blocking fetches — try storage.courtlistener.com PDFs, the court's own site, and PACER-derived reporting, and say which route worked.
2. Epstein Files Transparency Act compliance: DOJ's disclosure page (justice.gov/epstein) — any release after the standing last-activity date of April 3, 2026. The DOJ OIG audit of EFTA compliance. Withholding grounds asserted, and whether the withheld handwritten FBI interview notes (the 2019 trafficking allegation) are addressed by any DOJ statement.
3. **Preska unsealing, S.D.N.Y. (Giuffre v. Maxwell, 15-cv-07433 / US v. Maxwell)** — she rejected all of Maxwell's objections Aug 11–12, 2026 and ordered materials unsealed. Has the release actually EXECUTED? Any newly named individuals qualify only at [A]/[B].
4. Survivor litigation (including the Jane Does suit against DOJ and Google), and any DOJ leadership changes, resignations-in-protest, or whistleblower letters this window.
5. Attorney General Blanche's department: new OLC opinions, policy memos, personnel actions. Standing: the ~Aug 10–11 OLC opinion extending executive privilege to presidential communications with "private advisers" outside government.
6. **[upd 08-22]** The report's Chapter 21-O now carries the administration's Epstein explanations as a nine-phase dated chronology ending with Sullivan's Aug 13 warning. Any NEW official explanation this window is a tenth phase: quote it exactly, date it, and say which earlier phase it contradicts.

DENIAL-SCOPE DISCIPLINE IS THE POINT HERE: DOJ's institutional line is that it has "not KNOWINGLY violated, nor has it ever ACKNOWLEDGED violating" the Act — a knowledge-qualified denial that concedes nothing about the withholding. Blanche's December 2025 line — "There's no effort to hold anything back because there's the name Donald J. Trump" — is a MOTIVE denial, not a withholding denial. Record whether any new statement finally covers the allegation.

### SPAWN 5 — Immigration detention & enforcement

description: "Immigration detention sweep"

YOUR SWEEP AREAS:

1. Detention population: the most recent official ICE detention statistics release — anchor to the dataset and its as-of date; do NOT merge point-in-time figures with average-daily-population figures. Standing anchors: ~68,000 in early Aug 2026; record 70,766 on Jan 24, 2026; TRAC's 65,765 is a July 11 point-in-time.
2. Contracts, especially no-bid/sole-source: the up-to-$10B "Mega Hub" IDC solicitation (seven concurrent sites incl. Guantánamo; bids are due Aug 31, 2026 — after this window; report any amendment, Q&A, or extension; the award is next week's item **[upd 08-22]**), the ~$1.5B CoreCivic facility PURCHASES (California City, Otay Mesa), GEO awards, the Camp East Montana no-bid extension. Escalate to SAM.gov notice IDs and USAspending award IDs.
3. Deaths in custody: new ICE death notifications (ICE must publish them), plus deaths ICE declines to count. Standing finding: Jose Chajon-Raxon, third Delaney Hall-linked death, where ICE stated "when an individual is no longer in ICE custody, then ICE will no longer be responsible for monitoring or reviewing deaths that may occur" — a denial whose scope is the accounting category, not the death. Keep the competing YTD tallies (AILA, NIPNLG, Kocher) separate and labeled; do not merge them.
4. Court blocks: injunctions/TROs on detention and removal practice, appellate developments, third-country removal agreements and flights, Guard/military use in immigration enforcement.
5. Abrego Garcia: CA4 No. 26-6466 (briefing due Sept 21 / Oct 21 **[upd 08-22]**), D. Md. habeas 8:25-cv-02780, M.D. Tenn. 3:25-cr-00115 dismissal appeal.
6. **[upd 08-22]** DRI target: the report carries **November 30, 2026** (C-005 corrected a Sept 30 figure). Report any change to the 92,600-bed / 8 mega-center / 16 RPC / 12,000-officer targets against the white paper, and any new site purchase with its USAspending award ID.

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
7. **[upd 08-22] Four new Silence Ledger clocks (Consolidated Edition) — establish each day count as of {{SUNDAY}} and report any answer:** (a) Huffman/Garcia/Heinrich → Defense, Commerce, Energy, Interior, Feb 2, 2026, on officials'/donors'/Trump Organization equity in companies taking federal mineral stakes — documents were due Feb 26, 2026; (b) Warren/Blumenthal/Stansbury → the Trump Presidential Library Foundation, July 16, 2026, on the ~$14.5M gap between identified settlement proceeds and reported revenue; (c) Warren/Garcia/Blumenthal/Duckworth → DoD Inspector General, Aug 5, 2026, on $3.2B in awards to companies tied to 1789 Capital and American Ventures — has an investigation opened?; (d) the 15%/25% China chip remittances — any regulation, appropriation, or Treasury receipt showing they were ever collected.
8. **[upd 08-22] New standing money items from the Consolidated Edition:** Project Vault / EO 14415 (91 Fed. Reg. 46693) and the federal mineral-equity ledger (MP Materials, Trilogy, Lithium Americas, Vulcan/ReElement, Korea Zinc, USA Rare Earth, Atlantic Alumina) — any new federal stake, price floor, or insider sale; Stargate — MGX/G42/Tahnoon transactions and any filing that links Stargate capital to family revenue (standing: none — report ABSENT if still none); Argentina — the $40B package, Bessent–Citrone, Discovery Capital positions; the presidential library foundation's filings; Disney/ABC v. FCC (filed Aug 18, 2026) and the NYT v. Trump amended-complaint deadline of Aug 27, 2026 (dockets to Spawn 8; the money side — settlements, the $56.5M to the library — is yours).
9. **The un-drawn edge — confirm the absence:** any subpoena identifying Polymarket wallet holders, WLFI stake buyers, or an envoy's market position. This has been ABSENT every week; say what you searched and confirm it is still absent.

DO NOT merge these entities: DT Marks DEFI LLC (receives 75% of token-sale proceeds) is not DT Marks SC LLC (passive investor in the trust bank). Zach Witkoff (WLF CEO, trust-bank president, ALT5 chairman) is not Steve Witkoff (special envoy).

### SPAWN 8 — The dockets

description: "Docket sweep: prosecutions and appeals"

YOUR SWEEP AREAS — identify every case number; pull the docket entry, not the coverage:

1. **US v. Comey** — CA4 Nos. 25-4673(L)/25-4674 (argument set for Sept 15, 2026, Richmond **[upd 08-22]**): any scheduling change, supplemental briefing, or opinion. And the separate E.D.N.C. No. 4:26-cr-00016-FL ("86 47" threat case): government responses to the four dismissal motions were due Aug 18 — pull them **[upd 08-22]**; arraignment; trial set for Oct 21, 2026.
2. **US v. Letitia James** — the consolidated CA4 appeal; any new indictment attempt.
3. **US v. Bolton** — D. Md. 8:25-cr-00314-TDC, sentencing set Oct 28, 2026. NOTE: the plea was to **Count 12 only**, per the docket minute entry — coverage claiming "all 18 counts" is wrong; the docket controls.
4. Any grand jury or probe targeting Gavin Newsom.
5. Press subpoenas: new DOJ subpoenas to journalists or outlets, and litigation over them.
6. **Harvard** — CA1 No. 25-2230 (funding appeal; government reply filed Aug 12, 2026; watch for an argument date) and D. Mass. 1:26-cv-10844-MJJ (Title VII; MTD hearing Sept 24, 2026). The Title VI suit was dismissed Aug 13, 2026 (D. Mass. 1:26-cv-11352-RGS) — any appeal?
7. **AAP v. Kennedy** — CA1 No. 26-1503; the government moved Aug 14, 2026 to expedite argument or submit on the briefs. Any ruling, argument date, or district-court movement.
8. **Abrego Garcia** — CA4 26-6466, D. Md. 8:25-cv-02780, M.D. Tenn. 3:25-cr-00115.
9. NEW indictments of political adversaries (former officials, prosecutors, judges, governors) and any grand jury refusals to indict.
10. Contempt proceedings against DOJ or administration officials.
11. **[upd 08-22]** The press dockets the report's Chapter M now tracks: Disney/ABC v. FCC (filed Aug 18, 2026 — complaint, any TRO motion, FCC response); NYT v. Trump (amended complaint due Aug 27, 2026); the refiled WSJ suit (May 27, 2026); the Selzer state case (argued Jan 30, 2026, no ruling); the AP D.C. Circuit merits (argued Nov 24, 2025, no opinion — report the day count); the USAGM/VOA stay (D.C. Cir., since Mar 31, 2026). Also the White House ballroom: the D.C. Circuit self-stay expired Aug 21 — what happened, and the status of the SCOTUS application filed Aug 14.

---

# §B — THE WRITING STANDARD

The brief is the product. It is read by people, not parsed by a pipeline, and it sits beside a 50,000-word master whose voice it must match. The standard below is **measured from Brief 001 (2026-08-16) and the master report**, not invented; `brief_lint.py` enforces the parts a machine can check, and the rest is on you.

## B.1 The shape — fixed, enforced

Eight `<section>` blocks, each with exactly one `<h2>`, in this order and with this wording:

1. **The lede** — in `<section class="lede">`
2. **Architecture I — The family money**
3. **Architecture II — Executive power**
4. **Architecture III — The wars and the count**
5. **The node where the architectures touch** — carries the `.dotted-edge` box
6. **What would change the tier**
7. **Rejected below [B], with reasons** — ends with the "Checked for and not found" paragraph
8. **Next week's priorities** — ends with the method line and `<p class="mono">EDITION {{NNN}} · {{SUNDAY}}</p>`

Masthead: `<h1 class="mast">Weekly Brief — Edition {{NNN}}</h1>` and `<p class="mast-sub">Window: … · compiled … · eight parallel research tracks</p>`. Copy `src/briefs/_TEMPLATE.html` and replace every placeholder; the linter fails on any that survive.

No `<h3>`/`<h4>`, no lists, no tables, no `<style>`, no inline styles, no classes that are not in `final.css`. 2,500–6,500 words. No paragraph over 320 words. At least twenty tier chips; at least one `[C]` rejection; at least one verified absence.

## B.2 The voice — what 001 actually does

**Every paragraph opens with a fact or a bolded lead, never a frame.** 001's openings: "On August 14 the Office of the Comptroller of the Currency granted…"; "**The bank.** The OCC decision (Aug 14) approves…"; "**The corrections.** The carried-forward thread held that…". Two to four words in bold, then the evidence. The linter wants at least six of these.

**The documents do the accusing.** The record is named inside the sentence that relies on it — "an 8-K eighteen days later states: 'After discussion with The Nasdaq Stock Market LLC…'" — and the tier chip sits on that sentence, not at the end of the paragraph. Accession numbers, docket numbers, roll-call numbers, decision numbers appear in prose, in parentheses, where a reader who wants to check can.

**Paragraphs build and land.** A section is three to six paragraphs. Each paragraph makes one move — a document, a correction, a non-answer, a sequence — and ends on the sentence that carries its weight. 001 closes a paragraph with "the token issuer lending money to its own largest bagholder while the issuer's CEO chairs the borrower's board A." That is the cadence: the long evidentiary sentence, then the short one that says what it means, then the chip.

**Academic in discipline, human in cadence.** Short sentence after a long one. Plain verbs — *states, approves, denies, shows, holds* — over *constitutes, represents, underscores*. One dry, earned observation per section at most: "a brief that only adds and never subtracts isn't applying its own standard"; "The non-answer is the finding, three times over." The observation is always about the record, never about the people.

**Denials keep their scope.** "a *knowledge*-qualified denial, which denies knowing violation while conceding nothing about the underlying withholding." Read each denial for exactly what it denies and say that.

**Adjacency is stated as adjacency, every time.** "Two documents, one architecture. No causal claim required." "The investment and the export decision are separate dated facts. The causal edge remains dotted." Never "linked to," "tied to," "in the wake of," "following" used to imply cause.

**Numbers are anchored and drift is shown.** "$750M cash plus $750M *of $WLFI tokens*"; "(the carried '5/19' date was one day off)"; "55→59 vessel redirections." Where sources differ, both figures appear with their as-of dates; they are never averaged.

**Quiet weeks are written, not padded.** "No material change" is a legitimate brief: the clocks advanced, the absences were checked, the rail moved. Say what was searched. Do not inflate a thin section with background the master already carries.

## B.3 What the voice is not

Not a news story (no "sources say," no "experts warn," no headline-sentences). Not a memo (no bullets, no "Bottom line," no "Key takeaways"). Not a polemic (no adjectives doing a tier's work — *brazen, stunning, chilling* — and no motive). Not a model's filler: the linter bans *it is worth noting, underscores, in conclusion, a stark reminder, raises questions, sends a message, at the end of the day, delve, tapestry, landscape of, a testament to, navigating, unpack, double down, shocking, bombshell, slammed*. Rhetorical questions: two per brief at most, and 001 used none.

## B.4 The edits to `update_part2.html` are written in the same voice

`#u-week` is the page's running record, not a changelog: dated declarative paragraphs with bolded leads, the same chips, the same scope discipline. A correction's `.was` is the premise as carried; its `.now` is the primary record, quoted, with the accession or docket. A clock's `.what` is one sentence: who asked whom, what, by when.

---

# §C — THE EXACT ACTIONS

Run in the main thread, in order. Commands are literal. Steps that `AUTOMATED_RUN_TASK.md` specifies are referenced, not duplicated.

## C.1 Start clean, pull, gate (G0–G3)

```
cd "/Users/zincdigital/Documents/the architect neural"
vercel whoami                              # G0
git status --porcelain                     # G1 — must print nothing
[ -d work ] && mv work "work.prev-$(date +%Y%m%d-%H%M%S)"   # a stale draft in work/ must never be built
bash pull_src.sh work                      # G2 — hash-verified working copy
python3 -c "import json;print(json.load(open('work/MANIFEST.json'))['current_through'])"   # {{PREV}}; G3
```

`work.prev-*` is git-ignored; delete it at the end of a successful run. Read `work/AGENT_INSTRUCTIONS.md`, this file, and the newest `_backups/TURNOVER_*.md` in full. Apply the turnover's §D.4 drift list to `work/src/WEEKLY_RUN.md` now, as the first edit, and note it in your own turnover.

## C.2 Spawn (G4)

One message, eight `Agent` calls, `subagent_type: "general-purpose"`, each prompt = §A.1 verbatim + one §A.2 block, substitutions resolved. Nothing else in that message.

## C.3 Verify (G5)

For every row you intend to publish at `[A]`: open the primary record yourself and quote from it. For `[B]`: confirm the two origins are genuinely independent — if both trace to one wire, it is one origin and the row is `[C]`. Reconcile every number and date against the origin document; record the drift in the brief's notes. Anything surviving only as `[C]` goes to "Rejected below [B]" with its reason and its context paragraph. Anything an agent marked ABSENT that you can disprove is a finding; anything you cannot, stays ABSENT with the search named.

## C.4 Write the brief (G6)

```
cp work/src/briefs/_TEMPLATE.html work/src/briefs/{{SUNDAY}}.html
# write it to §B; then:
python3 work/src/brief_lint.py --css work/src/final.css work/src/briefs/{{SUNDAY}}.html
```

The linter must exit 0 before you touch anything else. Fix the brief, never the linter.

## C.5 Edit `work/src/update_part2.html` — five anchors, nothing else (G7)

| Anchor | Exact action |
|---|---|
| `#u-week` | Replace with the new week in §B.4 voice. Update the `<h4>` window label. The outgoing week already lives in its brief; keep only what still carries. |
| `#u-node` | Only if the week changed the node. Edit the inline SVG's labels/tiers. Dotted stays dotted unless a document closed it — and if one closes, that is the lede. |
| `#u-corrections` | **APPEND ONLY.** Next ID in sequence (the turnover names it). Context for an existing entry is a new dated block `DATE · C-00N · context added`, never an edit. |
| `#u-silence` | Advance every `.num` to {{SUNDAY}}; set `.clocks-asof` to {{SUNDAY}}. An answered clock is replaced by the answer and the date it arrived. The count never goes down (check.sh). |
| `#u-threads` | Retire resolved threads stating how; add the new checks; keep date order. |

## C.6 Map — only if nodes or edges changed

Edit `work/src/map_source.json`; run `node work/src/build_neural_map.js`; copy the printed counts and {{SUNDAY}} into `work/src/neural_map.html` (kicker, counts, chips, ledger, stamp). `check.sh` fails if the prose and `data.json` disagree. Quiet week: set the date, add the ledger line "no edge changes this window."

## C.7 Rail, build, guard (G8)

In `work/src/build_site3.py` → `rail_stops`: drop passed dates, add newly docketed ones, `NOV 3` stays `big`. Then:

```
cd work && python3 src/build_site3.py && ./check.sh
```

`check.sh` runs the brief linter on every brief, page hygiene, the `final.css` pin, and — because `work/MANIFEST.json` is the previous week's — the monotonic guards: corrections ≥, clocks ≥, briefs +1, map nodes ≥, `current_through` advanced, index growth ≤ 120 KB. Record `shasum -a 256 site/index.html`.

## C.8 Deploy, verify, push (G9, G10)

Exactly `AUTOMATED_RUN_TASK.md` §5–§6: `./deploy.sh --no-build --prod` from `work/`; verify the three URLs from the public address; then sync back, `./check.sh` on the synced tree, commit `Weekly Brief {{NNN}} — week ending {{SUNDAY}}`, push, confirm `ls-remote` == `HEAD`. Zip only if G9 failed. Then remove `work.prev-*`.

## C.9 Archive, artifact, notify

Drive: `AUTOMATED_RUN_TASK.md` §6 (folder `1_S9ouWMx2SWZ7mYCN52V296hdGzFkOAs`; text only). Artifact: republish in place only if `Artifact action:list` shows `43bad372-6bd6-4ce6-a2e8-c1d5a06589f4` as owned by this account; otherwise skip and say so; never create a second one. Notify per `AUTOMATED_RUN_TASK.md` §7: lede verbatim; one status line; what changed; next checks.

---

# §D — TURNOVER (written after the work; the run is not done without it) (G11)

Write `_backups/TURNOVER_{{SUNDAY}}.md` before the commit in C.8. Facts only, for the agent that runs next Sunday. Five numbered sections; each must be present even if its content is "none."

1. **What moved.** Every correction/context ID added; every thread retired (how) or added; every clock answered; every map edge changed. IDs and dates only.
2. **What did not resolve.** Every origin domain that 403'd and the route that worked; every docket that could not be read and why; every "find the award / find the bill number" still open.
3. **Standing anchors.** The exact numbers the next run advances from: `current_through`; next correction ID; every clock's day count as of {{SUNDAY}}; detention figure and as-of date; last statutory Epstein release date; newest Senate roll call recorded; map node/edge counts; the pushed SHA.
4. **Spawn-prompt drift.** Every sentence in §A.2 that this week's record superseded — quote it, give the replacement, name the record. Also: any agent that delegated despite the leaf rule (which one, how many children) so §A.1's last paragraph can be tightened. **Do not edit §A.2 mid-run**; the next run applies this list first and commits it.
5. **Environment.** `vercel whoami`; Node/Python versions if changed; any tool that blocked; anything the next run must know before C.1.

The turnover replaces nothing. §A–§C stay as they are; the turnover is the delta the next run reads after the three governing files.
