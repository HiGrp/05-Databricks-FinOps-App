"""Build Cython extensions for distribution (run inside Docker Linux build)."""

from __future__ import annotations

import glob
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup

ROOT = Path(__file__).resolve().parent

# Streamlit entry point + cache wrappers — must stay plain Python.
KEEP_PY = {"app.py", "streamlit_caches.py"}

# Packages / modules compiled to .so (IP + license logic).
COMPILE_ROOT = [
    "licensing.py",
    "app_config.py",
    "prod_data.py",
]

extensions: list[Extension] = []

for rel in COMPILE_ROOT:
    mod = rel.replace(".py", "").replace("/", ".")
    extensions.append(Extension(mod, [str(ROOT / rel)]))

for path in sorted(glob.glob(str(ROOT / "dashboards" / "*.py"))):
    name = Path(path).name
    if name == "__init__.py":
        continue
    mod = "dashboards." + name[:-3]
    extensions.append(Extension(mod, [path]))

setup(
    name="finops-optimizer-dist",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
        quiet=False,
    ),
)
