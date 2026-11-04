from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FONT_FILE = ROOT / "vaxfont.dat"


@pytest.fixture(scope="session")
def font_file():
    """The local (unredistributed) font library used by the functional tests."""
    if not FONT_FILE.is_file():
        pytest.skip("vaxfont.dat is not available in the source checkout")
    return FONT_FILE


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
