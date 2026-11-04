"""EBCDIC character mapping and the original PSYM control characters."""

import unicodedata

# Original PSYM control characters (ASCII input).  PSYM.F: Up = Z'09', Down = Z'01',
# Up/Down-with-size-change = Z'03' / Z'02', backspace = Z'08', carriage return = Z'0A'.
UP = '\t'
DOWN = '\x01'
UPSIZE = '\x03'
DOWNSIZE = '\x02'
BACKSPACE = '\b'

# --------------------------------------------------------------------------- symbols
# Characters are addressed by EBCDIC code (PSYM.F: "the native code of the PSYM font structure").
# Greek letters and math symbols sit in slots EBCDIC leaves unused -- verified for TRIUMF.1 and
# TRIUMF.2 on the contact sheet (see demo_charmap.py).
SYMBOLS = {
    # capital Greek
    'Gamma': 112, 'Delta': 128, 'Theta': 144, 'Lambda': 160, 'Xi': 176, 'Upsilon': 192,
    'Phi': 208, 'Psi': 224, 'Omega': 225, 'Sigma': 106, 'Pi': 102,
    # lower-case Greek
    'alpha': 202, 'beta': 203, 'gamma': 204, 'delta': 205, 'epsilon': 206, 'zeta': 207,
    'eta': 218, 'vartheta': 219, 'iota': 220, 'kappa': 221, 'lambda': 222, 'mu': 223,
    'nu': 234, 'xi': 235, 'omicron': 236, 'pi': 237, 'rho': 238, 'sigma': 239,
    'tau': 250, 'upsilon': 251, 'phi': 252, 'chi': 253, 'psi': 254, 'omega': 255,
    'theta': 121, 'varepsilon': 120, 'varphi': 116,
    # math
    'forall': 65, 'times': 66, 'div': 67, 'rightarrow': 68, 'leftarrow': 69, 'uparrow': 70,
    'downarrow': 71, 'parallel': 72, 'perp': 73, 'hbar': 74, 'propto': 81, 'exists': 82,
    'in': 83, 'subset': 84, 'cup': 85, 'supset': 86, 'cap': 87, 'vee': 88, 'wedge': 89,
    'neg': 95, 'angle': 98, 'cdot': 100, 'therefore': 101, 'int': 104, 'oint': 105,
    'aleph': 113, 'infty': 114, 'nabla': 117, 'sqrt': 118, 'partial': 119,
    'section': 138, 'le': 140, 'Rightarrow': 142, 'approx': 143, 'pm': 158,
    'dagger': 170, 'degree': 161, 'ge': 174, 'oplus': 175, 'ne': 190,
    'langle': 171, 'rangle': 187, 'll': 183, 'gg': 184, 'lesssim': 185, 'gtrsim': 186,
    'equiv': 188, 'mp': 191, 'sim': 103,
}
# aliases for common LaTeX / mathtext spellings
for _a, _b in {'leq': 'le', 'geq': 'ge', 'neq': 'ne', 'to': 'rightarrow', 'gets': 'leftarrow',
               'circ': 'degree', 'ast': 'cdot', 'Longrightarrow': 'Rightarrow'}.items():
    SYMBOLS[_a] = SYMBOLS[_b]

_UNICODE = {'Γ': 'Gamma', 'Δ': 'Delta', 'Θ': 'Theta', 'Λ': 'Lambda', 'Ξ': 'Xi', 'Σ': 'Sigma',
            'Π': 'Pi', 'Φ': 'Phi', 'Ψ': 'Psi', 'Ω': 'Omega', 'α': 'alpha', 'β': 'beta',
            'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
            'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi',
            'ο': 'omicron', 'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
            'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega', 'ϑ': 'vartheta', 'ϕ': 'varphi',
            '×': 'times', '÷': 'div', '±': 'pm', '∓': 'mp', '≤': 'le', '≥': 'ge', '≠': 'ne',
            '≈': 'approx', '≡': 'equiv', '∞': 'infty', '∫': 'int', '√': 'sqrt', '∂': 'partial',
            '∇': 'nabla', '→': 'rightarrow', '←': 'leftarrow', '↑': 'uparrow', '↓': 'downarrow',
            '∝': 'propto', 'ħ': 'hbar', '·': 'cdot', '∀': 'forall', '∃': 'exists', '∈': 'in',
            '⊥': 'perp', '∥': 'parallel', '§': 'section', '†': 'dagger', '°': 'degree',
            '∼': 'sim', '≪': 'll', '≫': 'gg', '⟨': 'langle', '⟩': 'rangle'}

# characters in this font family follow EBCDIC but not any single standard code page
_ASCII_FIX = {'[': 173, ']': 189, '\\': 172, '^': 177, '~': 181, '`': 179, '{': 139,
              '}': 155, '|': 79, '!': 90, '¢': 74}


def _code_for(ch):
    """EBCDIC slot for one character; unmapped characters give '?'."""
    if ch in '−–—‐':       # unicode minus / dashes -> hyphen-minus
        return 96
    if ch in '   ':
        return 64
    if ch in _UNICODE:
        return SYMBOLS[_UNICODE[ch]]
    if ch in _ASCII_FIX:
        return _ASCII_FIX[ch]
    if ord(ch) < 128:
        try:
            return ch.encode('cp037')[0]
        except UnicodeEncodeError:
            return 111
    base = unicodedata.normalize('NFKD', ch)[:1]       # e-acute -> e
    if base and ord(base) < 128 and base != ch:
        return _code_for(base)
    return 111


# Public spelling used by the high-level API and by the character-map example.
code_for = _code_for
