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
echo "OK: $(ls site/briefs/[0-9]*.html | wc -l) brief(s); index $(wc -c < site/index.html | tr -d " ") B; current through $(python3 -c "import json;print(json.load(open('site/src/MANIFEST.json'))['current_through'])")"
