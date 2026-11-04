"""Specimen of the mathtext subset, legacy mode, font parameters and several fonts."""

from _common import IMAGES, plt, save, sf, setup

setup()

fig = plt.figure(figsize=(9, 7))
rows = [
    (r"Plain text, no math: x^2 and a_b stay literal; cost \$5", {}),
    (r"Inline $E = mc^2$ and $\alpha_i^{2} + \beta^{\mu\nu} \leq \infty$", {}),
    (r"$\frac{a+b}{c-d} = \sqrt{x^2+y^2} \pm \Delta\Omega\ \mathrm{GeV}/c^2$", {}),
    (r"$10^{-3}$  $\mathdefault{10^{2}}$  $\sin\theta\cos\phi$  $x_{i_j}^{k^2}$  $-5 + 3 \times 2$", {}),
    ("x" + sf.UP + "2" + sf.DOWN + " y" + sf.DOWN + "i" + sf.UP + " z" + sf.UP + "a"
     + sf.UPSIZE + "b" + sf.DOWNSIZE + sf.DOWN + "!  (legacy PSYM)", dict(markup='legacy')),
    ("Legacy backspace: A" + sf.BACKSPACE + "/ and Q" + sf.UP + "2" + sf.BACKSPACE
     + sf.DOWN + sf.DOWN + "1" + sf.UP, dict(markup='legacy')),
    (r"params SHGT=0.8 $x^2_i$ vs default $x^2_i$", dict(params={'SHGT': 0.8})),
]
y = 0.94
for text, kwargs in rows:
    fig.add_artist(sf.StrokeText(0.03, y, text, fontsize=15,
                                 transform=fig.transFigure, **kwargs))
    y -= 0.075

for k, font in enumerate(['TRIUMF.2', 'ROMAN.2', 'ITALIC.2', 'SANSERIF.2',
                          'HELVETICA.1', 'ROMAN.SWISSM']):
    fig.add_artist(sf.StrokeText(0.03, 0.36 - k * 0.06,
                                 font + r": The quick brown fox $x^2_i \alpha$",
                                 font=font, fontsize=14, transform=fig.transFigure))

save(fig, "markup.png", dpi=110)
print("wrote", IMAGES / "markup.png")
