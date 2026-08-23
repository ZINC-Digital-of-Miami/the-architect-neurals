#!/usr/bin/env bash
# THE ARCHITECTURE — pre-deploy guards only (no network, no Vercel). Run from the package root.
# Exit 0 = site/ is safe to upload. Any other exit = do not deploy.
set -euo pipefail
cd "$(dirname "$0")"
fail() { echo "FAIL: $*" >&2; exit 1; }

test -s site/index.html                                   || fail "site/index.html missing"
[ "$(wc -c < site/index.html | tr -d " ")" -gt 350000 ]           || fail "site/index.html under 350 KB — report body missing"
for id in u-corrections u-silence u-threads brief-001 sources; do
  grep -q "id=\"$id\"" site/index.html                    || fail "missing #$id in index.html"
done
grep -q '\$1,269,843' site/index.html                     || fail "C-002 ExodusPoint figure (\$1,269,843) missing — a correction was reverted"
grep -q 'after discussion with The Nasdaq' site/index.html || fail "C-001 observer language missing"
# consolidated edition (2026-08-22): corrections C-005..C-008, the eleven new chapters, both appendices
for c in C-005 C-006 C-007 C-008; do
  grep -q "$c" site/index.html                             || fail "correction $c missing — a correction was reverted"
done
for id in chapter-0-b chapter-c-2 chapter-e-2 chapter-e-3 chapter-g-2 chapter-h-the-warehouse chapter-m chapter-21-n chapter-21-o chapter-21-p chapter-21-q appendix-a appendix-b; do
  grep -q "id=\"$id" site/index.html                      || fail "missing #$id — consolidated-edition chapter dropped"
done
[ "$(grep -c 'class="clock"' site/index.html)" -ge 9 ]    || fail "silence ledger has fewer than 9 clocks — a clock was dropped"
# map prose must match map data (neural_map.html counts are hand-typed)
NN=$(python3 -c "import json;d=json.load(open('site/map/data.json'));print(len(d['nodes']))")
NE=$(python3 -c "import json;d=json.load(open('site/map/data.json'));print(len(d['edges']))")
grep -q "$NN nodes · $NE edges" site/neural.html          || fail "neural.html says a different node/edge count than map/data.json ($NN/$NE)"
grep -q "data state $(python3 -c "import json;print(json.load(open('site/map/data.json'))['current'])")" site/neural.html || fail "neural.html data-state date differs from map/data.json"
test -s site/neural.html && test -s site/map/svg.frag && test -s site/map/data.json || fail "neural map assets missing"
test -s site/src/MANIFEST.json                            || fail "site/src/MANIFEST.json missing — rebuild with build_site3.py v3.2+"
grep -q 'Disallow: /src/' site/robots.txt                 || fail "robots.txt does not disallow /src/"
grep -q 'the-architecture-neurals.vercel.app' site/sitemap.xml || fail "sitemap.xml does not carry the live address"
[ "$(grep -c 'class="content"' site/index.html)" -le 1 ]  || fail "nested div.content — a brief was ingested without unwrapping"
! grep -q '>&larr; The Architecture<' site/index.html     || fail "stray back-link inside the inlined brief archive"
# every brief in src/ must have a built page and a sitemap entry
for b in src/briefs/[0-9]*.html; do
  s=$(basename "$b" .html)
  test -s "site/briefs/$s.html"                           || fail "built brief page missing for $s"
  grep -q "/briefs/$s.html" site/sitemap.xml              || fail "sitemap missing /briefs/$s.html"
