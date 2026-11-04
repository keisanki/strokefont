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


def install(font=None, markup=None):
    """Make matplotlib create StrokeText wherever it creates Text (tick labels, axis labels,
    titles, legends, ax.text, fig.text, colour-bar labels).  Affects artists created *after* the
    call.  `font` and `markup` set the defaults.  Annotation text keeps the normal font.

    matplotlib.text itself is not modified (Annotation calls Text.__init__ explicitly);
    instead the other matplotlib modules' references to it are redirected.  Undo: uninstall().
    """
    if font is not None:
        if font.upper() not in FONT_NAMES:
            raise ValueError(f"unknown font {font!r}")
        StrokeText.default_font = font.upper()
    if markup is not None:
        StrokeText.default_markup = markup
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
    for mod, attr, val in reversed(_installed):
        setattr(mod, attr, val)
    _installed.clear()


@contextlib.contextmanager
def use(font=None, markup=None):
    """with strokefont.use('ROMAN.2'): ... figures created inside use stroke fonts."""
    old = (StrokeText.default_font, StrokeText.default_markup)
    install(font, markup)
    try:
        yield
    finally:
        uninstall()
        StrokeText.default_font, StrokeText.default_markup = old


def stroke_texts(artist, font=None, **kw):
    """Switch existing plain Text objects over to stroke rendering, in place.

    `artist` may be a Figure, Axes, Legend, Text or an iterable of those.  Convert *after* the
    ticks exist (call fig.canvas.draw() or set the ticks explicitly first); ticks created later by
    the locator are not converted -- for that use install()/use().  Annotation text is left alone.
    Legends (entries and title) are converted too: create them first, then call this.
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
