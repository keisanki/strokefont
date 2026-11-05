"""Reading and caching the binary ``vaxfont.dat`` font library."""

import copy
import os
import struct

import numpy as np
from matplotlib.path import Path

FONT_NAMES = [
    'STANDARD', 'HELVETICA.1', 'GOTHIC.ENGLISH', 'ROMAN.3', 'ITALIC.3', 'GREEK.2A',
    'ITALIC.2A', 'ROMAN.2A', 'SANSERIF.2', 'GREEK.1', 'SANSERIF.1', 'SCRIPT.1',
    'GOTHIC.FRAKTUR', 'GOTHIC.ITALIAN', 'SCRIPT.2', 'ROMAN.2', 'ITALIC.2', 'GREEK.2',
    'CYRILLIC.2', 'SANSERIF.CART', 'GREEK.CART', 'HIRAGANA', 'KATAKANA', 'KANJI1',
    'KANJI2', 'KANJI3', 'KANJI4', 'KANJI5', 'OLDALPH', 'TRIUMF.1', 'TRIUMF.2', 'TSAN',
    'ROMAN.FUTURA', 'ROMAN.SERIF', 'ROMAN.FASHON', 'ROMAN.LOGO1', 'ROMAN.SWISSL',
    'ROMAN.SWISSM', 'ROMAN.SWISSB', 'SPECIAL', 'MATH', 'HEBREW', 'TRIUMF.OUTLINE']
"""Names of the 43 fonts in ``vaxfont.dat``, in library order."""

_RECLEN = 24000          # one font = two 12000-byte direct-access records
_FONT_FILE = None
_cache = {}
_pcache = {}


# --------------------------------------------------------------------------- font file
def set_font_file(path):
    """Select the binary font library to read.

    Parameters
    ----------
    path : str or os.PathLike
        Path to ``vaxfont.dat``.

    Notes
    -----
    All cached fonts and cached line geometry are discarded.  The path is not checked until a
    font is loaded with :func:`get_font`.
    """
    global _FONT_FILE
    _FONT_FILE = os.fspath(path)
    _cache.clear()
    _pcache.clear()
    from ._layout import clear_cache
    clear_cache()


def _font_file():
    """Locate ``vaxfont.dat`` (explicit path, environment, package data, or cwd)."""
    if _FONT_FILE:
        return _FONT_FILE
    candidates = []
    env = os.environ.get('TRIUMF_FONTS')
    if env:
        # The Fortran convention is a directory; accepting a file path too is convenient.
        candidates += [os.path.join(env, 'vaxfont.dat'), env]
    candidates += [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'vaxfont.dat'),
        os.path.join('fonts', 'vaxfont.dat'),
        'vaxfont.dat',
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "vaxfont.dat not found: call set_font_file() or set TRIUMF_FONTS")


def get_font_file():
    """Return the font-library path that will be used.

    Returns
    -------
    str
        The path selected by :func:`set_font_file`, the ``TRIUMF_FONTS`` environment variable,
        the packaged ``strokefont/data/vaxfont.dat``, ``fonts/vaxfont.dat``, or ``vaxfont.dat``,
        in that order.

    Raises
    ------
    FileNotFoundError
        If no ``vaxfont.dat`` file can be found.
    """
    return _font_file()


# PSALPH parameter names (PSYM.F) -> attributes
_PSALPH = {'HSPC': 'hspac', 'VSPC': 'vspac', 'SUPS': 'psup', 'SUBS': 'psub', 'SHGT': 'shgt',
           'SCAL': 'scal', 'HSCL': 'sscal', 'ANGL': 'angl', 'LTRS': 'letterspacing',
           'REFP': 'ref', 'LSPC': 'lspac'}


