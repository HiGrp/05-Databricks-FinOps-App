#!/usr/bin/env bash
# Build dist/ (Cython, Ubuntu 22.04 / Python 3.11). Usage: bash build.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# --- run inside Docker container ---
if [[ "${1:-}" == "--in-docker" ]]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -qq -y python3.11 python3.11-dev python3-pip gcc rsync > /dev/null
  python3.11 -m pip install -q --upgrade pip cython setuptools wheel

  rm -rf dist && mkdir -p dist
  rsync -a \
    --exclude '.git' --exclude '.venv' --exclude 'venv' --exclude 'dist' --exclude 'build' \
    --exclude 'tools' --exclude 'dev_data' --exclude '__pycache__' --exclude '.gitignore' \
    --exclude '*.pyc' --exclude '*.c' --exclude '*.so' --exclude 'README.md' --exclude 'metadata' \
    ./ dist/

  cat > dist/setup_cython.py << 'PY'
from pathlib import Path
import glob
from Cython.Build import cythonize
from setuptools import Extension, setup

ROOT = Path(__file__).resolve().parent
extensions = []
for rel in ("licensing.py", "app_config.py", "prod_data.py"):
    extensions.append(Extension(rel[:-3].replace("/", "."), [str(ROOT / rel)]))
for path in sorted(glob.glob(str(ROOT / "dashboards" / "*.py"))):
    if Path(path).name == "__init__.py":
        continue
    extensions.append(Extension("dashboards." + Path(path).stem, [path]))
setup(ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}, quiet=False))
PY

  cd dist
  python3.11 setup_cython.py build_ext --inplace
  rm -f setup_cython.py licensing.py app_config.py prod_data.py
  find dashboards -name '*.py' ! -name '__init__.py' -delete
  find . -name '*.c' -delete && rm -rf build
  touch .dist_build
  printf '[app]\ndev_mode = false\n' > config.toml
  printf '__pycache__/\n*.pyc\n' > .gitignore
  cp /src/license_public_key.txt . 2>/dev/null || true

  SO_COUNT=$(find . -name '*.so' | wc -l)
  [[ "$SO_COUNT" -ge 5 ]] || { echo "ERROR: missing .so ($SO_COUNT)"; exit 1; }
  python3.11 -m pip install -q cryptography
  python3.11 -c "import licensing; print('OK')"
  echo "Build complete."
  exit 0
fi

# --- host (Git Bash / Linux) ---
if [[ "${MSYSTEM:-}" == MINGW* || "${MSYSTEM:-}" == MSYS* ]]; then
  export MSYS_NO_PATHCONV=1
fi
VOL="$ROOT"
if (cd "$ROOT" && pwd -W) &>/dev/null; then
  VOL="$(cd "$ROOT" && pwd -W | sed 's|\\|/|g')"
fi

echo "==> build dist/ (Docker)"
docker run --rm -v "${VOL}:/src" -w /src ubuntu:22.04 \
  bash -c "sed -i 's/\r$//' /src/build.sh && bash /src/build.sh --in-docker"

git add -f dist/ .gitignore dist/.gitignore 2>/dev/null || true
echo "==> done. dist/ staged. Commit + push, then client runs:"
echo "    databricks sync ./dist /Workspace/Users/<client>/finops-app"
