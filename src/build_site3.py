#!/usr/bin/env python3
"""Editorial static-site builder with shared navigation, accessible reading controls,
preserved report, weekly archive, relationship map, and source-backed research pages.

Reads sources from this script's directory (src/): master_report.md, update_part2.html,
sources_manifest.md, final.css, briefs/*.html.
Emits ../site/ (index.html + styles.css + sources.html + briefs/*.html + robots.txt + sitemap.xml)
plus artifact.html (same body, no document wrapper) for publishers that wrap content themselves.

Weekly: add briefs/YYYY-MM-DD.html and refresh the dated update in update_part2.html,
preserving every prior correction and archive record, then re-run.
Brief numbering, the edition number, the masthead date, the archive, the per-brief pages,
and the sitemap all follow from the briefs/ directory automatically."""
import re, html, pathlib, unicodedata, os, json, sys
from dataclasses import asdict
import markdown

# Portable paths. Sources live beside this script; output goes to ../site (the Vercel deploy dir).
# Override with ARCH_ROOT / ARCH_DIST if you keep a different layout.
ROOT = pathlib.Path(os.environ.get("ARCH_ROOT") or pathlib.Path(__file__).resolve().parent)
DIST = pathlib.Path(os.environ.get("ARCH_DIST") or (ROOT.parent / "site"))
(DIST / "briefs").mkdir(parents=True, exist_ok=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from report_references import link_report_references
from report_navigation import link_silence_clocks, repair_directional_references
reference_inventory = []

def reference_links(markup, source):
    markup = repair_directional_references(markup, source)
    linked, inventory = link_report_references(markup, toc,
        aliases={"Chapter 21": "The Budget Architecture — Priorities Revealed"})
    reference_inventory.append({"source": source, "resolved": [asdict(row) for row in inventory.resolved],
        "unresolved": [asdict(row) for row in inventory.unresolved]})
    return linked

master = (ROOT / "master_report.md").read_text()
split_at = master.index("## Executive Summary")
title_block_md, body_md = master[:split_at], master[split_at:]

# front-matter fold
fm_split = title_block_md.index("**CONSOLIDATED EDITION")
head_md, fm_md = title_block_md[:fm_split], title_block_md[fm_split:]

# inline ed-notes
ED = '<span class="ed-note">[<strong>Edition update, 2026-08-16</strong> — %s]</span>'
notes = [
 ("Blanche's confirmation remains stalled in part over the Epstein files",
  ED % 'Blanche was confirmed Attorney General 50–49–1 at 4:17 a.m. on Aug 8, 2026 (Senate roll call #230; Collins and Murkowski no), and sworn in Aug 10 by Third Circuit Judge Emil Bove, his former co-defense counsel, with press excluded. See <a href="#update">The Record Since July 19</a>.'),
 ("## Current Documentation (2025–July 2026)",
  ED % 'This part runs through July 19, 2026. For July 19 – August 16 — the war, the count, the dockets, the money — see <a href="#update">The Record Since July 19</a>.'),
 ("These are documented facts about electoral mathematics",
  '<span class="ed-note">[<strong>Correction, 2026-09-08 · C-017</strong> — Trump won the 2024 national popular-vote plurality: 77,302,580 votes (49.80%), ahead of Harris. A plurality below 50% is not a popular-vote loss. See <a href="#u-c017">the FEC record and correction</a>.]</span>'),
 ("## Formation: The Making of the Man",
  '<span class="ed-note">[<strong>Research added, 2026-09-08</strong> — Follow <a href="/topics/trump-early-financing.html">Trump’s early financing, Rothschild Inc. and Wilbur Ross</a>: the creditor negotiations, exact entities, later personnel bridge and remaining records to check. <a href="/neural.html?topic=trump-early-financing">Explore the dated connections</a>; <a href="/topics/trump-later-financing.html">continue into later financing</a>.]</span>'),
]
for anchor, note in notes:
    idx = body_md.find(anchor)
    if idx == -1:
        print("WARN anchor:", anchor[:40]); continue
    if anchor.startswith("## "):
        le = body_md.index("\n", idx); body_md = body_md[:le] + "\n\n" + note + body_md[le:]
    else:
        se = body_md.index(".", idx + len(anchor)); body_md = body_md[:se+1] + " " + note + body_md[se+1:]

md = markdown.Markdown(extensions=["tables"])
body_html = md.convert(body_md)
head_html = md.reset().convert(head_md)
fm_html = md.reset().convert(fm_md)

# ids + toc
seen = {}
def slugify(s):
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s))
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "sec"
    n = seen.get(s, 0); seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"
toc = []
def add_id(m):
    tag, inner = m.group(1), m.group(2)
    sid = slugify(inner); toc.append((tag, sid, re.sub(r"<[^>]+>", "", inner)))
    return f'<{tag} id="{sid}">{inner}</{tag}>'
body_html = re.sub(r"<(h[23])>(.*?)</\1>", add_id, body_html, flags=re.S)
# Assign subsection anchors after the existing headings so their published IDs stay stable.
body_html = re.sub(r"<(h4)>(.*?)</\1>", add_id, body_html, flags=re.S)
toc = [(m[1], m[2], re.sub(r"<[^>]+>", "", m[3]))
       for m in re.finditer(r'<(h[234]) id="([^"]+)">(.*?)</\1>', body_html, re.S)]
h2s = [(sid, txt) for tag, sid, txt in toc if tag == "h2"]
slug_of = {txt: sid for sid, txt in h2s}

