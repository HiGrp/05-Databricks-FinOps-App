#!/usr/bin/env bash
# Inner build — Cython compile for Databricks Apps (Ubuntu 22.04 + Python 3.11).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -qq -y \
  python3.11 python3.11-dev python3.11-venv python3-pip \
  gcc ca-certificates file rsync > /dev/null

echo "Python in build container:"
python3.11 --version

python3.11 -m pip install -q --upgrade pip
python3.11 -m pip install -q cython setuptools wheel

# Clean previous outputs
rm -rf dist
mkdir -p dist

# Stage source (no dev tooling, no fake-data engine)
rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude 'dist' \
  --exclude 'build' \
  --exclude 'tools' \
  --exclude 'dev_data' \
  --exclude 'scripts' \
  --exclude 'docs' \
  --exclude '__pycache__' \
  --exclude '.gitignore' \
  --exclude '.pyarmor' \
  --exclude 'pyarmor.bug.log' \
  --exclude '*.pyc' \
  --exclude '*.c' \
  --exclude '*.so' \
  --exclude 'setup_cython.py' \
  --exclude 'README.md' \
  --exclude 'metadata' \
  ./ dist/

cp setup_cython.py dist/

echo "==> Compiling extensions (Cython)..."
cd dist
python3.11 setup_cython.py build_ext --inplace
rm -f setup_cython.py

# Remove plain Python sources that were compiled (keep app.py, streamlit_caches.py, __init__.py)
rm -f licensing.py app_config.py prod_data.py
find dashboards -name '*.py' ! -name '__init__.py' -delete
find . -name '*.c' -delete
rm -rf build

# Distribution marker — locks license enforcement in app_config.so
touch .dist_build

# Keep dist/ git-friendly (do not copy repo-root .gitignore)
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
EOF

# Minimal runtime config (no license/dev bypass knobs)
cat > config.toml << 'EOF'
[app]
dev_mode = false
EOF

# Optional public key file (also embedded in licensing.so)
if [ -f /src/license_public_key.txt ]; then
  cp /src/license_public_key.txt .
fi

echo "==> Compiled modules:"
find . -name '*.so' | head -40
SO_COUNT=$(find . -name '*.so' | wc -l)
if [ "$SO_COUNT" -lt 5 ]; then
  echo "ERROR: expected multiple .so files, found $SO_COUNT"
  exit 1
fi

echo "Smoke-test: import compiled licensing"
python3.11 -m pip install -q cryptography
python3.11 -c "import licensing; print('licensing OK')"

echo "Build complete — dist/ ready for Databricks Apps."
