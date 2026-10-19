"""conftest.py - make src/ importable for tests without installing the package.

NOTE: harmless when the package IS installed (sys.path dedup by Python);
this is the belt-and-suspenders so `pytest -q` always works on a fresh clone.
"""
import pathlib
import sys

SRC = pathlib.Path(__file__).parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
