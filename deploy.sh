#!/usr/bin/env bash
# Preview by default; --prod publishes only the artifact committed on LIVE GitHub main.
# Build and review BEFORE the commit. No arbitrary preview promotion or source sync.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
exec python3 "$ROOT/scripts/release.py" "$@"