# deks + part openers with reading time
DEKS = {
 "Executive Summary (one page)": "The whole argument in one page — three architectures, one precise sentence, and the date it gets tested.",
 "Formation: The Making of the Man": "Part Zero. The father's two words — “king” and “killer” — and where the machinery of endless retribution was learned.",
 "The Crown: The Architecture of Power": "What has actually been consolidated — personnel, prosecution, the commanding heights of the economy — and, just as carefully, what has held.",
 "The Money: The Profit Architecture": "How authority converts to family wealth: the crypto empire, the envoy economy, the pardon market, the enforcement industry — documented deal by deal.",
 "The Ideology: Supremacy Politics and Its Limits": "What “Nazi-light” gets right, what it gets wrong, and the precise words the evidence actually supports.",
 "The Historical Lens — retained in full": "Why 1930s Germany is in this report at all — as one analytic lens among several, never as the verdict.",
 "The Historical Record": "Weimar to 1934, as documented history: how a constitutional republic dismantled itself legally, step by dated step.",
 "The Scholarly Framework": "What Snyder, Arendt, Browning, Albright, and the democratic-erosion literature actually say — and don't.",
 "Pattern Recognition": "The ten mechanisms, 2015–2026: each historical mechanism stated precisely, then tested against the American record.",
 "Current Documentation (2025–July 2026)": "The primary-source record: executive orders, detention metrics, the budget, the war, the home front — through July 19.",
 "The Honest Assessment": "Where the parallels are strongest, where they break down, and what pattern recognition cannot tell you.",
 "Pattern Recognition Is Not Prophecy — It Is Responsibility": "The conclusion: what is being built, what would falsify this report's thesis, and the nearest date on which it is tested.",
 "Appendix A — Editorial Method and Verification History": "How this report was built, what was corrected along the way, and the standing cautions its own reviewer imposed.",
 "Appendix B — Provenance: What This Edition Consolidated": "Every source document folded into this master, what it contributed, and what could not be reached.",
}
parts = re.split(r'(<h2 id="[^"]+">.*?</h2>)', body_html)
out, order = [], 0
total_words = 0
for i, chunk in enumerate(parts):
    m = re.match(r'<h2 id="([^"]+)">(.*?)</h2>$', chunk, re.S)
    if m:
        order += 1
        sid, inner = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", "", inner)
        nxt = parts[i+1] if i+1 < len(parts) else ""
        words = len(re.sub(r"<[^>]+>", " ", nxt).split()); total_words += words
        mins = max(1, round(words/220))
        dek = DEKS.get(txt, "")
        out.append(
          f'<header class="part-open"><div class="pmeta"><span>Section {order} of {len(h2s)}</span>'
          f'<span class="rt">~{mins} min read</span><span class="top"><a href="#top">Back to top &uarr;</a></span></div>'
          f'<h2 id="{sid}">{inner}</h2>' + (f'<p class="dek">{dek}</p>' if dek else "") + "</header>")
        if txt == "Formation: The Making of the Man":
            out.append('<aside class="research-note" aria-label="Research navigation">'
                       '<span class="topic-meta">Research navigation · 2026-09-08</span><br>'
                       '<a href="/topics/trump-early-financing.html">'
                       'Research topic: early financing and creditor records</a></aside>')
    else:
        out.append(chunk)
body_html = reference_links("".join(out), "master_report.md:body")
head_html = reference_links(head_html, "master_report.md:title")
fm_html = reference_links(fm_html, "master_report.md:edition-notes")
read_total = round((total_words/220 + 15))

# ---------- orientation ----------
S = slug_of  # by exact h2 text
crown, money, ideol = S["The Crown: The Architecture of Power"], S["The Money: The Profit Architecture"], S["The Ideology: Supremacy Politics and Its Limits"]
execs, hist, concl = S["Executive Summary (one page)"], S["The Historical Lens — retained in full"], S["Pattern Recognition Is Not Prophecy — It Is Responsibility"]
honest, curdoc = S["The Honest Assessment"], S["Current Documentation (2025–July 2026)"]

sentence = f'''
<section class="sentence" id="the-sentence">
  <div class="kicker">The precise sentence the evidence carries</div>
  <blockquote>&ldquo;A personalist, patrimonial regime-in-formation, using supremacist mobilization rhetoric, inside a still-functioning constitutional shell.&rdquo;</blockquote>
  <p class="attr">— the <a href="#{execs}">Executive Summary</a>. Not a prediction; a description that is tested, with dates. The nearest date is <a href="#u-threads">November 3, 2026</a>.</p>
</section>'''

arch3 = f'''
<section id="arch">
<div class="deck-label">Three architectures &middot; start where you want</div>
<div class="arch3">
  <a href="#{crown}"><span class="n">I &middot; POWER</span><h3>The Crown</h3>
    <p>The concentration of authority in one man — personnel, prosecution, the economy's commanding heights — with royal and third-term signaling in the open. And the ledger of what has held: courts obeyed so far, elections conceded so far.</p>
    <span class="go">Read the power architecture &rarr;</span></a>
  <a href="#{money}"><span class="n">II &middot; MONEY</span><h3>The Money</h3>
    <p>The conversion of that authority into family wealth: WLFI, USD1, $TRUMP, the envoy economy, foreign-state revenue, the pardon market, detention as an industry — each deal a dated, documented fact.</p>
    <span class="go">Read the profit architecture &rarr;</span></a>
  <a href="#{ideol}"><span class="n">III &middot; IDEOLOGY</span><h3>The Ideology</h3>
    <p>The enemies, grievances, and justifications that fuel the first two — held to the same evidence discipline, including where the darkest analogies break down.</p>
    <span class="go">Read the ideology architecture &rarr;</span></a>
</div>
</section>'''

