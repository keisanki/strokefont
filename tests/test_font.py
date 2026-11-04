import pytest

import strokefont as sf

pytestmark = pytest.mark.usefixtures("configured_font")


def test_get_font_is_case_insensitive():
    font = sf.get_font("triumf.2")
    assert font.name == "TRIUMF.2"
    assert font is sf.get_font("TRIUMF.2")


def test_font_metrics_and_glyph_lookup():
    font = sf.get_font("ROMAN.2")
    assert font.grid > 0
    assert font.cap_height > 0
    assert font.ref == (font.refx, font.refy)

    width, vertices, codes = font.glyph("A".encode("cp037")[0])
    assert width > 0
    assert vertices.shape[1] == 2
    assert len(vertices) == len(codes)
    assert set(int(c) for c in codes) <= {1, 2}       # MOVETO / LINETO


def test_unknown_font_is_rejected():
    with pytest.raises(ValueError, match="unknown font"):
        sf.get_font("NOT.A.FONT")


def test_font_parameter_overrides_are_cached_and_validated():
    base = sf.get_font("ROMAN.2")
    adjusted = sf.get_font("ROMAN.2", {"SHGT": 0.8, "LSPC": 4})
    assert adjusted is not base
    assert adjusted is sf.get_font("ROMAN.2", {"SHGT": 0.8, "LSPC": 4})
    assert adjusted.shgt == 0.8
    assert adjusted.lspac == 4

    with pytest.raises(ValueError, match="unknown font parameter"):
        sf.get_font("ROMAN.2", {"NOT_A_PARAM": 1})

    with pytest.raises(ValueError, match="ANGL"):
        sf.get_font("ROMAN.2", {"ANGL": 90})


def test_ref_override_is_applied():
    font = sf.get_font("ROMAN.2", {"REFP": (1, 2)})
    assert font.ref == (1, 2)
    assert font.cap_height > 0


def test_get_font_file_reports_the_configured_library(font_file):
    assert sf.get_font_file() == str(font_file)