class PFont:
    """One font loaded from ``vaxfont.dat``.

    The binary layout follows the fields documented in ``PFONT.F``.  Fonts are normally
    obtained through :func:`get_font`, which caches them.

    Attributes
    ----------
    name : str
        Library name.
    grid : int
        Coordinate-grid size.
    refx, refy : int
        Reference point in grid units.
    hspac, vspac : int
        Fixed advance and line-spacing parameters.
    psup, psub : tuple of int
        Superscript and subscript reference points as ``(x, y)``.
    shgt : float
        Script height as a fraction of the current character height.
    scal, sscal : float
        Horizontal and height scale factors.
    angl : float
        Shear angle of the Y axis, in degrees.
    letterspacing : bool
        Whether advances use the glyph width plus ``lspac``.
    lspac : int
        Letterspacing constant.
    defined : frozenset of int
        EBCDIC codes that have their own glyph.
    cap_height : float
        Measured cap height in grid units above the baseline.
    """

    def __init__(self, raw, name):
        """Parse one 24000-byte font record.

        Parameters
        ----------
        raw : bytes
            One complete font record from ``vaxfont.dat``.
        name : str
            Library name to assign to the font.
        """
        h = raw[:180].decode('latin1')
        i8 = lambda k: int(h[k * 8:k * 8 + 8])
        f16 = lambda k: float(h[64 + k * 16:80 + k * 16])
        size, self.grid, self.hspac, self.vspac = i8(0), i8(1), i8(2), i8(3)
        self.psup, self.psub = (i8(4), i8(5)), (i8(6), i8(7))
        self.shgt, self.scal, self.sscal, self.angl = f16(0), f16(1), f16(2), f16(3)
        self.refx, self.refy = int(h[128:136]), int(h[136:144])
        self.letterspacing = (int(h[144:152]) & 0xFFFF) == 0x8000   # high bit of SWITCH
        self.lspac = int(h[152:160])
        self.name = name
        dirn = struct.unpack('<256h', raw[180:692])
        l3 = raw[692:692 + size]
        self.defined = frozenset(c for c in range(256) if dirn[c])   # codes with their own glyph
        two = self.grid > 16
        pen = 255 if two else 15
        self._glyphs = {}
        for c in range(256):
            o = dirn[c]
            n, w = l3[o], l3[o + 1]
            if two:
                b = l3[o + 2:o + 2 + 2 * n]
                pts = [(b[2 * k], b[2 * k + 1]) for k in range(n)]
            else:
                pts = [((p >> 4) & 15, p & 15) for p in l3[o + 2:o + 2 + n]]
            verts, codes, pen_up = [], [], True
            for p in pts:
                if p == (pen, pen):
                    pen_up = True
                    continue
                verts.append(p)
                codes.append(Path.MOVETO if pen_up else Path.LINETO)
                pen_up = False
            # an isolated point (single vertex) is drawn as a dot: duplicate it as a zero-length line
            i = 0
            while i < len(codes):
                if codes[i] == Path.MOVETO and (i + 1 == len(codes) or codes[i + 1] == Path.MOVETO):
                    verts.insert(i + 1, verts[i])
                    codes.insert(i + 1, Path.LINETO)
                i += 1
            self._glyphs[c] = (w, np.array(verts, float).reshape(-1, 2), np.array(codes, np.uint8))
        hs = self._glyphs['H'.encode('cp037')[0]][1]
        self._cap_top = float(hs[:, 1].max()) if len(hs) else self.grid / 2.0
        self.cap_height = self._cap_top - self.refy or self.grid / 2.0   # grid units above baseline

    @property
    def ref(self):
        """Reference point as ``(refx, refy)`` in grid units."""
        return (self.refx, self.refy)

    def glyph(self, code):
        """Return the geometry of one glyph.

        Parameters
        ----------
        code : int
            EBCDIC character code.

        Returns
        -------
        width : int
            Right edge of the glyph in grid units.
        vertices : numpy.ndarray
            ``(N, 2)`` array of grid coordinates.
        codes : numpy.ndarray
            Matplotlib ``Path`` codes (``MOVETO`` / ``LINETO``), one per vertex.
        """
        return self._glyphs[code]

    def with_params(self, **params):
        """Return a copy with PSALPH-style parameter overrides.

        Parameters
        ----------
        **params
            Parameter names from the original PSALPH interface, for example
            ``SHGT=0.7``, ``LSPC=5`` or ``SUPS=(0, 25)``.  Names are case-insensitive.

        Returns
        -------
        PFont
            A copy with the requested overrides.  ``cap_height`` is recalculated if ``REFP``
            changes.

        Raises
        ------
        ValueError
            If a parameter name is unknown or ``ANGL`` is outside ``(-90, 90)``.
        """
        f = copy.copy(self)
        for k, v in params.items():
            key = k.upper()
            if key not in _PSALPH:
                raise ValueError(f"unknown font parameter {k!r}; valid: {sorted(_PSALPH)}")
            if key == 'REFP':
                f.refx, f.refy = int(v[0]), int(v[1])
            elif key == 'LTRS':
                f.letterspacing = bool(v)
            elif key in ('SUPS', 'SUBS'):
                setattr(f, _PSALPH[key], (int(v[0]), int(v[1])))
            else:
                setattr(f, _PSALPH[key], v)
        if not -90.0 < f.angl < 90.0:
            raise ValueError("ANGL must satisfy -90 < ANGL < 90")
        f.cap_height = f._cap_top - f.refy or f.grid / 2.0
        return f


def get_font(name, params=None):
    """Load and cache a font by library name.

    Parameters
    ----------
    name : str
        One of :data:`FONT_NAMES`; matching is case-insensitive.
    params : dict, optional
        PSALPH-style overrides, for example ``{"SHGT": 0.8, "LSPC": 4}``.  The resulting
        configured font is cached separately.

    Returns
    -------
    PFont
        The cached font, or a cached configured copy when ``params`` is given.

    Raises
    ------
    ValueError
        If ``name`` is not a known font or a parameter name is invalid.
    FileNotFoundError
        If the font library cannot be found.
    """
    name = name.upper()
    if name not in FONT_NAMES:
        raise ValueError(f"unknown font {name!r}; see strokefont.FONT_NAMES")
    if name not in _cache:
        i = FONT_NAMES.index(name)
        with open(_font_file(), 'rb') as fh:
            fh.seek(i * _RECLEN)
            _cache[name] = PFont(fh.read(_RECLEN), name)
    if not params:
        return _cache[name]
    key = (name, tuple(sorted((k.upper(), tuple(v) if isinstance(v, (list, tuple)) else v)
                              for k, v in params.items())))
    if key not in _pcache:
        _pcache[key] = _cache[name].with_params(**params)
    return _pcache[key]
