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

## A.2 The eight standing specialists

Each agent is a **standing specialist with a file of its own** in `src/agents/`, shipped with the working copy and hash-verified by the pull. The file carries the specialist's job, its standing instruction, the anchors it owns, the fetch routes that beat the blocks, the traps it has already hit, its sweep areas, and — at the foot — **the handoff written to it by the agent that closed the previous run**.

| # | File | Specialist |
|---|---|---|
| 1 | `src/agents/1-elections.md` | Elections & election machinery |
| 2 | `src/agents/2-executive-power.md` | Insurrection Act & executive power |
| 3 | `src/agents/3-wars.md` | The wars, the count |
| 4 | `src/agents/4-epstein-doj.md` | Epstein files & DOJ compliance |
| 5 | `src/agents/5-detention.md` | Immigration detention & enforcement |
| 6 | `src/agents/6-succession.md` | Succession, health, 2028 |
| 7 | `src/agents/7-money.md` | The money (EDGAR-first) |
| 8 | `src/agents/8-dockets.md` | The dockets |

**Each prompt = §A.1 preamble, verbatim (including the leaf paragraph) + the whole specialist file, with substitutions resolved.** Do not summarize the file and do not send only its sweep areas: the standing instruction, the owned anchors and the handoff are what stop the agent starting cold every week.

**Never edit a specialist file during a run.** Agents return a `FILE DRIFT` section; the closing agent applies it at the *start* of the next run (§C.1) and records that it did so.

The eight sweep blocks that used to live inline here are now §Sweep areas inside each specialist file; the original wording is preserved there and in the owner's Google Doc named under Provenance.

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
4. **Specialist handoffs — write all eight.** For each `src/agents/N-*.md`, replace its `## Handoff from the closing agent` section with a new dated one addressed to that specialist: *what I could not resolve for you* (named, with what was tried), *pull these first* (two to four items, in order, with dates), and *what moved in your anchors* (including any correction that overturned something the file asserted). Then apply every `FILE DRIFT` item the agents returned, and update each §Standing anchors to the values this run measured. **This is the memory. A run that skips it makes next week start cold.** Also record any agent that delegated despite the leaf rule, so §A.1 can be tightened.
5. **Environment.** `vercel whoami`; Node/Python versions if changed; any tool that blocked; anything the next run must know before C.1.

The turnover replaces nothing. §A–§C stay as they are; the turnover is the delta the next run reads after the three governing files.