howto = f'''
<section id="howto">
<div class="deck-label">How to read this report</div>
<div class="howto">
  <div class="card legend">
    <h4>The evidence discipline</h4>
    <p><span class="tier a">A</span> <strong>Primary record cited directly</strong>, or an on-the-record admission — the docket entry, the roll call, the filing itself, the agency's own decision document.</p>
    <p><span class="tier b">B</span> <strong>Two-plus genuinely independent named outlets</strong> with the primary record identified. Syndications of one wire story count as one origin — origins are counted, not headlines.</p>
    <p><span class="tier c">C</span> <strong>Single outlet, anonymous, or aggregator</strong> — rejected, with the reason stated. Rejections are published, not hidden.</p>
    <p><span class="tier abs">ABSENT</span> <strong>Checked for and not found.</strong> A verified absence is a result, not a gap — some of this report's most important findings are absences.</p>
    <p><strong>Dotted edges.</strong> A documented sequence is never asserted as a proven cause. Where two facts sit suggestively close, the edge between them is drawn dotted and labeled — and stays dotted until a document closes it.</p>
    <p><strong>Denials, with scope.</strong> Every denial stays attached to its allegation, read for exactly what it denies — a knowledge-qualified denial, a motive-only denial, and a narrow denial beside a broad one are each findings.</p>
  </div>
  <div class="card paths">
    <h4>Three ways in</h4>
    <div class="reading-path"><span class="pm">~10 MIN</span><a class="pt" href="#the-sentence">The ten-minute read</a>
      <span class="pd">The sentence &rarr; <a href="#{execs}">executive summary</a> &rarr; <a href="#u-week">this week's lede</a> &rarr; <a href="#u-node">the node</a> &rarr; <a href="#{concl}">the conclusion</a>.</span></div>
    <div class="reading-path"><span class="pm">~50 MIN</span><a class="pt" href="#{money}">The evidence spine</a>
      <span class="pd">The <a href="#{money}">money architecture</a> &rarr; <a href="#{curdoc}">current documentation</a> &rarr; <a href="#u-corrections">corrections</a> &rarr; <a href="#u-silence">the silence ledger</a>.</span></div>
    <div class="reading-path"><span class="pm">~{read_total//60} HR {read_total%60} MIN</span><a class="pt" href="#{execs}">The full synthesis</a>
      <span class="pd">Cover to conclusion in order, the <a href="#{hist}">historical lens</a> in full, honest assessment included.</span></div>
  </div>
</div>
</section>'''

cast = f'''
<section id="cast">
<div class="card cast">
  <h4>The cast, briefly — people and vehicles this report keeps distinct</h4>
  <p>A guide to the principal figures already covered in the report. Follow each section for its dated evidence, corrections, denials, and limits.</p>
  <h5>People</h5>
  <dl>
    <dt>Donald Trump</dt><dd>The report's principal subject: <a href="#{S['Formation: The Making of the Man']}">formation and early financing</a>, <a href="#{crown}">presidential authority</a>, and <a href="#{money}">family businesses</a>.</dd>
    <dt>Wilbur Ross</dt><dd>Trace his <a href="/topics/trump-early-financing.html">Rothschild Inc. creditor-side work in the Taj restructuring</a> and his later role as Trump's Commerce secretary. The <a href="/neural.html?entity=ROSS&amp;topic=trump-early-financing">dated map</a> keeps employment, negotiation and public office distinct.</dd>
    <dt>Donald Trump Jr.</dt><dd>1789 Capital; Polymarket adviser. His investment and advisory roles are covered in <a href="#{money}">the money architecture</a>. <a href="https://1789capital.vc/don-trump-jr">1789's partner biography</a>. <a href="/neural.html?entity=DONALD_TRUMP_JR">View individual connections</a>.</dd>
    <dt>Eric Trump</dt><dd>American Bitcoin; ALT5 <em>observer</em>, never seated as director (corrected at [A]). Read <a href="#u-corrections">the correction</a> alongside <a href="#{money}">the family portfolio</a>. <a href="/neural.html?entity=ERIC_TRUMP">View individual connections</a>.</dd>
    <dt>Steve Witkoff</dt><dd>Diplomacy and financial disclosures, including the distinction between agency and OGE certification. Read <a href="#u-corrections">the dated certification correction</a> and <a href="#{money}">the envoy economy</a>; his son's company roles are listed separately.</dd>
    <dt>Zach Witkoff</dt><dd>WLF CEO, trust-bank president, ALT5 chairman. Follow <a href="#{money}">the company and trust-bank records</a>. <a href="/neural.html?entity=ZACH_WITKOFF">View individual connections</a>.</dd>
    <dt>Jared Kushner</dt><dd>Affinity Partners — Gulf sovereign money; the envoy economy's other pole. Read <a href="#{money}">the envoy economy and foreign-state revenue chapters</a>.</dd>
    <dt>JD Vance</dt><dd>Vice-presidential authority and the Rockbridge / 1789 references in <a href="#{ideol}">the network chapter</a>. <a href="/neural.html?entity=VANCE">Dated individual connections</a>.</dd>
    <dt>Elon Musk</dt><dd>The dated records connect Trump's November 2024 advisory-role announcement with Musk's January 2025 AfD campaign appearance. <a href="/neural.html?entity=MUSK">Explore the map</a> and <a href="/topics/germany-afd.html#records">source context</a>.</dd>
    <dt>Alice Weidel</dt><dd>AfD's 2025 chancellor candidate; campaign participation and a vice-presidential pool record are kept separately dated. <a href="/neural.html?entity=WEIDEL">Explore her connections</a>.</dd>
    <dt>Stephen Miller</dt><dd>Immigration policy and the enforcement structure covered in <a href="#{curdoc}">the current documentation</a>.</dd>
    <dt>Todd Blanche</dt><dd>The president's former defense lawyer; confirmed Attorney General Aug 8, 2026, 50&ndash;49&ndash;1; under Sullivan's contempt warning over the Epstein files. Read <a href="#update">the dated record and corrections</a>.</dd>
    <dt>Kash Patel</dt><dd>FBI leadership and the investigations examined in <a href="#{curdoc}">the current documentation</a>.</dd>
    <dt>Russell Vought</dt><dd>OMB, Project 2025, and executive-branch personnel policy in <a href="#{curdoc}">the blueprint and machinery chapters</a>.</dd>
    <dt>Omeed Malik</dt><dd>1789 Capital and the financing connections identified in <a href="#{ideol}">the network chapter</a>.</dd>
    <dt>Chris Buskirk</dt><dd>1789 Capital and the network's organizing connections in <a href="#{ideol}">the network chapter</a>.</dd>
    <dt>Rebekah Mercer</dt><dd>1789 Capital and the financing references in <a href="#{ideol}">the network chapter</a>.</dd>
    <dt>David Sacks</dt><dd>The crypto-policy and investment references covered in <a href="#{money}">the money architecture</a> and <a href="#{ideol}">network chapter</a>.</dd>
    <dt>Justin Sun</dt><dd>Token purchases and regulatory proceedings documented in <a href="#{money}">the crypto ledger</a>.</dd>
    <dt>Changpeng Zhao</dt><dd>Binance, WLF-related transactions, and the pardon record. <a href="#{money}">The report distinguishes the documented sequence from alleged causation</a>.</dd>
    <dt>Sheikh Tahnoon bin Zayed Al Nahyan</dt><dd>The UAE-linked financing and MGX / USD1 transaction covered in <a href="#{money}">the foreign-state and crypto records</a>.</dd>
    <dt>Mohammed bin Salman</dt><dd>Saudi Arabia, PIF, and the sovereign-funding references in <a href="#{money}">the envoy economy</a>.</dd>
  </dl>
  <h5>Companies and vehicles</h5>
  <dl>
    <dt>World Liberty Financial (WLF / WLFI / USD1)</dt><dd>The family crypto venture: governance token (WLFI) and dollar-pegged stablecoin (USD1, ~$4B).</dd>
    <dt>DT Marks DEFI LLC</dt><dd>The Trump vehicle that WLF's own disclosures say receives 75% of token-sale proceeds [A].</dd>
    <dt>DT Marks SC LLC</dt><dd>A second Trump vehicle — named in OCC Corporate Decision #1385 as a passive indirect investor in the family's chartered trust bank [A].</dd>
    <dt>World Liberty Trust Company, N.A.</dt><dd>The national trust bank the OCC conditionally approved Aug 14, 2026. Zachary Witkoff, president and director.</dd>
    <dt>ALT5 Sigma = AI Financial Corp (AIFC)</dt><dd>One SEC registrant (CIK 862861), renamed April 2026 — WLFI's largest disclosed token holder, &minus;92.2% with going-concern doubt.</dd>
    <dt>TMTG / DJT (Truth Social)</dt><dd>The president's media company — whose API sells structured post feeds to ~10 customers, primarily high-frequency trading firms, per its interim CEO on the record.</dd>
  </dl>
</div>
</section>'''

