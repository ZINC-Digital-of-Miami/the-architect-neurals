#!/usr/bin/env bash
# Acquire the exact live GitHub main in a NEW directory. Never overwrite a draft.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
exec python3 "$ROOT/scripts/repository.py" "${1:?usage: ./pull_src.sh NEW_DIRECTORY}"
