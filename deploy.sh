#!/usr/bin/env bash
# THE ARCHITECTURE — build + guard + link + deploy. Run from the package root.
#   ./deploy.sh                      build, check, PREVIEW deployment (prints its URL)     ← default
#   ./deploy.sh --prod               build, check, PRODUCTION deployment (goes live)
#   ./deploy.sh --promote <url|id>   promote an existing (reviewed) preview to production
#   --no-build                       skip the rebuild (site/ already current)
# Vercel project: the-architecture · team: zincdigitalofmiamis-projects · no Git repository
# Live: https://the-architecture-neurals.vercel.app/  (the-architecture-liard.vercel.app redirects here)
# Set VERCEL_TOKEN for non-interactive use; without it the CLI prompts for login once.
set -euo pipefail
cd "$(dirname "$0")"
TEAM=zincdigitalofmiamis-projects
PROJECT=the-architecture
TOK=${VERCEL_TOKEN:+--token "$VERCEL_TOKEN"}

MODE=preview; BUILD=yes; PROMOTE_TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-build) BUILD=no ;;
    --prod) MODE=prod ;;
    --preview) MODE=preview ;;
    --promote) MODE=promote; PROMOTE_TARGET="${2:?--promote needs a deployment url or id}"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done

if [ "$MODE" = promote ]; then
  # Promotes the reviewed preview as-is; nothing is rebuilt or re-uploaded.
  vercel promote "$PROMOTE_TARGET" --scope "$TEAM" --yes $TOK
  echo "promoted — verify https://the-architecture-neurals.vercel.app/"
  exit 0
fi

if [ "$BUILD" = yes ]; then
  python3 -m pip install --quiet markdown
  python3 src/build_site3.py            # rewrites site/ from src/
fi
./check.sh                              # all pre-deploy guards live in check.sh

# The deploy folder is named `site`, not `the-architecture`; an unlinked folder plus --yes
# would auto-link by folder name. Link explicitly to the real project first.
if [ ! -f site/.vercel/project.json ]; then
  ( cd site && vercel link --team "$TEAM" --project "$PROJECT" --yes $TOK )
fi

if [ "$MODE" = prod ]; then
  ( cd site && vercel deploy --prod --yes $TOK )
  echo "deployed to production — verify https://the-architecture-neurals.vercel.app/"
else
  RAW=$( cd site && vercel deploy --yes $TOK )          # bare URL, or JSON when the CLI detects an agent
  URL=$(printf '%s' "$RAW" | python3 -c 'import sys,json;t=sys.stdin.read().strip();print(json.loads(t)["deployment"]["url"] if t.startswith("{") else t)')
  echo "PREVIEW_URL=$URL"
  echo "review it, then launch with:  ./deploy.sh --promote $URL"
  echo "(or Vercel dashboard → the-architecture → Deployments → ⋯ → Promote to Production)"
fi