rail_stops = [
 ("SEP 2","Missouri Supreme Court — referendum argument",""),
 ("SEP 3","Phang reply; FCC opposes Disney TRO",""),
 ("SEP 4","Slavin v. Parnell — TRO hearing on the Stripes firings",""),
 ("SEP 10","Ballot-rule restraining order expires",""),
 ("SEP 14","Congress returns — SAVE Act; war powers; S. 5300",""),
 ("SEP 15","CA4 argument: Comey / James dismissal appeals",""),
 ("SEP 24","US v. Harvard (Title VII) motion hearing",""),
 ("SEP 25","ICE Mega Hub — IDIQ awards due",""),
 ("SEP 29","D.C. Circuit en banc — Boasberg contempt inquiry",""),
 ("SEP 30","Camp East Montana contract ends",""),
 ("OCT 6","Disney v. FCC — TRO/PI hearing, Courtroom 21",""),
 ("OCT 21","Comey trial date, New Bern",""),
 ("OCT 28","Bolton sentencing, Greenbelt",""),
 ("NOV 3","THE MIDTERMS — the nearest test with a date","big"),
]
rail = ('<section id="dates"><div class="card rail-wrap"><h4>The nearest dates — this report tests itself on a calendar</h4><div class="rail">'
 + "".join(f'<div class="stop {b}"><a href="#u-threads"><div class="d">{d}</div><div class="w">{w}</div></a></div>' for d,w,b in rail_stops)
 + "</div></div></section>")

# ---------- shared navigation and reading chrome ----------
children = {}
cur = None
for tag, sid, text in toc:
    if tag == "h2":
        cur = sid
        children[cur] = []
    elif cur:
        children[cur].append((sid, text))
sb_story = ""
for sid, text in h2s:
    links = f'<a href="/#{sid}">Read this section</a>'
    links += "".join(f'<a href="/#{child}">{html.escape(label)}</a>'
                     for child, label in children.get(sid, []))
    sb_story += (f'<details data-part="{sid}"><summary>{html.escape(text)}</summary>'
                 f'<div>{links}</div></details>')
sidebar = f'''<div class="sb-label">Start here</div>
<a href="/#cover">The report</a><a href="/#howto">How to read this</a>
<a href="/#edition-notes">Edition notes</a>
<div class="sb-label">The record</div>
<a href="/#update">This week's record</a><a href="/#brief-001">Weekly briefs</a>
<a href="/#u-corrections">Corrections</a><a href="/#u-silence">Silence ledger</a>
<a href="/#u-threads">Next checks</a>
<div class="sb-label">The story</div>{sb_story}
<div class="sb-label">Reference</div>
<a href="/topics.html">Topics</a><a href="/synthesis.html">Synthesis</a>
<a href="/neural.html">Neural map</a><a href="/sources.html">Sources</a>'''


