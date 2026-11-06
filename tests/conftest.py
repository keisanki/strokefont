from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FONT_FILES = (
    ROOT / "src" / "strokefont" / "data" / "vaxfont.dat",
    ROOT / "vaxfont.dat",
)


@pytest.fixture(scope="session")
def font_file():
    """The local (unredistributed) font library used by the functional tests."""
    for path in FONT_FILES:
        if path.is_file():
            return path
    pytest.skip("vaxfont.dat is not available in the source checkout")


@pytest.fixture
def configured_font(font_file):
    """Point strokefont at the local font library."""
    import strokefont as sf

    sf.set_font_file(font_file)
    return font_file


@pytest.fixture(autouse=True)
def reset_global_state():
    """Keep install()/use() and default-font changes from leaking between tests."""
    import strokefont as sf

    yield
    sf.uninstall()
    sf.StrokeText.default_font = "TRIUMF.2"
    sf.StrokeText.default_markup = "mathtext"
    sf.StrokeText.default_linewidth = None
    sf.StrokeText.default_capheight = 0.72
    sf.StrokeText.default_params = None
