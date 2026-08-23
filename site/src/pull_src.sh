#!/usr/bin/env bash
# THE ARCHITECTURE — pull the working copy for a weekly run.
#   ./pull_src.sh <workdir>
# Source of truth = the NEWEST READY deployment of the project (preview or production), so a
# week that was previewed but not yet promoted is never lost. Falls back to the live alias.
# Needs VERCEL_TOKEN for the deployment lookup; without it, uses the live alias only.
set -euo pipefail
WORK=${1:?workdir}; mkdir -p "$WORK/src"
TEAM=zincdigitalofmiamis-projects; PROJECT=the-architecture
LIVE=${ARCH_LIVE:-https://the-architecture-neurals.vercel.app}
SRC_BASE=""; DEPLOYMENT=""

if [ -n "${VERCEL_TOKEN:-}" ] && command -v vercel >/dev/null; then
  DEPLOYMENT=$(vercel ls "$PROJECT" --scope "$TEAM" --status READY --format json --token "$VERCEL_TOKEN" 2>/dev/null \
    | python3 -c '
import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
deps=d.get("deployments",d if isinstance(d,list) else [])
def ts(x): return x.get("created") or x.get("createdAt") or 0
deps=[x for x in deps if str(x.get("state",x.get("status","READY"))).upper()=="READY"]
deps.sort(key=ts,reverse=True)
if deps:
    u=deps[0].get("url",""); print(u if u.startswith("http") else ("https://"+u if u else ""))
' || true)
fi

fetch() {  # fetch <path> <outfile>
  if [ -n "$DEPLOYMENT" ]; then
    vercel curl "$1" --deployment "$DEPLOYMENT" --scope "$TEAM" --yes --token "$VERCEL_TOKEN" > "$2" 2>/dev/null \
      || curl -sf "$DEPLOYMENT$1" -o "$2"
  else
    curl -sf "$LIVE$1" -o "$2"
  fi
}

echo "source deployment: ${DEPLOYMENT:-$LIVE (live alias)}"
fetch /src/MANIFEST.json "$WORK/MANIFEST.json" || { echo "FAIL: /src/MANIFEST.json unreachable — deploy the v3.2 package first" >&2; exit 1; }
python3 - "$WORK" <<'PY'
import json,sys,pathlib
w=pathlib.Path(sys.argv[1]); m=json.loads((w/'MANIFEST.json').read_text())
print("current_through:", m["current_through"], "| files:", len(m["files"]))
(w/'files.txt').write_text("\n".join(f["path"]+" "+f["sha256"] for f in m["files"])+"\n")
PY
ROOT_FILES="AGENT_INSTRUCTIONS.md AUTOMATED_RUN_TASK.md check.sh deploy.sh pull_src.sh"
while read -r path sha; do
  case " $ROOT_FILES " in *" $path "*) out="$WORK/$path" ;; *) out="$WORK/src/$path" ;; esac
  mkdir -p "$(dirname "$out")"
  fetch "/src/$path" "$out" || { echo "FAIL: could not fetch /src/$path" >&2; exit 1; }
  got=$(sha256sum "$out" | cut -d' ' -f1)
  [ "$got" = "$sha" ] || { echo "FAIL: hash mismatch on $path" >&2; exit 1; }
done < "$WORK/files.txt"
chmod +x "$WORK"/*.sh 2>/dev/null || true
echo "OK: working copy verified in $WORK ($(wc -l < "$WORK/files.txt") files)"
