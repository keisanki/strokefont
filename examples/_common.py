"""Shared setup for the example scripts.

Run the examples from a source checkout with ``python examples/demo.py`` after installing the
package, or directly from the checkout (the ``src`` directory is added to ``sys.path`` as a
fallback).  Output images go to ``docs/images``.
"""

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"

try:
    import strokefont as sf
except ModuleNotFoundError:  # running straight from a source checkout
    sys.path.insert(0, str(ROOT / "src"))
    import strokefont as sf


def setup():
    """Select a font library and return the strokefont module."""
    for key in ("VAXFONT", "TRIUMF_FONTS"):
        value = os.environ.get(key)
        if value:
            path = Path(value)
            if path.is_dir():
                path = path / "vaxfont.dat"
            if path.is_file():
                sf.set_font_file(path)
                return sf
    for path in (ROOT / "src" / "strokefont" / "data" / "vaxfont.dat",
                 ROOT / "fonts" / "vaxfont.dat", ROOT / "vaxfont.dat"):
        if path.is_file():
            sf.set_font_file(path)
            return sf
    return sf


def save(fig, name, **kwargs):
    """Save a figure in the documentation image directory."""
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / name, **kwargs)