def topic_menu():
    """The registry supplies labels and routes; it never changes the authored report."""
    registry_path = ROOT / "research_registry.json"
    if not registry_path.exists():
        return '<a href="/topics.html">Browse all topics &rarr;</a>'
    registry = json.loads(registry_path.read_text())
    groups = []
    for category in registry.get("categories", []):
        topics = [t for t in registry.get("topics", [])
                  if category["id"] in t.get("categoryIds", [])]
        if not topics:
            continue
        links = "".join(f'<a href="/topics/{html.escape(t["id"], quote=True)}.html">'
                        f'{html.escape(t["title"])}</a>' for t in topics)
        groups.append(f'<div><h3>{html.escape(category["title"])}</h3>{links}</div>')
    return ('<div class="topic-menu-grid">' + "".join(groups) + '</div>'
            '<a class="browse-topics" href="/topics.html">Browse all topics &rarr;</a>')


def site_header(active="report"):
    def link(label, href, key):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{href}"{current}>{label}</a>'
    topics_current = ' class="nav-current"' if active == "topics" else ''
    return ('<a class="skip-link" href="#main-content">Skip to content</a>'
            '<div class="progress" id="progress" aria-hidden="true"></div>'
            '<header class="topnav" id="top"><a class="brand" href="/">THE ARCHITECTURE</a>'
            '<button class="menu-toggle" type="button" data-ui-menu aria-expanded="false" '
            'aria-controls="site-navigation"><span aria-hidden="true">☰</span> Menu</button>'
            '<nav class="navlinks" id="site-navigation" aria-label="Main navigation">'
            + link('Report', '/', 'report') + link('Weekly record', '/#update', 'record')
            + f'<div class="navgroup"><button{topics_current} type="button" data-ui-dropdown aria-expanded="false" '
            'aria-controls="topics-navigation">Topics <span aria-hidden="true">⌄</span></button>'
            '<div class="dd topics-menu" id="topics-navigation" hidden>' + topic_menu() + '</div></div>'
            + link('Synthesis', '/synthesis.html', 'synthesis')
            + link('Neural map', '/neural.html', 'neural') + link('Sources', '/sources.html', 'sources')
            + '<a class="search-link" href="/topics.html#topic-search" aria-label="Search topics">'
            '<svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true"><circle cx="10" cy="10" r="6.5" '
            'fill="none" stroke="currentColor" stroke-width="1.4"/><path d="m15 15 6 6" stroke="currentColor" '
            'stroke-width="1.4"/></svg></a></nav></header>')


def reading_controls(sidebar_html):
    return ('''<dialog class="contents-dialog" id="contents-dialog" aria-labelledby="contents-heading">
<div class="dialog-heading"><h2 id="contents-heading">Contents</h2>
<button type="button" data-ui-close-contents aria-label="Close contents">Close <span aria-hidden="true">×</span></button></div>
<nav class="contents-links sidebar-links" aria-label="Page contents">''' + sidebar_html + '''</nav></dialog>
<div class="reader-bar" role="region" aria-label="Reading controls">
<button type="button" data-ui-contents aria-controls="contents-dialog" aria-haspopup="dialog"><span aria-hidden="true">☰</span> Contents</button>
<span class="reader-current">Current section: <span id="whereami">Introduction</span></span>
<a class="reader-topics" href="/topics.html">Topics</a>
<button type="button" data-ui-save><svg viewBox="0 0 16 20" width="13" height="17" aria-hidden="true"><path d="M2 1h12v17l-6-4-6 4Z" fill="none" stroke="currentColor" stroke-width="1.2"/></svg> Save place</button>
<button type="button" data-ui-share aria-haspopup="dialog" aria-controls="share-dialog">Share</button>
<button type="button" data-ui-resume hidden>Resume reading</button>
<a class="reader-top" href="#top"><span aria-hidden="true">↑</span> Top</a>
<progress id="reading-progress" max="100" value="0" aria-label="Page reading progress"></progress>
</div><p class="reader-status" data-ui-status role="status" aria-live="polite"></p>
<dialog class="contents-dialog share-dialog" id="share-dialog" aria-labelledby="share-heading">
<div class="dialog-heading"><p id="share-heading">Share this record</p><button type="button" data-share-close aria-label="Close sharing">Close ×</button></div>
<div class="share-body"><p data-share-title></p><label for="share-url">Link to this page or section</label>
<input id="share-url" type="url" readonly spellcheck="false">
<div class="share-actions"><button type="button" data-share-copy>Copy link</button><button type="button" data-share-native hidden>Share via…</button></div>
<p data-share-status role="status" aria-live="polite"></p></div></dialog>
<dialog class="contents-dialog" id="print-dialog" aria-labelledby="print-heading">
<div class="dialog-heading"><p id="print-heading">Print-ready document</p><button type="button" data-print-close aria-label="Close print options">Close ×</button></div>
<div class="share-body"><p data-print-title></p><p>This PDF includes the complete page or entity record. Download it to print from your PDF app.</p>
<div class="print-actions"><a data-print-download download>Download PDF</a><a data-print-open>Open PDF</a></div>
<p data-print-status role="status" aria-live="polite"></p></div></dialog>''')

# ---------- assemble shared body ----------
update_html = reference_links((ROOT / "update_part2.html").read_text(), "update_part2.html")
update_html, navigation_inventory = link_silence_clocks(update_html,
    json.loads((ROOT / "report_reference_targets.json").read_text())["targets"],
    set(re.findall(r'\bid="([^"]+)"', body_html + update_html)))
neural_html = (ROOT / "neural_map.html").read_text()   # interactive map section (own <style>/<script>)

