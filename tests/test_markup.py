import pytest

from strokefont._markup import _compile_line, _parse_math, _split_math


def test_split_math_matches_matplotlib_rules():
    assert _split_math("plain text") == [(False, "plain text")]
    assert _split_math(r"cost \$5") == [(False, "cost $5")]
    assert _split_math("a $b$ c") == [(False, "a "), (True, "b"), (False, " c")]
    assert _split_math(r"$a$ and $b$") == [(True, "a"), (False, " and "), (True, "b")]
    assert _split_math("$unclosed") == [(False, "$unclosed")]
    assert _split_math("$a$", parse_math=False) == [(False, "$a$")]


def test_script_parsing():
    nodes = _parse_math("x_i^2")
    assert nodes[0][0] == "c"
    script = nodes[1]
    assert script[0] == "script"
    assert script[1] == "sub"
    assert script[3] is not None       # both a subscript and a superscript


def test_fraction_and_radical_nodes():
    assert _compile_line(r"$\frac{1}{2}$", "mathtext", True)[0][0] == "frac"
    assert _compile_line(r"$\sqrt{x}$", "mathtext", True)[0][0] == "sqrt"


def test_plain_mode_disables_markup():
    nodes = _compile_line("x^2", "plain", True)
    assert [n[0] for n in nodes] == ["c", "c", "c"]
    assert _compile_line(r"$x$", "plain", True)[0][0] == "c"


def test_backslash_commands_and_unicode_symbols():
    assert _compile_line(r"$\alpha$", "mathtext", True) == [("c", 202)]
    assert _compile_line(r"$α$", "mathtext", True) == [("c", 202)]
    assert _compile_line(r"$\frac$", "mathtext", True)[0][0] == "frac"


@pytest.mark.parametrize("command", [r"\infty", r"\degree", r"\alpha"])
def test_symbol_commands_are_known(command):
    nodes = _compile_line(f"${command}$", "mathtext", True)
    assert nodes and nodes[0][0] == "c"


def test_relations_get_spacing():
    nodes = _compile_line(r"$a \le b$", "mathtext", True)
    codes = [n[1] for n in nodes if n[0] == "c"]
    assert 140 in codes
    assert nodes[1][0] == "sp"
