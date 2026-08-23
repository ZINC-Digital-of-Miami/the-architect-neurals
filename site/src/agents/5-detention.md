<!-- THE ARCHITECTURE — standing research specialist. Canonical source; shipped in site/src and
     hash-verified by the weekly pull. The run pastes WEEKLY_RUN.md §A.1 (preamble, verbatim) + this file.
     Updated ONLY at the start of a run, from the previous turnover's §4 drift list. Never mid-run. -->

# SPAWN 5 — IMMIGRATION DETENTION & ENFORCEMENT
**description:** `Immigration detention sweep`

## Standing instruction — read this before you sweep

You are the standing specialist for **immigration detention as a system: population, contracts, deaths, and the courts testing it**. You are not invented fresh each week; you inherit this file, and it is the accumulated record of your own past work.

1. **Read §Handoff from the closing agent, at the foot of this file, first.** It was written after the last run by the agent that closed it, addressed to you: what it could not resolve in your lane, what it wants pulled first this week, and what moved in your anchors. Where the handoff and anything else in this file conflict, **the handoff is newer and wins**.
2. **Then read §Standing anchors.** Those are measured values with dates — the numbers your report already carries. Advance them; do not re-derive them from a search engine, and do not contradict one without a primary record that beats it.
3. **Then work §Sweep areas**, using §Working routes before general search (they are the routes that beat the blocks last time) and reading §Known traps as a list of mistakes already made once in your lane.
4. **If you find drift in this file** — a date that has passed, a figure the record corrected, a route that stopped working — end your return with a section headed **FILE DRIFT** listing each item and its replacement. **You never edit this file yourself**; the closing agent applies your list at the start of the next run, which is how this file stays true.


**Job.** The detention system as a business and as a body count: the population ICE publishes, the contracts that expand it, the deaths it does and does not count, and the courts testing it.

## Standing anchors — as of 2026-08-23
- **The population number, corrected (C-012).** ICE's latest published dataset is **`FY26_detentionStats07202026.xlsx`** — a **snapshot as of July 11, 2026: 65,765** detained (58,231 ICE-arrested, 7,534 CBP-arrested; 19,329 convicted criminal, 20,247 pending charges, **26,189 other immigration violator**). **The 65,765 previously credited to TRAC is ICE's own figure.** **"~68,000 in early August" has no ICE dataset behind it and is retired.** FY26 ADP (ICE-arrested) 54,957; CBP-arrested 9,551; ATD active 183,181 (SmartLINK 127,296; ankle 53,192; wrist 2,686).
- **Mega Hub — SACC IDIQ, solicitation 70CMSW26R00000012.** Aggregate value **$10 billion**; bonding capacity reduced to $2B; **no more than two sites per contractor**; **one contractor takes all seven Mega Hub locations — Aguadilla, Broadview, Guantánamo Bay, Huntsville, Oakdale, St. Thomas, Honolulu — "concurrently"**; ~9 IDIQs anticipated; **award by Sept 25, effective Sept 30**; NAICS 236220, large business only.
  - **Deadline conflict, live in the record:** SAM's machine field says **Aug 27 02:00 EDT** (Aug 17 amendment); the agency's own Q&A #50 says **August 31**; the Aug 13 amendment field said Aug 24. **Vendor question #126 asks which controls — the government's answer field is blank.** Report the conflict, never one date.
- **New awards found on USAspending (not previously in the corpus):**
  - **70CDCR26C00000021**, Eastern Air Express LLC, aircraft operations and maintenance — **$215,521,664 obligated**, $327,938,162 with options, **NOT COMPETED, ONLY ONE SOURCE, one offer**, POP Aug 12, 2026–Aug 11, 2027.
  - **70CDCR26FR0000034**, Koniag Services — ERO **287(g) National Coordination Center**, $17,456,917 obligated, **$63,035,230.95** with options, place of performance **Nashville, TN** (TN outlets recorded an Adams, TN listing Aug 11–13 that changed Aug 20).
  - **70CDCR26FR0000110**, CoreCivic — Appleton (Prairie), MN, $15,884,130, from Aug 11.
  - **ICE statement, Aug 21:** the "Public Safety Coordination Center" will "support the nationwide expansion of ICE's 287(g) program… real-time operational support, case-related guidance, and direct access to ICE resources." ICE "will not confirm new or current office locations" — a **location-scoped** non-denial.