# ---------- weekly briefs: every briefs/YYYY-MM-DD.html is picked up automatically ----------
def brief_inner(raw):
    """Body of a brief, normalized for inlining. Accepts either an original brief source or a
    brief re-authored from built output (which already carries subpage(): a div.content wrapper
    and a back-link paragraph) — both must yield the same bare body."""
    inner = raw.split("<body>", 1)[1].rsplit("</body>", 1)[0] if "<body>" in raw else raw
    m = re.match(r'\s*<div class="content"[^>]*>(.*)</div>\s*\Z', inner, re.S)
    if m:
        inner = m.group(1)
    inner = re.sub(r'\A\s*<p class="mast-kicker"[^>]*>.*?</p>', '', inner, count=1, flags=re.S)
    return inner

briefs = []  # [(date_stem, inner_html)] oldest -> newest
for bp in sorted((ROOT / "briefs").glob("2*.html")):
    inner = reference_links(brief_inner(bp.read_text()), "briefs/" + bp.name)
    brief_seen = {}
    def brief_heading(match):
        tag, attrs, title = match.groups()
        if re.search(r'\bid\s*=', attrs):
            return match.group(0)
        label = html.unescape(re.sub(r"<[^>]+>", "", title))
        base = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", label).lower()).strip("-")[:60] or "section"
        number = brief_seen.get(base, 0)
        brief_seen[base] = number + 1
        ident = f"brief-{bp.stem}-{base}" + (f"-{number}" if number else "")
        return f'<{tag}{attrs} id="{ident}">{title}</{tag}>'
    inner = re.sub(r"<(h[234])([^>]*)>(.*?)</\1>", brief_heading, inner, flags=re.S)
    inner = inner.replace('<div class="mast-kicker"><a href="/">&larr; The Architecture — Main Report</a></div>',
                          '<div class="mast-kicker">Weekly Brief Archive</div>')
    inner = inner.replace('<a href="/">&larr; MAIN REPORT</a> &middot; ', '')
    inner = re.sub(r'href="/briefs/[^"]+\.html"', 'href="#brief-001"', inner)
    briefs.append((bp.stem, inner))
if not briefs:
    raise SystemExit("no briefs found in " + str(ROOT / "briefs"))
latest_brief = briefs[-1][0]
edition_no = f"{len(briefs):03d}"

items = ""
for n, (stem, inner) in reversed(list(enumerate(briefs, start=1))):
    items += (f'<details class="front-matter" id="brief-{stem}">'
              f'<summary>Weekly Brief {n:03d} &mdash; week ending {stem} (full narrative)</summary>'
              f'<div class="fm-body">{inner}</div></details>')
brief_section = ('<section id="brief-001"><h2><span class="num">ARCHIVE</span>Weekly Brief Archive</h2>'
                 f'<p>{len(briefs)} brief{"s" if len(briefs) != 1 else ""} on the record, newest first. '
                 'Each opens in full — lede, three architectures, rejects, sourcing notes.</p>'
                 + items + '</section>')
src_md = (ROOT / "sources_manifest.md").read_text()
# Keep the archived wording intact, but render it as readable prose instead of code.
source_archive_html = reference_links(markdown.markdown(src_md, extensions=["tables"]), "sources_manifest.md")
source_archive_html = re.sub(r"<h1>(.*?)</h1>", r'<p class="mast-kicker">\1</p>', source_archive_html, count=1, flags=re.S)
source_registry = json.loads((ROOT / "research_registry.json").read_text())
reviewed_sources = '<ul class="source-links">'
for source in source_registry.get("sources", []):
    reviewed_sources += (f'<li id="source-{html.escape(source["id"], quote=True)}">'
        f'<a href="{html.escape(source["url"], quote=True)}" rel="noopener noreferrer">'
        f'{html.escape(source["publisher"])}: {html.escape(source["title"])}</a>'
        f'<span class="topic-meta">{html.escape(source.get("publishedAt") or "Publication date not recorded")} '
        f'· reviewed {html.escape(source["accessedAt"])}</span>'
        + (f'<span class="topic-meta">Location: {html.escape(source["locator"])}</span>' if source.get("locator") else "") + '</li>')
reviewed_sources += '</ul>'
sources_section = ('<section id="sources"><h2><span class="num">REFERENCE</span>Source Archive Index (2026-07-19)</h2>'
                   '<p>Every sourced line in the master report, extracted for archiving — 200 entries. Weekly-update sourcing lives inline in the update sections and archived briefs.</p>'
                   '<details class="front-matter"><summary>Open the 200-entry source index</summary><div class="fm-body">'
                   + source_archive_html + "</div></details></section>")

cover = (f'<header class="cover" id="cover">{head_html}'
         f'<div class="mast-meta"><span>MASTER REPORT: CONSOLIDATED EDITION &middot; 2026-08-22</span><span>RESEARCH BEGUN 2025-12</span>'
         f'<span>EDITION UPDATE {edition_no} &middot; {latest_brief}</span><span>~{read_total//60} HR {read_total%60} MIN &middot; {len(h2s)} SECTIONS</span></div>'
         f'<details class="front-matter" id="edition-notes"><summary>Front matter — edition notes, table of contents, what this document is and is not</summary>'
         f'<div class="fm-body">{fm_html}</div></details></header>')

footer = f'''<footer class="site-footer">
<p>THE ARCHITECTURE is an investigative synthesis by Kirk Musick, carried forward by a standing tiered-evidence weekly process. It reports structure, not intent; separates private positions from government actions; labels dotted edges dotted; keeps denials attached to their allegations with exact scope; treats verified absence as a result; and logs corrections permanently.</p>
<p class="mono">MASTER REPORT: CONSOLIDATED EDITION (2026-08-22; research begun 2025-12) &middot; EDITION UPDATE {edition_no} ({latest_brief}) &middot; <a href="#brief-001">WEEKLY BRIEFS</a> &middot; <a href="#sources">SOURCE ARCHIVE</a> &middot; <a href="#u-corrections">CORRECTIONS</a></p>
</footer>'''

