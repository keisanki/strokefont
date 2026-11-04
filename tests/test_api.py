import strokefont as sf


def test_version_is_exposed():
    assert isinstance(sf.__version__, str)
    assert sf.__version__


def test_public_api_is_importable():
    expected = {
        "BACKSPACE",
        "DOWN",
        "DOWNSIZE",
        "FONT_NAMES",
        "PFont",
        "StrokeText",
        "SYMBOLS",
        "UP",
        "UPSIZE",
        "code_for",
        "get_font",
        "get_font_file",
        "install",
        "set_font_file",
        "stroke_texts",
        "uninstall",
        "use",
    }
    for name in expected:
        assert hasattr(sf, name), name
        assert name in sf.__all__, name


def test_all_is_sorted_and_unique():
    assert len(sf.__all__) == len(set(sf.__all__))
    assert sf.__all__ == sorted(sf.__all__)


def test_font_library_names():
    assert len(sf.FONT_NAMES) == 43
    assert len(set(sf.FONT_NAMES)) == len(sf.FONT_NAMES)
    assert sf.FONT_NAMES[0] == "STANDARD"
    assert sf.FONT_NAMES[-1] == "TRIUMF.OUTLINE"


def test_legacy_control_characters():
    assert sf.UP == "\t"
    assert sf.DOWN == "\x01"
    assert sf.UPSIZE == "\x03"
    assert sf.DOWNSIZE == "\x02"
    assert sf.BACKSPACE == "\b"


def test_symbol_table_uses_ebcdic_slots():
    assert sf.SYMBOLS["alpha"] == 202
    assert sf.SYMBOLS["Omega"] == 225
    assert sf.SYMBOLS["le"] == 140
    assert sf.code_for("A") == 193
    assert sf.code_for("α") == sf.SYMBOLS["alpha"]
    assert sf.code_for("\N{SNOWMAN}") == 111
