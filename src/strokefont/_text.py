"""The matplotlib Text subclass that draws text as stroke geometry."""

import numpy as np
from matplotlib.path import Path
from matplotlib.text import Text as _MplText
from matplotlib.transforms import Bbox, IdentityTransform

from ._font import FONT_NAMES, get_font
from ._layout import _line_geometry


class _StrokeMixin:
    default_font = 'TRIUMF.2'
    default_markup = 'mathtext'      # 'mathtext' | 'legacy' | 'plain'
    default_linewidth = None         # points; None -> 0.09 * fontsize
    default_capheight = 0.72         # cap height as a fraction of fontsize (Helvetica ~0.72)
    default_params = None            # PSALPH overrides applied to every StrokeText
    _sf_font = None
    _sf_linewidth = None
    _sf_capheight = None
    _sf_markup = None
    _sf_params = None

    def set_stroke_font(self, font=None, linewidth=None, capheight=None, markup=None, params=None):
        """Change the stroke-rendering options on this artist.

        Parameters
        ----------
        font : str, optional
            Font name from :data:`strokefont.FONT_NAMES`.
        linewidth : float, optional
            Pen width in points.
        capheight : float, optional
            Cap height as a fraction of ``fontsize``.
        markup : {"mathtext", "legacy", "plain"}, optional
            Markup parser to use.
        params : dict, optional
            PSALPH-style font parameter overrides.

        Only arguments that are not ``None`` are changed.  The artist is marked stale so the
        next draw uses the new settings.
        """
        if font is not None:
            if font.upper() not in FONT_NAMES:
                raise ValueError(f"unknown font {font!r}; see strokefont.FONT_NAMES")
            self._sf_font = font.upper()
        if linewidth is not None:
            self._sf_linewidth = linewidth
        if capheight is not None:
            self._sf_capheight = capheight
        if markup is not None:
            if markup not in ('mathtext', 'legacy', 'plain'):
                raise ValueError("markup must be 'mathtext', 'legacy' or 'plain'")
            self._sf_markup = markup
        if params is not None:
            self._sf_params = dict(params)
        self.stale = True

    def _effective_linewidth(self):
        linewidth = self._sf_linewidth
        if linewidth is None:
            linewidth = StrokeText.default_linewidth
        return 0.09 * self.get_fontsize() if linewidth is None else linewidth

    def _effective_capheight(self):
        return (self._sf_capheight if self._sf_capheight is not None
                else StrokeText.default_capheight)

    def _effective_params(self):
        params = StrokeText.default_params
        if self._sf_params:
            params = {**(params or {}), **self._sf_params}
        return params

    def get_stroke_font(self):
        """Return the effective :class:`~strokefont.PFont` for this artist.

        Per-artist parameters are merged over the defaults installed by
        :func:`strokefont.install` or :func:`strokefont.use`.
        """
        return get_font(self._sf_font or StrokeText.default_font, self._effective_params())

    # -- geometry ------------------------------------------------------------------
    def _stroke_layout(self, px_per_pt, pos):
        """Return (verts_display, codes, bbox_display)."""
        font = self.get_stroke_font()
        markup = self._sf_markup or StrokeText.default_markup
        parse_math = self.get_parse_math() if hasattr(self, 'get_parse_math') else True
        capheight = self._effective_capheight()
        cap_px = self.get_fontsize() * px_per_pt * capheight
        lines = self.get_text().split('\n')
        ls = self.get_linespacing()
        ls = 1.2 if ls == 'normal' else float(ls)         # newer matplotlib: 'normal'
        pitch = ls / capheight                            # cap units
        lay = [_line_geometry(font, ln, markup, parse_math) for ln in lines]
        W = max(l[2] for l in lay)
        ha = self.get_horizontalalignment()
        ma = self._get_multialignment() or ha
        V, C = [], []
        for i, (v, c, w) in enumerate(lay):
            dx = {'left': 0, 'center': (W - w) / 2, 'right': W - w}[ma]
            if len(v):
                V.append(v + [dx, -i * pitch])
                C.append(c)
        verts = np.vstack(V) if V else np.zeros((0, 2))
        codes = np.concatenate(C) if C else np.zeros(0, np.uint8)
        top = max(1.0, verts[:, 1].max() if len(verts) else 1.0)
        bot = min(-0.3 - (len(lines) - 1) * pitch, verts[:, 1].min() if len(verts) else 0.0)
        # block corners in local (cap-height) units, baseline of first line at y=0
        corners = np.array([[0, bot], [W, bot], [W, top], [0, top]])
        ax_ = {'left': 0.0, 'center': W / 2, 'right': W}[ha]
        va = self.get_verticalalignment()
        base = -(len(lines) - 1) * pitch          # like Text: 'baseline' is the LAST line's baseline
        ay_ = {'baseline': base, 'top': top, 'bottom': bot, 'center': (top + bot) / 2,
               'center_baseline': (top + base) / 2}[va]
        rot = np.radians(self.get_rotation())
        R = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]])
        if self.get_rotation_mode() == 'anchor':
            off = np.array([ax_, ay_])
            verts = (verts - off) @ R.T * cap_px + pos
            corners = (corners - off) @ R.T * cap_px + pos
        else:
            rv, rc = verts @ R.T, corners @ R.T
            lo, hi = rc.min(0), rc.max(0)
            ox = {'left': lo[0], 'center': (lo[0] + hi[0]) / 2, 'right': hi[0]}[ha]
            by = (R @ np.array([0.0, base]))[1]
            oy = {'top': hi[1], 'bottom': lo[1], 'center': (lo[1] + hi[1]) / 2,
                  'baseline': by, 'center_baseline': (hi[1] + by) / 2}[va]
            off = np.array([ox, oy])
            verts = (rv - off) * cap_px + pos
            corners = (rc - off) * cap_px + pos
        bbox = Bbox([corners.min(0), corners.max(0)])
        return verts, codes, bbox

    def _get_layout(self, renderer):
        """Text._get_layout replacement; this is what TextArea (legend entries, offsetboxes)
        calls to size the text.  Returns (bbox, info, (xy, size)) in pixels."""
        ppp = renderer.points_to_pixels(1.0)
        _, _, bbox = self._stroke_layout(ppp, np.zeros(2))
        cap_px = self.get_fontsize() * ppp * self._effective_capheight()
        lines = self.get_text().split('\n')
        w, h = bbox.size
        desc = 0.3 * cap_px
        ls = self.get_linespacing()
        pitch = (1.2 if ls == 'normal' else float(ls)) * self.get_fontsize() * ppp
        info = [(ln, (w, h - desc, desc), (0.0, -i * pitch)) for i, ln in enumerate(lines)]
        return bbox, info, ((bbox.x0, bbox.y0), (w, h))

    def _fig_px_per_pt(self, dpi=None):
        if dpi is None:
            try:
                fig = self.get_figure(root=True)   # matplotlib >= 3.10
            except TypeError:
                fig = self.get_figure()
            dpi = fig.dpi
        return dpi / 72.0

    def get_window_extent(self, renderer=None, dpi=None):
        """Return the display-coordinate bounding box of the stroke text.

        Parameters
        ----------
        renderer : matplotlib renderer, optional
            Unused; accepted for compatibility with ``matplotlib.text.Text``.
        dpi : float, optional
            Dots per inch used to convert points to pixels.  Defaults to the figure DPI.

        Returns
        -------
        matplotlib.transforms.Bbox
            The text bounding box in display coordinates.
        """
        pos = np.asarray(self._get_xy_display(), float)
        if not self.get_visible() or not self.get_text():
            return Bbox.from_bounds(pos[0], pos[1], 0, 0)      # same as Text for empty strings
        return self._stroke_layout(self._fig_px_per_pt(dpi), pos)[2]

    # -- drawing ---------------------------------------------------------------------
    def draw(self, renderer):
        """Draw the stroke geometry with the active matplotlib renderer."""
        if not self.get_visible() or not self.get_text():
            return
        ppp = renderer.points_to_pixels(1.0)
        pos = np.asarray(self._get_xy_display(), float)
        verts, codes, _ = self._stroke_layout(ppp, pos)
        if not len(verts):
            return
        renderer.open_group('text', self.get_gid())
        gc = renderer.new_gc()
        gc.set_foreground(self.get_color())
        gc.set_alpha(self.get_alpha())
        gc.set_linewidth(self._effective_linewidth())
        gc.set_capstyle('round')
        gc.set_joinstyle('round')
        if hasattr(self, 'get_antialiased'):
            gc.set_antialiased(self.get_antialiased())
        self._set_gc_clip(gc)
        if self.get_url():
            gc.set_url(self.get_url())
        gc.set_gid(self.get_gid())
        renderer.draw_path(gc, Path(verts, codes), IdentityTransform())
        gc.restore()
        renderer.close_group('text')
        self.stale = False