done
# ---- every brief must pass the linter (shape = Brief 001; voice floor; no undefined classes) ----
python3 src/brief_lint.py --css src/final.css src/briefs/2*.html        || fail "a brief failed brief_lint.py — fix the brief, never the linter"
# ---- page hygiene: no duplicate ids, no dead in-page anchors, no template residue ----
python3 - <<'PY' || fail "page hygiene"
import re,sys,collections
h=open("site/index.html").read()
ids=re.findall(r' id="([^"]+)"',h); dup=[k for k,v in collections.Counter(ids).items() if v>1]
if dup: print("duplicate ids:",dup[:10]); sys.exit(1)
hrefs=set(re.findall(r'href="#([^"]+)"',h)); dead=sorted(hrefs-set(ids))
if dead: print("dead in-page anchors:",dead[:10]); sys.exit(1)
for ph in ["YYYY-MM-DD","{{SUNDAY}}","{{SITE}}","Edition NNN","EDITION NNN","The topic lead."]:
    if ph in h: print("template residue in index:",ph); sys.exit(1)
PY
# ---- the look is frozen: final.css may change only when this pin is updated by hand ----
FINAL_CSS_SHA=$(shasum -a 256 src/final.css | cut -c1-16)
[ "$FINAL_CSS_SHA" = "2ef00da80bbd84f4" ]                    || fail "src/final.css changed (sha $FINAL_CSS_SHA) — the look is settled; if this is deliberate, update 2ef00da80bbd84f4 in check.sh"
# ---- the ENTIRE design is locked (owner, 2026-08-22): map-page CSS, the site shell generator, the brief template ----
python3 - <<'PY' || fail "design surface changed — the look is settled; if deliberate, update the three DESIGN pins in check.sh"
import re,hashlib,pathlib
sha=lambda t: hashlib.sha256(t.encode()).hexdigest()[:16]
nm=pathlib.Path("src/neural_map.html").read_text(); st=re.search(r"<style>.*?</style>",nm,re.S).group(0)
b=pathlib.Path("src/build_site3.py").read_text(); shell=re.sub(r"rail_stops = \[.*?\n\]\n","rail_stops = [...]\n",b,flags=re.S)
tp=pathlib.Path("src/briefs/_TEMPLATE.html").read_text()
bad=[]
if sha(st)!="9ff6113991fe4c1c": bad.append(f"neural_map.html <style> (now {sha(st)}, pinned 9ff6113991fe4c1c)")
if sha(shell)!="293b2a68a5f22070": bad.append(f"build_site3.py outside rail_stops (now {sha(shell)}, pinned 293b2a68a5f22070)")
if sha(tp)!="91e3ef93168f0864": bad.append(f"_TEMPLATE.html (now {sha(tp)}, pinned 91e3ef93168f0864)")
if bad: print("DESIGN PIN MISMATCH: "+"; ".join(bad)); raise SystemExit(1)
PY
# ---- monotonic guards vs the previous week's pulled manifest (present only inside a work/ pull) ----
if [ -s MANIFEST.json ]; then
python3 - <<'PY' || fail "monotonic guard"
import json,sys
prev=json.load(open("MANIFEST.json")); cur=json.load(open("site/src/MANIFEST.json"))
pc=prev.get("counts",{}); cc=cur["counts"]
def need(k,op,why):
    a,b=pc.get(k),cc.get(k)
    if a is None: return
    ok={"ge":b>=a,"eq1":b in(a,a+1),"gt":b>a}[op]
    if not ok: print(f"{k}: previous {a}, now {b} — {why}"); sys.exit(1)
need("corrections","ge","a correction was dropped (append-only)")
need("clocks","ge","a silence clock was dropped (advance or resolve, never delete)")
need("briefs","eq1","briefs must grow by exactly one per week")
need("map_nodes","ge","a map node was dropped without a ruling")
if cur["current_through"] <= prev["current_through"]: print("current_through did not advance"); sys.exit(1)
if cc["index_bytes"] > pc.get("index_bytes",0)+120000: print("index grew >120 KB in one week — something was inlined that should not be"); sys.exit(1)
PY
fi
echo "OK: $(ls site/briefs/[0-9]*.html | wc -l) brief(s); index $(wc -c < site/index.html | tr -d " ") B; current through $(python3 -c "import json;print(json.load(open('site/src/MANIFEST.json'))['current_through'])")"