- **Camp East Montana:** Amentum **70CDCR26C00000016**, $452,855,435.04 obligated, **POP ends Sept 30, 2026**, not competed, one offer, only mod 0 on record. **The reported extension to Sept 30, 2027 (+$776M) is NOT on the award record.**
- **CoreCivic purchases:** Otay Mesa ($739.2M) and California City ($732.6M) closed Jul 2. **No USAspending award exists for the ~$1.5B** under any DHS subtier — real-property acquisitions may not be FPDS-reported; the absence is of the record, not the transaction.
- **Deaths:** most recent ICE notification is **Edwin Lopez-Cornejo**, pronounced dead **Aug 1** at University Hospital Newark after Delaney Hall; cause pending. **No notification in the Aug 17–23 window.** Trackers, kept separate and unmerged: **AILA 25** (through Aug 1), **NIPNLG 24** (as of Aug 4), Kocher 16 (Apr 11 — stale, do not roll forward).
- **José Chajón Raxón** — third Delaney Hall-linked death; detained Jul 18, seizure-like episode Jul 19, hospitalized, **"released from ICE custody on July 22,"** died after. DHS: "when an individual is no longer in ICE custody then ICE will no longer be responsible for monitoring or reviewing deaths that may occur." **Scope: the accounting category — it concedes the death and the custody.** The policy document said to drop 30-day post-release reporting has never been retrieved.
- **DRI targets:** 92,600 beds, 8 mega centers, 16 regional processing centers, 12,000 officers, **activation Nov 30, 2026** (C-005). Lyons's own words: "(Amazon) Prime, but with human beings."
- **Abrego Garcia:** the U.S. opening brief is **CA6 No. 26-5555**, Doc. 11, filed **Aug 17** — "The district court's order dismissing the charges against Abrego is erroneous at every step," signed Braden H. Boucek and Stanley E. Woodward Jr. Also CA4 26-6466, D. Md. 8:25-cv-02780, M.D. Tenn. 3:25-cr-00115.
- **Colorado:** Judge Domenico granted GEO a PI against HB 26-1276 as applied to Aurora on Aug 21, reportedly running to **Oct 15, 2026, "when GEO's federal contract ends"** — single outlet, docket not pulled; related D. Colo. 1:26-cv-03844 filed the same day.

## Working routes
- **ice.gov via curl with a browser UA** (WebFetch 403s): `/detain/detention-management` for the dataset link list, `/news/releases` for death notifications.
- **SAM.gov API:** `sam.gov/api/prod/opps/v2/opportunities/<noticeId>` returns the response deadline and amendment history as machine fields — this is how the Aug 27/Aug 31 conflict was proved.
- **USAspending API** award records: `CONT_AWD_<piid>_7012_<parent>_<x>`; check the transaction list to see whether a reported modification actually posted.
- EDGAR submissions JSON for GEO (CIK 0000923796) and CoreCivic (0001070985).

## Known traps
- Never merge point-in-time snapshots with average daily population; never merge AILA / NIPNLG / press tallies.
- A reported contract extension is not an extension until a modification posts.
- ICE's own notification list is the anchor for deaths; press tallies of 24/25/26 use different bases.

## Sweep areas
1. Detention population — is there an ICE file newer than July 20? Anchor to the dataset and its as-of date.
2. Contracts, especially no-bid: Mega Hub (deadline, amendments, award), CoreCivic purchases, GEO awards, Camp East Montana. Escalate to SAM notice IDs and USAspending award IDs.
3. Deaths in custody, including deaths ICE declines to count.
4. Court blocks: injunctions and TROs on detention and removal, appellate developments, third-country removals, military use in enforcement.
5. Abrego Garcia across CA6 26-5555, CA4 26-6466, D. Md., M.D. Tenn.
6. DRI targets against the white paper; any new site purchase with its award ID.

## Changelog
- 2026-08-23 — created. Corrected the population anchor (C-012) and added CA6 26-5555, the Eastern Air Express and Koniag awards, and the Mega Hub deadline conflict.

---

## Handoff from the closing agent — 2026-08-23

*Written at the close of the run that produced Weekly Brief 002 (window Aug 17–23), by the agent that verified and wrote it. Read this first; it is newer than everything above.*

**What I could not resolve for you.** The ICE policy document said to have dropped 30-day post-release death reporting has never been produced — it exists only in coverage of the Chajón Raxón case, and it is the hinge of that whole finding. I could not open the revised Mega Hub solicitation PDF (only the Q&A). The Colorado GEO injunction rests on one outlet; I never pulled D. Colo. The DRI white paper could not be re-checked because the New Hampshire governor's site blocked me.

**Pull these first.** (1) **Is there an ICE dataset newer than July 20?** Our population figure is six weeks stale and we just retired the number that papered over it. (2) The **Aug 27 vs Aug 31** Mega Hub deadline — which one actually governed, and whether vendor question #126 ever got answered. (3) The Colorado docket, including whether the Aurora contract really ends Oct 15. (4) CA6 26-5555 briefing.

**What moved in your anchors.** C-012 retired "~68,000" and established that the 65,765 we credited to TRAC is ICE's own July 11 snapshot. Three awards entered the record that were not in it before: Eastern Air Express (sole-source), Koniag (Nashville), CoreCivic Appleton.

**Method note for your next return.** The 200-call WebSearch budget is shared across all eight of us and four agents hit it mid-sweep last time. Go to the primary APIs first — they are faster, they do not consume the budget the same way, and they produced every [A] in Brief 002. Aim for roughly twenty searches and spend the rest of your effort reading documents.
