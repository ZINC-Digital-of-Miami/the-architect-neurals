#!/usr/bin/env python3
"""v3.1: white, large-type, full-width shell with sidebar + top menu, orientation layer,
part openers, clocks, node diagram.

Reads sources from this script's directory (src/): master_report.md, update_part2.html,
sources_manifest.md, final.css, briefs/*.html.
Emits ../site/ (index.html + styles.css + sources.html + briefs/*.html + robots.txt + sitemap.xml)
plus artifact.html (same body, no document wrapper) for publishers that wrap content themselves.

Weekly: drop the new briefs/YYYY-MM-DD.html and rewrite update_part2.html, then re-run.
Brief numbering, the edition number, the masthead date, the archive, the per-brief pages,
and the sitemap all follow from the briefs/ directory automatically."""
import re, html, pathlib, unicodedata, os
import markdown

# Portable paths. Sources live beside this script; output goes to ../site (the Vercel deploy dir).
# Override with ARCH_ROOT / ARCH_DIST if you keep a different layout.
ROOT = pathlib.Path(os.environ.get("ARCH_ROOT") or pathlib.Path(__file__).resolve().parent)
DIST = pathlib.Path(os.environ.get("ARCH_DIST") or (ROOT.parent / "site"))
(DIST / "briefs").mkdir(parents=True, exist_ok=True)

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
          f'<span class="rt">~{mins} min read</span><span class="top"><a href="#top">contents &uarr;</a></span></div>'
          f'<h2 id="{sid}">{inner}</h2>' + (f'<p class="dek">{dek}</p>' if dek else "") + "</header>")
    else:
        out.append(chunk)
