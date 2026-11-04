"""Parser for the matplotlib-style mathtext subset supported by StrokeText."""

import functools
import re

from ._symbols import SYMBOLS, _UNICODE, _code_for


# --------------------------------------------------------------------------- mathtext subset
# Spacing, in units of the cap height, around operators and for the \, \; ... commands.
_SPACES = {',': 0.17, ':': 0.22, ';': 0.28, ' ': 0.33, '!': -0.17, 'quad': 1.4, 'qquad': 2.8}
_RELATIONS = {'=', '<', '>', 'le', 'ge', 'ne', 'approx', 'propto', 'equiv', 'll', 'gg', 'sim',
              'rightarrow', 'leftarrow', 'Rightarrow', 'in', 'subset', 'supset', 'perp',
              'parallel', 'lesssim', 'gtrsim', 'to', 'gets', 'leq', 'geq', 'neq'}
_BINARY = {'+', '-', 'pm', 'mp', 'times', 'div', 'cdot', 'cup', 'cap', 'vee', 'wedge', 'oplus'}
_STYLES = {'mathrm', 'mathit', 'mathbf', 'mathcal', 'mathsf', 'mathtt', 'mathbb', 'mathfrak',
           'mathdefault', 'mathregular', 'text', 'textrm', 'textit', 'textbf', 'textsf', 'texttt',
           'operatorname', 'boldsymbol', 'displaystyle', 'textstyle', 'scriptstyle'}
_IGNORED = {'left', 'right', 'big', 'Big', 'bigg', 'Bigg', 'bigl', 'bigr', 'limits', 'nolimits'}
_FUNCS = {'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan', 'sinh', 'cosh',
          'tanh', 'coth', 'exp', 'log', 'ln', 'lg', 'min', 'max', 'sup', 'inf', 'lim', 'det',
          'dim', 'gcd', 'deg', 'arg', 'Pr', 'ker', 'hom', 'mod'}
_SPECIAL = set('\\{}$%&#_^')
_DOLLAR = re.compile(r'(?<!\\)\$')


def _plain_nodes(text):
    return [('c', _code_for(ch)) for ch in text]


def _split_math(line, parse_math=True):
    """matplotlib's rule: an even, non-zero number of unescaped '$' means math.  -> [(is_math, text)]"""
    if not parse_math:
        return [(False, line)]
    parts = _DOLLAR.split(line)
    if len(parts) < 3 or len(parts) % 2 == 0:             # 0 or odd number of '$'
        return [(False, line.replace(r'\$', '$'))]
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 0:
            if p:
                out.append((False, p.replace(r'\$', '$')))
        else:
            out.append((True, p))
    return out


def _parse_math(s):
    """Parse the inside of $...$ into nodes.
    ('c', code) ('g', nodes) ('sp', w) ('script', kind, node, other) ('frac', n, d) ('sqrt', n)"""
    pos = 0

    def name_at():
        nonlocal pos
        j = pos
        while j < len(s) and s[j].isalpha():
            j += 1
        nm, pos = s[pos:j], j
        return nm

    def group_arg():
        """one argument: {..} group or a single atom"""
        nonlocal pos
        while pos < len(s) and s[pos] == ' ':
            pos += 1
        if pos >= len(s):
            return ('g', [])
        if s[pos] == '{':
            pos += 1
            return ('g', seq('}'))
        return ('g', atom_list())

    def atom_list():
        """exactly one atom (with its operator spacing), as a node list"""
        tmp = []
        prev = [False]
        one(tmp, prev)
        return tmp

    def op_nodes(key, code, out, prev):
        kind = 'rel' if key in _RELATIONS else 'bin' if key in _BINARY else None
        if kind == 'rel' or (kind == 'bin' and prev[0]):
            w = 0.28 if kind == 'rel' else 0.2
            out += [('sp', w), ('c', code), ('sp', w)]
        else:
            out.append(('c', code))
        prev[0] = False

    def one(out, prev):
        """parse one item from the string, appending to out"""
        nonlocal pos
        ch = s[pos]
        if ch == ' ':
            pos += 1
            return
        if ch == '{':
            pos += 1
            out.append(('g', seq('}')))
            prev[0] = True
            return
        if ch == '\\':
            pos += 1
            if pos >= len(s):
                return
            if not s[pos].isalpha():
                c = s[pos]
                pos += 1
                if c in _SPACES:
                    out.append(('sp', _SPACES[c]))
                elif c == '\\':
                    out.append(('sp', 0.33))
                else:
                    out.append(('c', _code_for(c)))
                    prev[0] = True
                return
            nm = name_at()
            if nm in ('frac', 'dfrac', 'tfrac'):
                out.append(('frac', group_arg(), group_arg()))
                prev[0] = True
            elif nm == 'sqrt':
                out.append(('sqrt', group_arg()))
                prev[0] = True
            elif nm in _STYLES:
                out.append(group_arg())
                prev[0] = True
            elif nm in _IGNORED:
                if pos < len(s) and s[pos] not in '\\{ ':
                    out.append(('c', _code_for(s[pos])))
                    pos += 1
                prev[0] = False
            elif nm in _SPACES:
                out.append(('sp', _SPACES[nm]))
            elif nm in SYMBOLS:
                if nm in _RELATIONS or nm in _BINARY:
                    op_nodes(nm, SYMBOLS[nm], out, prev)
                else:
                    out.append(('c', SYMBOLS[nm]))
                    prev[0] = True
            else:                                      # \sin, \cos, unknown -> upright letters
                out.append(('g', _plain_nodes(nm)))
                if nm in _FUNCS:
                    out.append(('sp', 0.17))
                prev[0] = False if nm in _FUNCS else True
            return
        if ch in '^_':
            return                                     # handled by seq()
        pos += 1
        code = _code_for(ch)
        key = ch if ch in _RELATIONS or ch in _BINARY else _UNICODE.get(ch)
        if ch in '−':
            key = '-'
        if key in _RELATIONS or key in _BINARY:
            op_nodes(key, code, out, prev)
        else:
            out.append(('c', code))
            prev[0] = ch not in '([,;'

    def seq(stop=None):
        nonlocal pos
        out, prev = [], [False]
        while pos < len(s):
            ch = s[pos]
            if stop and ch == stop:
                pos += 1
                return out
            if ch in '^_':
                kinds = []
                while pos < len(s) and s[pos] in '^_' and len(kinds) < 2:
                    k = 'sup' if s[pos] == '^' else 'sub'
                    if any(k == q for q, _ in kinds):
                        break
                    pos += 1
                    kinds.append((k, group_arg()))
                    while pos < len(s) and s[pos] == ' ':
                        pos += 1
                out.append(('script', kinds[0][0], kinds[0][1], kinds[1][1] if len(kinds) > 1 else None))
                prev[0] = True
            else:
                one(out, prev)
        return out
    return seq()


@functools.lru_cache(maxsize=None)
def _compile_line(line, markup, parse_math):
    if markup == 'plain':
        return _plain_nodes(line)
    nodes = []
    for is_math, text in _split_math(line, parse_math):
        nodes += _parse_math(text) if is_math else _plain_nodes(text)
    return nodes