content = (cover + sentence + arch3 + howto + cast + rail + update_html
           + '<article class="story" id="report-story">' + body_html + "</article>" + brief_section + sources_section + footer)


css = (ROOT / "final.css").read_text()
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">')

TITLE = "The Architecture — Power, Money, and Ideology in the Second Trump Era"
DESC = ("An investigative synthesis of the second Trump era: the power architecture, the money architecture, "
        "and the ideology architecture — with a tiered-evidence weekly record, corrections log, and source archive.")

def render_page(title, body_inner, *, active="report", sidebar_html=None,
                description="", page_class=""):
    """Shared editorial shell for preserved report, briefs, map and research pages.

    body_inner is trusted generated HTML. sidebar_html is navigation HTML without IDs;
    it appears in the desktop rail and the keyboard-accessible contents dialog.
    Existing content, heading IDs and route shapes are not rewritten.
    """
    side = sidebar if sidebar_html is None else sidebar_html
    table_number = 0
    def wrap_table(match):
        nonlocal table_number
        table_number += 1
        return (f'<div class="table-scroll" role="region" aria-label="Table {table_number}" '
                f'tabindex="0">{match.group(0)}</div>')
    body_inner = re.sub(r'<table\b[^>]*>.*?</table>', wrap_table, body_inner, flags=re.S)
    body = (site_header(active) + '<div class="shell">'
            '<aside class="sidebar sidebar-links" aria-label="Section navigation">' + side + '</aside>'
            '<main class="content" id="main-content" tabindex="-1">' + body_inner + '</main></div>'
            + reading_controls(side) + '<script src="/site-ui.js" defer></script>')
    desc = html.escape(description or DESC, quote=True)
    return ('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">'''
            + f'<title>{html.escape(title)}</title><meta name="description" content="{desc}">'
            + f'<meta property="og:title" content="{html.escape(title, quote=True)}">'
            + f'<meta property="og:description" content="{desc}"><meta property="og:type" content="article">'
            + '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 fill=%22%238c2f1b%22/%3E%3Ctext x=%2216%22 y=%2224%22 text-anchor=%22middle%22 font-family=%22Georgia%22 font-size=%2225%22 fill=%22white%22%3EA%3C/text%3E%3C/svg%3E">'
            + FONTS + '<link rel="stylesheet" href="/styles.css"></head>'
            + f'<body class="{html.escape(page_class, quote=True)}">{body}</body></html>')

latest_record = (f'<a class="latest-record" href="/briefs/{latest_brief}.html">'
                 f'<span><span class="mast-kicker">Latest record · {latest_brief}</span>'
                 f'<strong>Weekly Brief {edition_no}</strong></span>'
                 f'<span class="latest-record-action">Read the brief <span aria-hidden="true">→</span></span></a>')
entry_links = (f'<div class="entry-links"><a href="#{execs}"><strong>Read the report</strong>'
               '<span>Start at the beginning →</span></a><a href="#update"><strong>Read this week</strong>'
               '<span>Latest record and analysis →</span></a><a href="/neural.html"><strong>Explore the map</strong>'
               '<span>People, money, institutions →</span></a></div>')
content = content.replace('</header>', '</header>' + latest_record + entry_links, 1)
site = render_page(TITLE, content, page_class="report-page")
(DIST / "index.html").write_text(site)
(DIST / "styles.css").write_text(css)
(DIST / "site-ui.js").write_text((ROOT / "site_ui.js").read_text())

# Standalone URLs retain the complete source body and use the same reading controls.
for stem, inner in briefs:
    (DIST / "briefs" / f"{stem}.html").write_text(render_page(
        f"Brief — week ending {stem} · The Architecture",
        '<p class="mast-kicker"><a href="/">&larr; The Architecture</a></p>'
        + inner.replace('href="#brief-001"', 'href="/#brief-001"'),
        active="record", page_class="brief-page"))
(DIST / "sources.html").write_text(render_page("Source Archive Index — The Architecture",
    '<p class="mast-kicker"><a href="/">&larr; The Architecture</a></p>'
    '<h1 class="mast">Sources</h1><p>Open the reviewed records, or read the preserved historical source index.</p>'
    + f'<section id="reviewed-sources"><h2>Reviewed source records</h2><p>{len(source_registry.get("sources", []))} records linked in the research views.</p>'
    + reviewed_sources + '</section><section id="historical-sources"><h2>Historical source archive</h2>'
    + '<p>The original index cites sources by name and date. Navigation wording is updated for this layout; the original wording remains in the download. '
    '<a href="/src/sources_manifest.md" download>Download the original index</a>.</p>'
    + '<div class="source-archive">' + source_archive_html + '</div></section>',
    active="sources", page_class="sources-page"))

# Content-only export keeps its CSS and reading behavior self-contained for publishers.
page_body = site.split('<body class="report-page">', 1)[1].rsplit('</body>', 1)[0]
page_body = page_body.replace('<script src="/site-ui.js" defer></script>',
                              '<script>' + (ROOT / "site_ui.js").read_text() + '</script>')
artifact = f"<title>The Architecture</title>\n{FONTS}\n<style>\n{css}\n</style>\n{page_body}"
(ROOT / "artifact.html").write_text(artifact)