body_html = "".join(out)
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
    <a href="#the-sentence"><span class="pm">~10 MIN</span><span class="pt">The ten-minute read</span>
      <span class="pd">The sentence &rarr; <a href="#{execs}">executive summary</a> &rarr; <a href="#u-week">this week's lede</a> &rarr; <a href="#u-node">the node</a> &rarr; <a href="#{concl}">the conclusion</a>.</span></a>
    <a href="#{money}"><span class="pm">~50 MIN</span><span class="pt">The evidence spine</span>
      <span class="pd">The <a href="#{money}">money architecture</a> &rarr; <a href="#{curdoc}">current documentation</a> &rarr; <a href="#u-corrections">corrections</a> &rarr; <a href="#u-silence">the silence ledger</a>.</span></a>
    <a href="#{execs}"><span class="pm">~{read_total//60} HR {read_total%60} MIN</span><span class="pt">The full synthesis</span>
      <span class="pd">Cover to conclusion in order, the <a href="#{hist}">historical lens</a> in full, honest assessment included.</span></a>
  </div>
</div>
</section>'''

cast = '''
<section id="cast">
<div class="card cast">
  <h4>The cast, briefly — people and vehicles this report keeps distinct</h4>
  <dl>
    <dt>World Liberty Financial (WLF / WLFI / USD1)</dt><dd>The family crypto venture: governance token (WLFI) and dollar-pegged stablecoin (USD1, ~$4B).</dd>
    <dt>DT Marks DEFI LLC</dt><dd>The Trump vehicle that WLF's own disclosures say receives 75% of token-sale proceeds [A].</dd>
    <dt>DT Marks SC LLC</dt><dd>A second Trump vehicle — named in OCC Corporate Decision #1385 as a passive indirect investor in the family's chartered trust bank [A].</dd>
    <dt>World Liberty Trust Company, N.A.</dt><dd>The national trust bank the OCC conditionally approved Aug 14, 2026. Zachary Witkoff, president and director.</dd>
    <dt>ALT5 Sigma = AI Financial Corp (AIFC)</dt><dd>One SEC registrant (CIK 862861), renamed April 2026 — WLFI's largest disclosed token holder, &minus;92.2% with going-concern doubt.</dd>
    <dt>Zach Witkoff &middot; Steve Witkoff</dt><dd>Son: WLF CEO, trust-bank president, ALT5 chairman. Father: special envoy whose OGE disclosure remains uncertified ~12 months on.</dd>
    <dt>Eric Trump &middot; Donald Trump Jr.</dt><dd>Eric: American Bitcoin; ALT5 <em>observer</em>, never seated as director (corrected at [A]). Don Jr.: 1789 Capital; Polymarket adviser.</dd>
    <dt>Jared Kushner</dt><dd>Affinity Partners — Gulf sovereign money; the envoy economy's other pole.</dd>
    <dt>TMTG / DJT (Truth Social)</dt><dd>The president's media company — whose API sells structured post feeds to ~10 customers, primarily high-frequency trading firms, per its interim CEO on the record.</dd>
    <dt>Todd Blanche</dt><dd>The president's former defense lawyer; confirmed Attorney General Aug 8, 2026, 50&ndash;49&ndash;1; under Sullivan's contempt warning over the Epstein files.</dd>
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

# ---------- nav + sidebar ----------
story_menu = "".join(f'<a href="#{sid}">{html.escape(t)}</a>' for sid, t in h2s)
menu = f'''<div class="progress" id="progress"></div>
<nav class="topnav" id="top">
  <a class="brand" href="#top">THE&nbsp;ARCHITECTURE</a>
  <span class="whereami" id="whereami"></span>
  <div class="navlinks">
    <div class="navgroup"><button type="button">Start ▾</button><div class="dd">
      <a href="#the-sentence">The Sentence</a><a href="#arch">The Three Architectures</a>
      <a href="#howto">How to Read &middot; Three Ways In</a><a href="#cast">The Cast, Briefly</a>
      <a href="#dates">The Nearest Dates</a></div></div>
    <div class="navgroup"><button type="button">Updates ▾</button><div class="dd">
      <a href="#update">The Record Since July 19</a><a href="#u-gap">The Gap — Jul 19 &rarr; Aug 9</a>
      <a href="#u-week">The Week — Aug 9&ndash;16</a><a href="#u-node">The Node</a>
      <a href="#u-corrections">Corrections Log</a><a href="#u-silence">The Silence Ledger</a>
      <a href="#u-threads">Open Threads &middot; Next Checks</a><a href="#brief-001">Weekly Brief Archive</a></div></div>
    <a class="nav-flag" href="/neural.html">Neural Map</a>
    <div class="navgroup"><button type="button">The Story ▾</button><div class="dd">{story_menu}</div></div>
    <a href="#sources">Sources</a>
  </div>
</nav>'''

# sidebar with h3 children
children = {}
cur = None
for tag, sid, t in toc:
    if tag == "h2": cur = sid; children[cur] = []
    elif cur: children[cur].append((sid, t))
sb_story = ""
for sid, t in h2s:
    kids = children.get(sid, [])
    inner = "".join(f'<a href="#{k}">{html.escape(kt)}</a>' for k, kt in kids)
    sb_story += (f'<details data-part="{sid}"><summary><a href="#{sid}" style="all:unset;cursor:pointer">{html.escape(t)}</a></summary>'
                 + (f"<div>{inner}</div>" if inner else "") + "</details>")
sidebar = f'''<aside class="sidebar" aria-label="Section navigation">
  <div class="sb-label">Orient</div>
  <a href="#the-sentence">The Sentence</a><a href="#arch">Three Architectures</a>
  <a href="#howto">How to Read</a><a href="#cast">The Cast</a><a href="#dates">The Nearest Dates</a>
  <div class="sb-label">The Record</div>
  <a href="#update">Since July 19</a><a href="#u-gap">— The Gap</a><a href="#u-week">— The Week</a>
  <a href="#u-node">— The Node</a><a href="#u-corrections">— Corrections</a>
  <a href="#u-silence">— Silence Ledger</a><a href="#u-threads">— Next Checks</a>
  <a class="sb-flag" href="/neural.html">The Neural Map &rarr;</a>
  <div class="sb-label">The Story</div>
  {sb_story}
  <div class="sb-label">Reference</div>
  <a href="#brief-001">Weekly Briefs</a><a href="#sources">Source Archive</a>
</aside>'''

JS = '''<script>
document.querySelectorAll('.navgroup > button').forEach(function(b){
  b.addEventListener('click', function(e){ e.stopPropagation();
    var g=b.parentElement, open=g.classList.contains('open');
    document.querySelectorAll('.navgroup.open').forEach(function(x){x.classList.remove('open')});
    if(!open) g.classList.add('open'); });});
document.addEventListener('click', function(){
  document.querySelectorAll('.navgroup.open').forEach(function(x){x.classList.remove('open')});});
var bar=document.getElementById('progress');
addEventListener('scroll', function(){
  var h=document.documentElement, p=h.scrollTop/(h.scrollHeight-h.clientHeight);
  bar.style.width=(p*100).toFixed(2)+'%';}, {passive:true});
var where=document.getElementById('whereami');
var targets=[].slice.call(document.querySelectorAll('section[id], h2[id], h3[id], h4[id]'));
var sbLinks={}; [].slice.call(document.querySelectorAll('.sidebar a[href^="#"]')).forEach(function(a){
  sbLinks[a.getAttribute('href').slice(1)]=a;});
var sbParts={}; [].slice.call(document.querySelectorAll('.sidebar details[data-part]')).forEach(function(d){
  sbParts[d.getAttribute('data-part')]=d;});
function label(el){var t=el.tagName==='SECTION'?(el.querySelector('h2,h4')||el):el;return (t.textContent||'').trim().slice(0,60);}
var current=null;
var io=new IntersectionObserver(function(es){
  es.forEach(function(e){ if(e.isIntersecting){ current=e.target;
    if(where) where.textContent='You are in: '+label(current);
    var id=current.id;
    document.querySelectorAll('.sidebar a.on').forEach(function(x){x.classList.remove('on')});
    document.querySelectorAll('.sidebar details.on').forEach(function(x){x.classList.remove('on')});
    if(sbLinks[id]) sbLinks[id].classList.add('on');
    var el=current;
    while(el && el!==document.body){
      if(el.id && sbParts[el.id]){sbParts[el.id].classList.add('on');sbParts[el.id].open=true;break;} el=el.parentElement;}
    if(sbParts[id]){sbParts[id].classList.add('on');sbParts[id].open=true;}
    var h2p=current.closest && current.closest('header.part-open');
    var pd=null, node=current;
    if(current.tagName==='H3'){ var prev=current; while(prev && !(prev.tagName==='H2'&&prev.id)){prev=prev.previousElementSibling||prev.parentElement;}
      if(prev&&prev.id&&sbParts[prev.id]){sbParts[prev.id].classList.add('on');sbParts[prev.id].open=true;}}
  }});},{rootMargin:'-35% 0px -55% 0px'});
targets.forEach(function(t){io.observe(t)});
</script>'''

# ---------- assemble shared body ----------
update_html = (ROOT / "update_part2.html").read_text()
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
    inner = brief_inner(bp.read_text())
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
sources_section = ('<section id="sources"><h2><span class="num">REFERENCE</span>Source Archive Index (2026-07-19)</h2>'
                   '<p>Every sourced line in the master report, extracted for archiving — 200 entries. Weekly-update sourcing lives inline in the update sections and archived briefs.</p>'
                   '<details class="front-matter"><summary>Open the 200-entry source index</summary><div class="fm-body">'
                   '<pre class="manifest">' + html.escape(src_md) + "</pre></div></details></section>")

cover = (f'<header class="cover" id="cover">{head_html}'
         f'<div class="mast-meta"><span>MASTER REPORT: CONSOLIDATED EDITION &middot; 2026-08-22</span><span>RESEARCH BEGUN 2025-12</span>'
         f'<span>EDITION UPDATE {edition_no} &middot; {latest_brief}</span><span>~{read_total//60} HR {read_total%60} MIN &middot; {len(h2s)} SECTIONS</span></div>'
         f'<details class="front-matter"><summary>Front matter — edition notes, table of contents, what this document is and is not</summary>'
         f'<div class="fm-body">{fm_html}</div></details></header>')

footer = f'''<footer class="site-footer">
<p>THE ARCHITECTURE is an investigative synthesis by Kirk Musick, carried forward by a standing tiered-evidence weekly process. It reports structure, not intent; separates private positions from government actions; labels dotted edges dotted; keeps denials attached to their allegations with exact scope; treats verified absence as a result; and logs corrections permanently.</p>
<p class="mono">MASTER REPORT: CONSOLIDATED EDITION (2026-08-22; research begun 2025-12) &middot; EDITION UPDATE {edition_no} ({latest_brief}) &middot; <a href="#brief-001">WEEKLY BRIEFS</a> &middot; <a href="#sources">SOURCE ARCHIVE</a> &middot; <a href="#u-corrections">CORRECTIONS</a></p>
</footer>'''

content = (cover + sentence + arch3 + howto + cast + rail + update_html
           + '<main class="story">' + body_html + "</main>" + brief_section + sources_section + footer)
page_body = menu + '<div class="shell">' + sidebar + '<div class="content">' + content + "</div></div>" + JS

css = (ROOT / "final.css").read_text()
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">')

TITLE = "The Architecture — Power, Money, and Ideology in the Second Trump Era"
DESC = ("An investigative synthesis of the second Trump era: the power architecture, the money architecture, "
        "and the ideology architecture — with a tiered-evidence weekly record, corrections log, and source archive.")

site = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">
<title>{html.escape(TITLE)}</title>
<meta name="description" content="{html.escape(DESC)}">
<meta property="og:title" content="{html.escape(TITLE)}"><meta property="og:description" content="{html.escape(DESC)}">
<meta property="og:type" content="article">
{FONTS}<style>
{css}</style>
</head>
<body>
{page_body}
</body>
</html>'''
(DIST / "index.html").write_text(site)
(DIST / "styles.css").write_text(css)

# standalone brief + sources pages for direct URLs (site build)
def subpage(title, body_inner):
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="index,follow">'
            f'<title>{html.escape(title)}</title>{FONTS}<link rel="stylesheet" href="/styles.css"></head>'
            f'<body><div class="content" style="max-width:1200px;margin:0 auto">{body_inner}</div></body></html>')
for stem, inner in briefs:
    (DIST / "briefs" / f"{stem}.html").write_text(subpage(
        f"Brief — week ending {stem} · The Architecture",
        '<p class="mast-kicker" style="margin-top:2rem"><a href="/">&larr; The Architecture</a></p>'
        + inner.replace('href="#brief-001"', 'href="/#brief-001"')))
(DIST / "sources.html").write_text(subpage("Source Archive Index — The Architecture",
    '<p class="mast-kicker" style="margin-top:2rem"><a href="/">&larr; The Architecture</a></p>'
    '<h1 class="mast">Source Archive Index</h1><pre class="manifest">' + html.escape(src_md) + "</pre>"))

# artifact: content-only (publisher wraps)
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
NEURAL_NAV = ('<nav class="topnav" id="top">'
  '<a class="brand" href="/">THE&nbsp;ARCHITECTURE</a><div class="navlinks">'
  '<a href="/">&larr; Main report</a><a href="/#update">The Record</a>'
  '<a class="nav-flag" href="/neural.html" aria-current="page">Neural Map</a>'
  '<a href="/sources.html">Sources</a></div></nav>')
(DIST / "neural.html").write_text(
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<meta name="robots" content="index,follow">'
    '<title>The Neural Map \u2014 The Architecture</title>'
    f'<meta name="description" content="The Architecture\u2019s neural map: {_n_nodes} nodes and {_n_edges} edges of power, '
    'money and ideology in the second Trump era, every edge graded by evidence.">'
    f'{FONTS}<link rel="stylesheet" href="styles.css"></head><body>{NEURAL_NAV}'
    '<div class="content" style="max-width:1700px;margin:0 auto;padding:0 clamp(1rem,3vw,2.5rem) 5rem">'
    f'{neural_html}</div></body></html>')

# Production address of Vercel project `the-architecture` (team zincdigitalofmiamis-projects).
# the-architecture-liard.vercel.app is the project's former address and redirects here.
SITE_URL = os.environ.get("ARCH_SITE_URL", "https://the-architecture-neurals.vercel.app").rstrip("/")
(DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
urls = ["/", "/neural.html", "/sources.html"] + [f"/briefs/{s}.html" for s, _ in reversed(briefs)]
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
           "build_site3.py", "neural_map.html", "neural_data.json", "neural_svg.frag",
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
