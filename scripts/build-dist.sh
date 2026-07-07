#!/usr/bin/env bash
# Build compiled dist/ for Databricks Apps (Cython, Ubuntu 22.04, Python 3.11).
#
# Usage (Git Bash / Linux / macOS), from repo root:
#   bash scripts/build-dist.sh
#
# Requires: Docker

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Git Bash on Windows converts -w /src → C:/Program Files/Git/src — disable that.
if [[ "${MSYSTEM:-}" == MINGW* || "${MSYSTEM:-}" == MSYS* ]]; then
  export MSYS_NO_PATHCONV=1
fi

# Docker Desktop on Windows needs a Windows-style host path for -v.
docker_src_volume() {
  local dir="$1"
  if (cd "$dir" && pwd -W) &>/dev/null; then
    (cd "$dir" && pwd -W) | sed 's|\\|/|g'
  else
    printf '%s' "$dir"
  fi
}

VOL="$(docker_src_volume "$ROOT")"

echo "==> Building compiled dist/ (Cython)"
echo "    mount: ${VOL} -> /src"

docker run --rm \
  -v "${VOL}:/src" \
  -w /src \
  ubuntu:22.04 \
  bash -c "sed -i 's/\r$//' /src/scripts/build-dist-inner.sh && bash /src/scripts/build-dist-inner.sh"

echo ""
echo "==> dist/ ready. Deploy with:"
echo "    databricks sync ./dist /Workspace/Users/<you>/finops-app"