# the neural map: its own full-width page, generated from src/neural_map.html;
# the SVG + dossier data are fetched assets so weekly updates swap two small files
import shutil
(DIST / "map").mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / "neural_svg.frag", DIST / "map" / "svg.frag")
shutil.copyfile(ROOT / "neural_data.json", DIST / "map" / "data.json")
import json as _json
_nd = _json.loads((ROOT / "neural_data.json").read_text())
_n_nodes, _n_edges = len(_nd["nodes"]), len(_nd["edges"])   # counts follow the data, never hand-typed
neural_html = re.sub(r'(<span id="nm-count">)[^<]*(</span>)',
                     lambda m: f'{m[1]}{_n_nodes} nodes · {_n_edges} edges{m[2]}', neural_html)
neural_html = re.sub(r'(<span id="nm-data-state">)[^<]*(</span>)',
                     lambda m: f'{m[1]}data state {html.escape(_nd["current"])}{m[2]}', neural_html)
(DIST / "neural.html").write_text(render_page(
    "The Neural Map — The Architecture", neural_html, active="neural", page_class="map-page",
    description=f"The Architecture's relationship map: {_n_nodes} nodes and {_n_edges} edges, graded by evidence."))

# The research builder owns its content and registry; this builder owns shared chrome.
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from build_research import build_research
research_urls = build_research(ROOT, DIST, render_page)
(DIST / "research" / "references.json").write_text(json.dumps(reference_inventory, ensure_ascii=False, indent=2) + "\n")
unresolved_references = [row for document in reference_inventory for row in document["unresolved"]]
if unresolved_references:
    raise SystemExit("Unresolved named report references: " + json.dumps(unresolved_references, ensure_ascii=False))
(DIST / "research" / "navigation.json").write_text(json.dumps(navigation_inventory, ensure_ascii=False, indent=2) + "\n")

# Production address of Vercel project `the-architecture` (team zincdigitalofmiamis-projects).
# the-architecture-liard.vercel.app is the project's former address and redirects here.
SITE_URL = os.environ.get("ARCH_SITE_URL", "https://the-architecture-neurals.vercel.app").rstrip("/")
(DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
urls = ["/", "/neural.html", "/sources.html"] + research_urls + [f"/briefs/{s}.html" for s, _ in reversed(briefs)]
(DIST / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"<url><loc>{SITE_URL}{u}</loc><lastmod>{latest_brief}</lastmod></url>\n" for u in urls)
    + "</urlset>\n")

for p in sorted(DIST.rglob("*")):
    if p.is_file(): print(f"{p.relative_to(DIST)}  {p.stat().st_size:,} B")
print("artifact.html ", (ROOT/'artifact.html').stat().st_size, "B")
print("sections:", len(h2s), "| toc:", len(toc), "| total read ~", read_total, "min")

# ---- v3.2: self-hosted sources (weekly runs fetch src from the live site) ----
import shutil as _sh
_srcdst = DIST / "src"
if _srcdst.exists():
    _sh.rmtree(_srcdst)
_srcdst.mkdir()
for _f in ["master_report.md", "sources_manifest.md", "update_part2.html", "final.css", "WEEKLY_RUN.md",
           "build_site3.py", "site_ui.js", "build_research.py", "research_registry.json",
           "research_registry.py", "research_ui.js", "report_references.py", "report_navigation.py", "report_reference_targets.json", "neural_map.html", "neural_data.json", "neural_svg.frag",
           "build_neural_map.py", "build_neural_map.js", "map_source.json", "mapgen.js", "brief_lint.py"]:
    _sp = ROOT / _f
    if _sp.exists():
        _sh.copy(_sp, _srcdst / _f)
(_srcdst / "agents").mkdir(exist_ok=True)
for _a in sorted((ROOT / "agents").glob("*.md")):
    _sh.copy(_a, _srcdst / "agents" / _a.name)
(_srcdst / "briefs").mkdir(exist_ok=True)
for _b in (ROOT / "briefs").glob("*.html"):
    _sh.copy(_b, _srcdst / "briefs" / _b.name)
for _root_f in ["AGENT_INSTRUCTIONS.md", "AUTOMATED_RUN_TASK.md", "check.sh", "deploy.sh", "pull_src.sh"]:
    _rp = ROOT.parent / _root_f
    if _rp.exists():
        _sh.copy(_rp, _srcdst / _root_f)
_rb = DIST / "robots.txt"
_rt = _rb.read_text()
if "Disallow: /src/" not in _rt:
    _rb.write_text(_rt.replace("Allow: /", "Allow: /\nDisallow: /src/"))

# MANIFEST.json: static hosting has no directory listing, so the weekly run fetches this
# first, then every listed path, and checks each SHA-256 before trusting the working copy.
import hashlib as _hl, json as _mj
_entries = sorted(p for p in _srcdst.rglob("*") if p.is_file())
_manifest = {
    "site": SITE_URL,
    "vercel_project": "the-architecture",
    "vercel_team": "zincdigitalofmiamis-projects",
    "current_through": latest_brief,
    "master_edition": "2026-08-22",
    "counts": {   # monotonic guards in check.sh compare these against the previous week's manifest
        "agents": len(list((ROOT / "agents").glob("*.md"))),
        "briefs": len(briefs),
        "corrections": len(re.findall(r'&middot; C-0\d\d', update_html)),
        "clocks": update_html.count('class="clock"'),
        "map_nodes": _n_nodes, "map_edges": _n_edges,
        "index_bytes": (DIST / "index.html").stat().st_size,
    },
    "files": [{"path": str(p.relative_to(_srcdst)).replace("\\", "/"),
               "bytes": p.stat().st_size,
               "sha256": _hl.sha256(p.read_bytes()).hexdigest()} for p in _entries],
}
(_srcdst / "MANIFEST.json").write_text(_mj.dumps(_manifest, indent=1) + "\n")
print("self-hosted sources: site/src populated;", len(_entries), "files listed in MANIFEST.json; robots updated")
