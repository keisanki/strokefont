"""
strokefont -- TRIUMF / Physica "vaxfont.dat" stroke fonts for matplotlib.

Quick start
-----------
    import strokefont as sf
    sf.set_font_file("vaxfont.dat")            # or set env var TRIUMF_FONTS=<dir with vaxfont.dat>

    # 1. one object, matplotlib-style (mathtext subset: $...$, ^, _, \\alpha, \\frac, \\sqrt ...)
    ax.add_artist(sf.StrokeText(.5, .5, r"decay $e^{-t/\\tau}$", fontsize=14,
                                transform=ax.transAxes, ha="center"))

    # 2. everything, including ticks, labels, titles and legends created afterwards
    with sf.use("TRIUMF.2"):
        fig, ax = plt.subplots(); ax.plot(...); ax.legend(); fig.savefig("x.pdf")
    #    ... or sf.install("TRIUMF.2") / sf.uninstall()

    # 3. convert text objects that already exist
    sf.stroke_texts(fig, "ROMAN.2")

    # 4. original PSYM control-character syntax ("legacy" markup)
    sf.StrokeText(0, 0, "x" + sf.UP + "2" + sf.DOWN + "y", markup="legacy")

The font file format and the script/letter-spacing rules follow the TRIUMF sources PFONT.F and
PSYM.F (R. Lee 1981/1988, F. W. Jones, J. Chuma); see README.md.
"""

from ._font import FONT_NAMES, PFont, get_font, get_font_file, set_font_file
from ._install import install, stroke_texts, uninstall, use
from ._symbols import (
    BACKSPACE,
    DOWN,
    DOWNSIZE,
    SYMBOLS,
    UP,
    UPSIZE,
    _code_for,
    code_for,
)
from ._text import StrokeText

__version__ = "0.1.0"

__all__ = [
    "BACKSPACE",
    "DOWN",
    "DOWNSIZE",
    "FONT_NAMES",
    "PFont",
    "SYMBOLS",
    "StrokeText",
    "UP",
    "UPSIZE",
    "__version__",
    "code_for",
    "get_font",
    "get_font_file",
    "install",
    "set_font_file",
    "stroke_texts",
    "uninstall",
    "use",
]
