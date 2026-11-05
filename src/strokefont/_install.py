"""Global matplotlib integration: install(), use() and stroke_texts()."""

import contextlib
import sys
import types

import matplotlib.text as _mpl_text
from matplotlib.text import Text as _MplText

from ._font import FONT_NAMES
from ._text import StrokeText


_installed = []          # (module, attribute, original) for uninstall()


class _TextMeta(type):
    """Makes isinstance()/issubclass() against the factory accept every matplotlib Text."""
    def __instancecheck__(cls, obj):
        return isinstance(obj, _MplText)

    def __subclasscheck__(cls, sub):
        return issubclass(sub, _MplText)


class _TextFactory(_MplText, metaclass=_TextMeta):
    """Stand-in for matplotlib.text.Text at *creation sites*: Text(...) gives a StrokeText."""
    def __new__(cls, *args, **kwargs):
        return StrokeText(*args, **kwargs)


class _TextModule(types.ModuleType):
    """matplotlib.text with Text replaced by the factory (Annotation etc. untouched)."""
    def __init__(self):
        super().__init__('matplotlib.text')
        self.Text = _TextFactory

    def __getattr__(self, name):
        return getattr(_mpl_text, name)


def install(font=None, markup=None, *, linewidth=None, capheight=None, params=None):
    """Make matplotlib create :class:`~strokefont.StrokeText` wherever it creates ``Text``.

    This covers tick labels, axis labels, titles, legends, ``ax.text``, ``fig.text``,
    colour-bar labels and similar artists created *after* the call.  Annotation text keeps the
    normal font.

    Parameters
    ----------
    font : str, optional
        Default font name from :data:`strokefont.FONT_NAMES`.
    markup : {"mathtext", "legacy", "plain"}, optional
        Default markup mode.
    linewidth : float, optional
        Default pen width in points.
    capheight : float, optional
        Default cap height as a fraction of ``fontsize``.
    params : dict, optional
        Default PSALPH-style font parameter overrides.

    Raises
    ------
    ValueError
        If ``font`` is unknown or ``markup`` is invalid.

    Notes
    -----
    The optional keyword arguments set global defaults for newly created artists; explicit
    arguments on an individual :class:`~strokefont.StrokeText` still win.  ``matplotlib.text``
    itself is not modified, because ``Annotation`` calls ``Text.__init__`` explicitly; instead
    the other matplotlib modules' references to ``Text`` are redirected.

    Calling :func:`install` while already installed updates the defaults without replacing the
    hooks again.  Use :func:`uninstall` to undo the installation.
    """
    if font is not None:
        font = font.upper()
        if font not in FONT_NAMES:
            raise ValueError(f"unknown font {font!r}")
    if markup is not None and markup not in ('mathtext', 'legacy', 'plain'):
        raise ValueError("markup must be 'mathtext', 'legacy' or 'plain'")
    if font is not None:
        StrokeText.default_font = font
    if markup is not None:
        StrokeText.default_markup = markup
    if linewidth is not None:
        StrokeText.default_linewidth = linewidth
    if capheight is not None:
        StrokeText.default_capheight = capheight
    if params is not None:
        StrokeText.default_params = dict(params)
    if _installed:
        return
    proxy = _TextModule()
    for name, mod in list(sys.modules.items()):
        if (mod is None or not name.startswith('matplotlib.') or name == 'matplotlib.text'
                or not hasattr(mod, '__dict__')):
            continue
        for attr, val in list(vars(mod).items()):
            if val is _mpl_text:
                _installed.append((mod, attr, val))
                setattr(mod, attr, proxy)
            elif val is _MplText:
                _installed.append((mod, attr, val))
                setattr(mod, attr, _TextFactory)


def uninstall():
    """Undo :func:`install` and restore matplotlib's original ``Text`` references.

    Artists that were already created as :class:`~strokefont.StrokeText` keep their type and
    rendering options.
    """
    for mod, attr, val in reversed(_installed):
        setattr(mod, attr, val)
    _installed.clear()


@contextlib.contextmanager
def use(font=None, markup=None, *, linewidth=None, capheight=None, params=None):
    """Context manager form of :func:`install`.

    The arguments are the same as for :func:`install`.  All global defaults and matplotlib's
    original ``Text`` references are restored when the block exits, even if an exception is
    raised.

    Examples
    --------
    >>> with use("ROMAN.2", linewidth=1.0, params={"SHGT": 0.8}):
    ...     fig, ax = plt.subplots()
    ...     ax.plot([0, 1], [0, 1])
    ...     fig.savefig("out.pdf")
    """
    old = (StrokeText.default_font, StrokeText.default_markup, StrokeText.default_linewidth,
           StrokeText.default_capheight, StrokeText.default_params)
    install(font, markup, linewidth=linewidth, capheight=capheight, params=params)
    try:
        yield
    finally:
        uninstall()
        (StrokeText.default_font, StrokeText.default_markup, StrokeText.default_linewidth,
         StrokeText.default_capheight, StrokeText.default_params) = old


def stroke_texts(artist, font=None, **kw):
    """Convert existing matplotlib text artists to stroke rendering, in place.

    Parameters
    ----------
    artist : matplotlib.artist.Artist or iterable
        A ``Figure``, ``Axes``, ``Legend``, ``Text`` or an iterable of those.
    font : str, optional
        Font name to apply.  If omitted, the current default is used.
    **kw
        Additional options forwarded to :meth:`StrokeText.set_stroke_font`, such as
        ``linewidth``, ``capheight``, ``markup`` or ``params``.

    Notes
    -----
    Convert *after* tick labels and legends exist.  Call ``fig.canvas.draw()`` or set ticks
    explicitly first; tick labels created later by a locator or interactive zoom are not
    converted.  For that case use :func:`install` or :func:`use` instead.

    Legends are converted, including their entries and title.  Annotation text is left alone.
    """
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.legend import Legend
    if isinstance(artist, Legend):
        for t in (*artist.get_texts(), artist.get_title()):
            stroke_texts(t, font, **kw)
    elif isinstance(artist, _MplText):
        if type(artist) is _MplText:
            artist.__class__ = StrokeText
        if isinstance(artist, StrokeText):
            artist.set_stroke_font(font, **kw)
    elif isinstance(artist, Figure):
        for t in artist.texts:
            stroke_texts(t, font, **kw)
        for lg in artist.legends:
            stroke_texts(lg, font, **kw)
        for ax in artist.axes:
            stroke_texts(ax, font, **kw)
    elif isinstance(artist, Axes):
        for t in (artist.title, artist._left_title, artist._right_title,
                  artist.xaxis.label, artist.yaxis.label, artist.xaxis.offsetText,
                  artist.yaxis.offsetText, *artist.texts,
                  *artist.get_xticklabels(which='both'), *artist.get_yticklabels(which='both')):
            stroke_texts(t, font, **kw)
        if artist.get_legend() is not None:
            stroke_texts(artist.get_legend(), font, **kw)
    else:
        for a in artist:
            stroke_texts(a, font, **kw)
