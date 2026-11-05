# strokefont API reference

All public names are re-exported from the top-level package:

```python
import strokefont as sf
```

The installed version is available as `sf.__version__`.

## Font library

The font data lives in `vaxfont.dat`, which is not distributed with the package. See
[Installation](../README.md#installation) for the search order.

### `set_font_file(path)`

Select the font library explicitly.

```python
sf.set_font_file("/path/to/vaxfont.dat")
```

`path` may be a string or any `os.PathLike`. The font cache and cached line geometry are cleared.
Subsequent `get_font()` calls read from this file.

### `get_font_file()`

Return the font-library path that would be used, without loading any glyph data.

```python
sf.get_font_file()
# '/path/to/vaxfont.dat'
```

Raises `FileNotFoundError` if no library can be found.

### `get_font(name, params=None)`

Load a font by name. Names are case-insensitive.

```python
font = sf.get_font("ROMAN.2")
adjusted = sf.get_font("ROMAN.2", params={"SHGT": 0.8, "LSPC": 4})
```

`name` must be one of `sf.FONT_NAMES`; otherwise `ValueError` is raised.

`params` applies PSALPH-style overrides to a copy of the font. The result is cached. Recognised
keys are:

| Key | Attribute | Meaning |
|---|---|---|
| `HSPC` | `hspac` | Fixed advance when letterspacing is off |
| `VSPC` | `vspac` | Original line-spacing value (unused by `StrokeText`) |
| `SUPS` | `psup` | Superscript reference point `(x, y)` |
| `SUBS` | `psub` | Subscript reference point `(x, y)` |
| `SHGT` | `shgt` | Script height as a fraction of the current size |
| `SCAL` | `scal` | Horizontal scale |
| `HSCL` | `sscal` | Original height scale (unused by `StrokeText`) |
| `ANGL` | `angl` | Slant of the Y axis in degrees, with `-90 < ANGL < 90` |
| `LTRS` | `letterspacing` | Enable/disable letterspacing |
| `REFP` | `refx`, `refy` | Reference point `(x, y)` |
| `LSPC` | `lspac` | Letterspacing constant |

### `FONT_NAMES`

A list of the 43 font names in library order. `FONT_NAMES[0]` is `"STANDARD"`; the default
`StrokeText` font is `"TRIUMF.2"`.

### `class PFont`

One loaded font. Instances are normally obtained with `get_font()`.

```python
width, vertices, codes = font.glyph(193)       # EBCDIC code for "A"
```

`vertices` is an `(N, 2)` NumPy array in font-grid coordinates. `codes` contains matplotlib
`Path` codes (`MOVETO` / `LINETO`). `width` is the glyph's right edge in grid units.

Font properties include:

| Attribute | Meaning |
|---|---|
| `name` | Library name |
| `grid` | Coordinate-grid size |
| `refx`, `refy` | Reference point in grid units |
| `hspac`, `vspac` | Fixed advance and line-spacing parameters |
| `psup`, `psub` | Superscript/subscript reference points |
| `shgt` | Script-size factor |
| `scal`, `sscal` | Horizontal and height scale |
| `angl` | Shear angle in degrees |
| `letterspacing`, `lspac` | Letterspacing flag and constant |
| `cap_height` | Measured cap height in grid units |
| `defined` | Frozenset of character codes with their own glyph |

#### `PFont.glyph(code)`

Return `(width, vertices, path_codes)` for one EBCDIC character code.

#### `PFont.with_params(**params)`

Return a copy of the font with PSALPH-style overrides. Unknown parameter names raise
`ValueError`, as does an `ANGL` outside `(-90, 90)`.

#### `PFont.ref`

Read-only property returning `(refx, refy)`.

## Text artist

### `class StrokeText(x=0, y=0, text='', *, font=None, linewidth=None, capheight=None, markup=None, params=None, **kwargs)`

A drop-in `matplotlib.text.Text` subclass that draws text as strokes. It accepts the normal
matplotlib text arguments (`fontsize`, `color`, `alpha`, `ha`, `va`, `rotation`,
`rotation_mode`, `multialignment`, `linespacing`, `transform`, `clip_on`, `zorder`, `parse_math`,
...); `fontfamily`, `fontweight` and `fontstyle` are ignored.

```python
ax.add_artist(
    sf.StrokeText(0.5, 0.5, r"decay $e^{-t/\tau}$", font="ROMAN.2", fontsize=14,
                  transform=ax.transAxes, ha="center", va="center")
)
```

| Extra argument | Meaning | Default |
|---|---|---|
| `font` | Font name from `FONT_NAMES` | `StrokeText.default_font` (`"TRIUMF.2"`) |
| `linewidth` | Pen width in points | `StrokeText.default_linewidth` or `0.09 * fontsize` |
| `capheight` | Cap height as a fraction of `fontsize` | `StrokeText.default_capheight` (`0.72`) |
| `markup` | `"mathtext"`, `"legacy"` or `"plain"` | `StrokeText.default_markup` (`"mathtext"`) |
| `params` | PSALPH-style font overrides | `StrokeText.default_params` (none) |

Explicit per-artist values override the installed defaults. Per-artist `params` are merged over
`StrokeText.default_params`.

#### `StrokeText.set_stroke_font(font=None, linewidth=None, capheight=None, markup=None, params=None)`

Update rendering options on an existing artist. Only non-`None` arguments are changed. Raises
`ValueError` for an unknown font, invalid markup, or invalid font parameters.

#### `StrokeText.get_stroke_font()`

Return the effective `PFont`, including any per-artist and installed `params` overrides.

#### `StrokeText.get_window_extent(renderer=None, dpi=None)`

Return the display-coordinate bounding box, like `matplotlib.text.Text.get_window_extent()`.

#### Class defaults

These attributes control text created without explicit per-artist overrides:

```python
sf.StrokeText.default_font         # "TRIUMF.2"
sf.StrokeText.default_markup       # "mathtext"
sf.StrokeText.default_linewidth    # None -> 0.09 * fontsize
sf.StrokeText.default_capheight    # 0.72
sf.StrokeText.default_params       # None
```

Prefer `sf.install()` or `sf.use()` rather than assigning these directly; they handle the
matplotlib creation hooks and the context-manager restoration.

## Global installation

### `install(font=None, markup=None, *, linewidth=None, capheight=None, params=None)`

Make matplotlib create `StrokeText` wherever it creates `Text`: tick labels, axis labels, titles,
legends, `ax.text`, `fig.text`, colour-bar labels, and similar artists. Only artists created
after the call are affected. `Annotation` text keeps the normal font.

```python
sf.install("TRIUMF.2", linewidth=1.0, capheight=0.70, params={"SHGT": 0.8})
```

The keyword arguments set global defaults for newly created artists. Explicit arguments on a
`StrokeText` still win. Unknown fonts and invalid markup raise `ValueError`.

### `uninstall()`

Undo `install()` and restore the matplotlib objects that were replaced. Artists already created
as `StrokeText` keep their type.

### `use(font=None, markup=None, *, linewidth=None, capheight=None, params=None)`

Context-manager form of `install()`. All defaults, including font, markup, linewidth, capheight
and params, are restored when the block exits.

```python
with sf.use("ROMAN.2", "plain", linewidth=0.8, params={"SHGT": 0.75}):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    fig.savefig("out.pdf")
```

### `stroke_texts(artist, font=None, **kwargs)`

Convert existing matplotlib `Text` artists to `StrokeText` in place.

```python
fig.canvas.draw()
sf.stroke_texts(fig, "TRIUMF.2", linewidth=0.8)
```

`artist` may be a `Figure`, `Axes`, `Legend`, `Text`, or an iterable of those. Extra keyword
arguments are forwarded to `StrokeText.set_stroke_font()` (`linewidth`, `capheight`, `markup`,
`params`). Convert after tick labels and legends exist; later ticks created by an interactive
zoom are not converted. For that case use `install()` or `use()` instead.

## Character mapping

### `code_for(ch)`

Return the EBCDIC slot used for a single character. Unicode Greek letters, mathematical symbols
and a few typographic variants are mapped to the same slots as their markup equivalents.
Unmapped characters return `111` (the `?` slot).

```python
sf.code_for("A")      # 193
sf.code_for("α")      # 202
```

### `SYMBOLS`

A dictionary mapping markup names to EBCDIC codes:

```python
sf.SYMBOLS["alpha"]   # 202
sf.SYMBOLS["le"]      # 140
```

It includes Greek letters, relations, operators, arrows and other mathematical symbols. See the
[README symbol list](../README.md#symbols) for the supported markup names.

### Legacy PSYM control constants

These are used with `markup="legacy"`:

| Constant | Value | Effect |
|---|---|---|
| `UP` | `"\t"` | Superscript |
| `DOWN` | `"\x01"` | Subscript |
| `UPSIZE` | `"\x03"` | Up, always reducing size |
| `DOWNSIZE` | `"\x02"` | Down, always reducing size |
| `BACKSPACE` | `"\b"` | One-character backspace |

```python
text = "x" + sf.UP + "2" + sf.DOWN + " y"
artist = sf.StrokeText(0, 0, text, markup="legacy")
```

## Errors and font-data notes

- `get_font()` and `StrokeText` raise `ValueError` for an unknown font name.
- `set_font_file()` does not check that the path exists; loading a font does.
- `get_font_file()` raises `FileNotFoundError` when no `vaxfont.dat` is found.
- `params` with an unknown PSALPH key raises `ValueError` when the font is loaded.
- The font file itself is not covered by the package's BSD-3-Clause license.
