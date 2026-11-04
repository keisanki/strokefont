import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.text import Text

import strokefont as sf

pytestmark = pytest.mark.usefixtures("configured_font")


def test_stroketext_draws_and_reports_an_extent():
    fig, ax = plt.subplots()
    text = sf.StrokeText(0.5, 0.5, r"$E = mc^2$", transform=ax.transAxes,
                         ha="center", va="center")
    ax.add_artist(text)
    fig.canvas.draw()

    bbox = text.get_window_extent(fig.canvas.get_renderer())
    assert bbox.width > 0
    assert bbox.height > 0


def test_empty_stroketext_has_zero_extent():
    fig, ax = plt.subplots()
    text = sf.StrokeText(0.5, 0.5, "", transform=ax.transAxes)
    ax.add_artist(text)
    fig.canvas.draw()

    bbox = text.get_window_extent(fig.canvas.get_renderer())
    assert bbox.width == 0
    assert bbox.height == 0


def test_use_installs_and_uninstalls_the_text_factory():
    with sf.use("ROMAN.2"):
        fig, ax = plt.subplots()
        ax.set_title("title")
        ax.plot([0, 1], [0, 1], label="line")
        ax.legend()
        assert isinstance(ax.title, sf.StrokeText)
        assert ax.title.get_stroke_font().name == "ROMAN.2"
        fig.canvas.draw()

    fig, ax = plt.subplots()
    ax.set_title("title")
    assert type(ax.title) is Text
    plt.close("all")


def test_stroke_texts_converts_existing_artists():
    fig, ax = plt.subplots()
    ax.set_title("title")
    ax.set_xlabel("x")
    fig.canvas.draw()

    sf.stroke_texts(fig, "TRIUMF.2")

    assert isinstance(ax.title, sf.StrokeText)
    assert isinstance(ax.xaxis.label, sf.StrokeText)
    assert ax.title._sf_font == "TRIUMF.2"
    fig.canvas.draw()
    plt.close(fig)


def test_stroketext_rejects_unknown_options():
    with pytest.raises(ValueError, match="unknown font"):
        sf.StrokeText(0, 0, "x", font="NOPE")
    with pytest.raises(ValueError, match="markup"):
        sf.StrokeText(0, 0, "x", markup="nope")


def test_multiline_and_markup_modes():
    fig, ax = plt.subplots()
    for i, kwargs in enumerate([
        {},
        {"markup": "plain"},
        {"markup": "legacy"},
        {"params": {"SHGT": 0.8}},
    ]):
        ax.add_artist(sf.StrokeText(0, i, "line one\nline two $x_i^2$", **kwargs))
    fig.canvas.draw()
    assert not ax.figure.stale
    plt.close(fig)
