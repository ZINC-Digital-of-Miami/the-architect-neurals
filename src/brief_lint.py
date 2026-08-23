#!/usr/bin/env python3
"""THE ARCHITECTURE — brief linter. Called by check.sh for every src/briefs/2*.html.

Enforces the canonical brief shape (Brief 001, 2026-08-16) and the voice floor from
WEEKLY_RUN.md §B. Exit 0 = the brief may be built. Any other exit = do not build; fix the
brief. Every failure names the rule and the evidence. No network, no dependencies.

Usage:  python3 src/brief_lint.py src/briefs/2026-08-23.html [more briefs...]
        python3 src/brief_lint.py --css src/final.css src/briefs/*.html
"""
import html as _html, pathlib, re, sys

REQUIRED_H2 = [
    "The lede",
    "Architecture I — The family money",
    "Architecture II — Executive power",
    "Architecture III — The wars and the count",
    "The node where the architectures touch",
    "What would change the tier",
    "Rejected below [B], with reasons",
    "Next week's priorities",
]
FORBIDDEN_TAGS = ["h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "style", "script", "iframe", "img", "link"]
EXTRA_CLASSES_OK = {"wrap", "content"}          # carried by Brief 001's reconstruction; harmless
PLACEHOLDERS = [
    "YYYY-MM-DD", "MONTH D", "Edition NNN", "EDITION NNN", "The topic lead.",
    "Vertex 1", "{{", "}}", "TODO", "TBD", "lorem", "[FILL",
]
# Voice floor — phrases the corpus never uses; their presence is a tell, not a style nit.
BANNED_PHRASES = [
    "it is worth noting", "it's worth noting", "worth noting that", "underscores", "underscore the",
    "in conclusion", "a stark reminder", "raises questions", "raises serious questions",
    "sends a message", "sends a clear message", "at the end of the day", "delve", "delves",
    "tapestry", "landscape of", "a testament to", "game-changer", "game changer",
    "it remains to be seen", "only time will tell", "the bottom line", "bottom line:",
    "in today's", "in an era of", "navigating", "unpack", "double down", "doubled down",
    "shocking", "bombshell", "explosive", "slammed", "blasted", "ripped",
]
MIN_WORDS, MAX_WORDS = 2500, 6500
MIN_P_PER_ARCH, MAX_P_LEN_WORDS = 2, 320
MIN_TIER_CHIPS = 20

def fail(msgs, brief):
    print(f"BRIEF LINT FAIL: {brief}")
    for m in msgs: print(f"  - {m}")

def lint(path: pathlib.Path, css_classes: set) -> list:
    raw = path.read_text(encoding="utf-8")
    body = raw.split("<body>", 1)[1].rsplit("</body>", 1)[0] if "<body>" in raw else raw
    m = re.match(r'\s*<div class="content"[^>]*>(.*)</div>\s*\Z', body, re.S)
    if m: body = m.group(1)
    errs = []

    # 1. structure: the eight h2s, in order, nothing else at h2 level
    h2s = [_html.unescape(re.sub(r"<[^>]+>", "", t)).strip() for t in re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S)]
    norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'").replace("—", "—")).strip()
    if [norm(h) for h in h2s] != [norm(h) for h in REQUIRED_H2]:
        errs.append(f"h2 headings must be exactly, in order: {REQUIRED_H2}\n      found: {h2s}")
    if not re.search(r'<h1 class="mast"', body): errs.append('missing <h1 class="mast">')
    if not re.search(r'<section class="lede">', body): errs.append('missing <section class="lede"> around The lede')
    if len(re.findall(r"<section\b", body)) < 8: errs.append("fewer than 8 <section> blocks — each h2 lives in its own <section>")

    # 2. forbidden tags / inline style
    for t in FORBIDDEN_TAGS:
        n = len(re.findall(rf"<{t}\b", body, re.I))
        if n: errs.append(f"forbidden tag <{t}> used {n}x (briefs are prose: sections, paragraphs, tier chips)")
    # the build's subpage() wrapper adds style= to div.content / p.mast-kicker / h1.mast when a brief is
    # reconstructed from built output (Brief 001). Anything else with style= is a hand-styled element.
    styled = [t for t in re.findall(r"<([a-z0-9]+)[^>]*\sstyle=\"", body)]
    styled_bad = [t for t in styled if t not in ("div", "p", "h1")]
    if styled_bad or len(styled) > 3:
        errs.append(f"inline style attributes on {styled} — the look lives in final.css only")

    # 3. classes must exist in final.css
    used = {c for grp in re.findall(r'class="([^"]+)"', body) for c in grp.split()}
    unknown = sorted(used - css_classes - EXTRA_CLASSES_OK)
    if unknown: errs.append(f"classes not defined in final.css: {unknown}")

    # 4. placeholders / template residue
    for p in PLACEHOLDERS:
        if p in body: errs.append(f"template placeholder left in brief: {p!r}")

    # 5. words, paragraphs, tier chips
    text = _html.unescape(re.sub(r"<[^>]+>", " ", body)); words = text.split()
    if not (MIN_WORDS <= len(words) <= MAX_WORDS): errs.append(f"word count {len(words)} outside {MIN_WORDS}–{MAX_WORDS}")
    paras = re.findall(r"<p(?![^>]*class=\"(?:mast|mono)[^\"]*\")[^>]*>(.*?)</p>", body, re.S)
    long_ps = [i for i, p in enumerate(paras) if len(re.sub(r"<[^>]+>", " ", p).split()) > MAX_P_LEN_WORDS]
    if long_ps: errs.append(f"{len(long_ps)} paragraph(s) over {MAX_P_LEN_WORDS} words (indices {long_ps[:5]}) — split them; the reader needs air")
    sections = re.findall(r"<section[^>]*>(.*?)</section>", body, re.S)
    for sec in sections:
        h = re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.S)
        if h and "Architecture" in h.group(1):
            n = len(re.findall(r"<p\b", sec))
            if n < MIN_P_PER_ARCH: errs.append(f"'{re.sub(r'<[^>]+>','',h.group(1))}' has {n} paragraph(s); minimum {MIN_P_PER_ARCH}")
    chips = len(re.findall(r'class="tier (?:a|b|c|abs)"', body))
    if chips < MIN_TIER_CHIPS: errs.append(f"only {chips} tier chips; a sourced brief carries at least {MIN_TIER_CHIPS}")
    if 'class="tier abs"' not in body and "ABSENT" not in text:
        errs.append("no verified absence — neither an ABSENT chip nor the word ABSENT appears; a brief that checked for nothing found nothing")
    if 'class="tier c"' not in body: errs.append("no [C] rejection — a week with nothing rejected did not look")

    # 6. voice floor
    low = text.lower()
    hits = sorted({b for b in BANNED_PHRASES if b in low})
    if hits: errs.append(f"banned phrases (the corpus never uses these): {hits}")
    q = len(re.findall(r"\?\s", text))
    if q > 2: errs.append(f"{q} question marks — rhetorical questions are not this report's voice (max 2)")
    leads = len(re.findall(r"<p>\s*<strong>[^<]{3,60}\.</strong>", body))
    if leads < 6: errs.append(f"only {leads} bolded topic leads (<p><strong>Two to four words.</strong>); Brief 001 pattern needs ≥6")
    return errs

def main(argv):
    css_path = None; briefs = []
    it = iter(argv)
    for a in it:
        if a == "--css": css_path = pathlib.Path(next(it))
        else: briefs.append(pathlib.Path(a))
    if css_path is None:
        here = pathlib.Path(__file__).resolve().parent
        css_path = here / "final.css"
    css_classes = set(re.findall(r"\.([A-Za-z_][\w-]*)", css_path.read_text(encoding="utf-8")))
    bad = 0
    for b in briefs:
        if b.name.startswith("_"): continue
        errs = lint(b, css_classes)
        if errs: bad += 1; fail(errs, b)
        else: print(f"brief lint OK: {b}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
