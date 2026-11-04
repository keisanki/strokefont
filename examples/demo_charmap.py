"""Write a PDF character map of every font in vaxfont.dat, one page per font.

    python examples/demo_charmap.py [vaxfont.dat] [charmap.pdf]

Each page is a 16x16 table indexed by character code (row = high hex digit, column = low hex
digit).  Cells show the glyph; the small label top-left is the hex code, bottom-right the
ASCII character or \\name that strokefont maps to that slot (only meaningful for the
Latin/TRIUMF-style fonts; other fonts reuse the slots for their own glyphs).  Grey cells have
no glyph.
"""

import os
import sys
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

from _common import ROOT, plt, sf, setup

fontfile = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("VAXFONT")
outfile = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs" / "charmap.pdf"

if fontfile:
    path = Path(fontfile)
    if path.is_dir():
        path = path / "vaxfont.dat"
    sf.set_font_file(path)
else:
    setup()

# reverse map: code -> label (ASCII character, or \name for Greek / math slots)
LABELS = {}
for name, code in sf.SYMBOLS.items():
    LABELS.setdefault(code, '\\' + name)
for o in range(33, 127):
    LABELS[sf.code_for(chr(o))] = chr(o)          # ASCII wins over symbol names


def draw_page(pdf, font):
    fig = plt.figure(figsize=(8.27, 11.69))        # A4 portrait
    ax = fig.add_axes([0.07, 0.04, 0.90, 0.86])
    ax.set_xlim(-0.6, 16)
    ax.set_ylim(16, -0.6)                          # row 0 at top
    ax.axis('off')
    fig.text(0.07, 0.955, font.name, fontsize=18, weight='bold')
    nglyph = len(font.defined)
    fig.text(0.07, 0.93, f"grid {font.grid}x{font.grid}   {nglyph} glyphs   "
             f"letterspacing {'on' if font.letterspacing else 'off'}   "
             f"ref ({font.refx},{font.refy})   shear {font.angl:g} deg",
             fontsize=9, color='0.35')

    # common cell box in glyph units, so glyphs are comparable within a page
    allv = [font.glyph(c)[1] for c in font.defined if len(font.glyph(c)[1])]
    if allv:
        v = np.vstack(allv)
        xmax = max(font.glyph(c)[0] for c in font.defined)
        x0, x1 = 0.0, max(float(xmax), float(v[:, 0].max()))
        y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    else:
        x0, x1, y0, y1 = 0, font.grid, 0, font.grid
    pad = 0.06 * max(x1 - x0, y1 - y0)
    x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
    inner = 0.80                                    # fraction of the cell used by the glyph box
    sc = inner / max(x1 - x0, y1 - y0)

    for i in range(16):
        ax.text(i + 0.5, -0.3, f"{i:X}", ha='center', va='center', fontsize=8, color='0.35')
        ax.text(-0.3, i + 0.5, f"{i:X}", ha='center', va='center', fontsize=8, color='0.35')

    patches, grey = [], []
    for r in range(16):
        for c in range(16):
            code = r * 16 + c
            cell = Rectangle((c, r), 1, 1)
            if code not in font.defined:
                grey.append(cell)
                continue
            w, v, codes = font.glyph(code)
            if len(v):
                # glyph box centred in cell; y flipped because the axis is inverted
                px = c + 0.5 + (v[:, 0] - (x0 + x1) / 2) * sc
                py = r + 0.5 - (v[:, 1] - (y0 + y1) / 2) * sc
                patches.append(PathPatch(Path(np.column_stack([px, py]), codes), fill=False))
            ax.text(c + 0.05, r + 0.04, f"{code:02X}", fontsize=4.5, color='0.45', va='top')
            label = LABELS.get(code)
            if label:
                ax.text(c + 0.95, r + 0.97, label, fontsize=4.5, color='tab:blue',
                        ha='right', va='bottom')
    ax.add_collection(PatchCollection(grey, facecolor='0.93', edgecolor='none'))
    ax.add_collection(PatchCollection(
        patches, match_original=False, facecolor='none', edgecolor='k', linewidth=0.7,
        capstyle='round', joinstyle='round'))
    for k in range(17):
        ax.plot([0, 16], [k, k], color='0.8', lw=0.4)
        ax.plot([k, k], [0, 16], color='0.8', lw=0.4)
    pdf.savefig(fig)
    plt.close(fig)


outfile.parent.mkdir(parents=True, exist_ok=True)
with PdfPages(outfile) as pdf:
    for i, name in enumerate(sf.FONT_NAMES):
        draw_page(pdf, sf.get_font(name))
        print(f"{i + 1:2d}/{len(sf.FONT_NAMES)} {name}")
print("wrote", outfile)
