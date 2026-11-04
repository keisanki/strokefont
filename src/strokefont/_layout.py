"""Glyph layout, line breaking and the legacy PSYM state machine."""

import functools

import numpy as np
from matplotlib.path import Path

from ._markup import _compile_line
from ._symbols import BACKSPACE, DOWN, DOWNSIZE, UP, UPSIZE, _code_for


# --------------------------------------------------------------------------- layout
class _Layout:
    """Accumulates stroke geometry.  Units: cap height of the base size == 1."""

    def __init__(self, font):
        self.f = font
        self.u = 1.0 / font.cap_height                    # grid unit -> cap-height units
        self.tan = np.tan(np.radians(font.angl))
        self.V, self.C = [], []
        self.right = 0.0                                  # right-most ink/advance edge

    # grid-unit offset (a, b) at scale s -> cap units, including the font's slant
    def mv(self, a, b, s):
        f = self.f
        return f.scal * self.u * s * (a + self.tan * b), self.u * s * b

    def put(self, code, x, y, s):
        f = self.f
        w, v, c = f.glyph(code)
        if len(v):
            gx, gy = v[:, 0] - f.refx, v[:, 1] - f.refy
            self.V.append(np.column_stack([x + f.scal * (gx + self.tan * gy) * self.u * s,
                                           y + gy * self.u * s]))
            self.C.append(c)
        # PSYM.F: WIDTHH = HSPAC+GRID, or LSPAC+WIDTH when letterspacing is on
        adv = (w + f.lspac) if f.letterspacing else (f.grid + f.hspac)
        xn = x + f.scal * adv * self.u * s
        gap = f.scal * (f.lspac + f.refx) * self.u * s if f.letterspacing else 0.0
        self.right = max(self.right, xn - gap)
        return xn

    def add(self, verts, codes, dx, dy):
        if len(verts):
            self.V.append(verts + [dx, dy])
            self.C.append(codes)
            self.right = max(self.right, float(verts[:, 0].max() + dx))

    def result(self):
        if self.V:
            return np.vstack(self.V), np.concatenate(self.C), self.right
        return np.zeros((0, 2)), np.zeros(0, np.uint8), self.right

    def sub(self, nodes, s):
        """lay out nodes in a fresh layout at scale s, origin (0,0): (verts, codes, width)"""
        lay = _Layout(self.f)
        x = lay.emit(nodes, 0.0, 0.0, s)
        v, c, w = lay.result()
        return v, c, max(x, w)

    # ---- sub/superscript placement, exactly as PSYM.F: the script's grid origin goes to the
    # PSUP/PSUB point of the preceding character's grid.
    def enter(self, kind, s):
        f = self.f
        ref = f.psup if kind == 'sup' else f.psub
        dx1, dy1 = self.mv(ref[0] - f.refx, ref[1] - f.refy, s)
        dx2, dy2 = self.mv(f.refx, f.refy, s * f.shgt)
        return dx1 + dx2, dy1 + dy2

    def emit(self, nodes, x, y, s):
        f = self.f
        for n in nodes:
            t = n[0]
            if t == 'c':
                x = self.put(n[1], x, y, s)
            elif t == 'g':
                x = self.emit(n[1], x, y, s)
            elif t == 'sp':
                x += n[1] * s
            elif t == 'script':
                _, kind, node, other = n
                ends = []
                for k, nd in ((kind, node), ('sub' if kind == 'sup' else 'sup', other)):
                    if nd is None:
                        continue
                    dx, dy = self.enter(k, s)
                    ends.append(self.emit([nd], x + dx, y + dy, s * f.shgt) - dx)
                x = max(ends)
            elif t == 'frac':
                fs = 0.75 * s
                vn, cn, wn = self.sub([n[1]], fs)
                vd, cd, wd = self.sub([n[2]], fs)
                W = max(wn, wd) + 0.2 * s
                bar = 0.45 * s
                self.add(vn, cn, x + (W - wn) / 2, y + bar + 0.24 * s)
                self.add(vd, cd, x + (W - wd) / 2, y + bar - 0.24 * s - 0.75 * s)
                self.add(np.array([[0.04 * s, bar], [W - 0.04 * s, bar]]),
                         np.array([Path.MOVETO, Path.LINETO], np.uint8), x, y)
                x += W + 0.06 * s
            elif t == 'sqrt':
                v, c, w = self.sub([n[1]], s)
                top = max(1.0 * s, float(v[:, 1].max()) if len(v) else 0.0) + 0.18 * s
                bar_end = 0.66 * s + w + 0.08 * s
                pts = np.array([[0, .40 * s], [.10 * s, .46 * s], [.30 * s, -.06 * s],
                                [.56 * s, top], [bar_end, top]])
                self.add(pts, np.array([Path.MOVETO] + [Path.LINETO] * 4, np.uint8), x, y)
                self.add(v, c, x + 0.66 * s, y)
                x += bar_end + 0.04 * s
        return x


def _legacy_line(font, text):
    """Original PSYM control-character state machine (PSYM.F), ported literally."""
    f = font
    lay = _Layout(f)
    x = y = 0.0
    s = 1.0
    levels = levelv = 0
    dsup = (f.psup[0] - f.refx, f.psup[1] - f.refy)
    dsub = (f.psub[0] - f.refx, f.psub[1] - f.refy)
    ref = (f.refx, f.refy)

    def mv(p, sign=1):
        nonlocal x, y
        dx, dy = lay.mv(p[0], p[1], s)
        x += sign * dx
        y += sign * dy

    def scale(fac):
        nonlocal s
        s *= fac

    for ch in text:
        if ch == UP:
            levels += 1
            if levels < 0:
                mv(f.psub, -1)
            elif levels == 0:
                mv(ref, -1); scale(1 / f.shgt); mv(dsub, -1)
            else:
                mv(dsup)
                if levels == 1:
                    scale(f.shgt)
                mv(ref)
        elif ch == DOWN:
            levels -= 1
            if levels < 0:
                mv(dsub)
                if levels == -1:
                    scale(f.shgt)
                mv(ref)
            elif levels == 0:
                mv(ref, -1); scale(1 / f.shgt); mv(dsup, -1)
            else:
                mv(f.psup, -1)
        elif ch == UPSIZE:
            levelv += 1
            if levelv <= 0:
                mv(ref, -1); scale(1 / f.shgt); mv(dsub, -1)
            else:
                mv(dsup); scale(f.shgt); mv(ref)
        elif ch == DOWNSIZE:
            levelv -= 1
            if levelv < 0:
                mv(dsub); scale(f.shgt); mv(ref)
            else:
                mv(ref, -1); scale(1 / f.shgt); mv(dsup, -1)
        elif ch == BACKSPACE:
            x -= f.scal * (f.grid + f.hspac) * lay.u * s
        elif ord(ch) >= 32:
            x = lay.put(_code_for(ch), x, y, s)
    return lay.result()


@functools.lru_cache(maxsize=4096)
def _line_geometry(font, line, markup, parse_math):
    """(verts, codes, width) of one line, base cap height == 1 (cached)."""
    if markup == 'legacy':
        return _legacy_line(font, line)
    lay = _Layout(font)
    lay.emit(_compile_line(line, markup, parse_math), 0.0, 0.0, 1.0)
    return lay.result()


def clear_cache():
    """Drop cached line geometry (called after the font library changes)."""
    _line_geometry.cache_clear()