class StrokeText(_StrokeMixin, _MplText):
    """``matplotlib.text.Text`` drawn with a Physica/TRIUMF stroke font.

    This is a drop-in replacement for ``Text``.  The usual Text options work (``fontsize``,
    ``color``, ``alpha``, ``ha``, ``va``, ``rotation``, ``rotation_mode``, ``multialignment``,
    ``linespacing``, ``transform``, ``clip_on``, ``zorder``, ``parse_math``, ...);
    ``fontfamily``, ``fontweight`` and ``fontstyle`` are ignored.  Strings use matplotlib's
    mathtext conventions: text outside ``$...$`` is literal, while text inside it uses the
    mathtext subset described in the README.

    Extra keywords
    --------------
    font : str, optional
        Library font name.  Defaults to ``StrokeText.default_font`` (``"TRIUMF.2"``).
    linewidth : float, optional
        Pen width in points.  Defaults to ``StrokeText.default_linewidth`` or
        ``0.09 * fontsize``.
    capheight : float, optional
        Cap height as a fraction of ``fontsize``.  Defaults to
        ``StrokeText.default_capheight`` (``0.72``).
    markup : {"mathtext", "legacy", "plain"}, optional
        ``"mathtext"`` (default), ``"legacy"`` for the original PSYM control characters, or
        ``"plain"`` for no markup.
    params : dict, optional
        PSALPH-style font parameter overrides, for example ``{"SHGT": 0.7, "LSPC": 4}``.
        These are merged over ``StrokeText.default_params``.

    Notes
    -----
    Installed defaults can be set globally with :func:`strokefont.install` or
    :func:`strokefont.use`; explicit values passed to this constructor take precedence.
    """

    def __init__(self, x=0, y=0, text='', *, font=None, linewidth=None, capheight=None,
                 markup=None, params=None, **kw):
        """Create a stroke-text artist at ``(x, y)``.

        Positional arguments and ``**kw`` are forwarded to ``matplotlib.text.Text``; the
        stroke-specific keywords are documented on the class.
        """
        super().__init__(x, y, text, **kw)
        self.set_stroke_font(font, linewidth, capheight, markup, params)

