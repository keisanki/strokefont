"""Drop-in use: an ordinary matplotlib script, wrapped in sf.use(); nothing else changes."""

from collections import Counter

import matplotlib
from _common import IMAGES, np, plt, save, sf, setup

setup()

with sf.use("TRIUMF.2"):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    x = np.logspace(-1, 3, 200)
    a1.loglog(x, x**-1.5 * 1e3, label=r"$N \propto E^{-3/2}$")
    a1.loglog(x, 50 / (1 + (x / 30) ** 2), label=r"$\frac{50}{1+(E/30)^2}$")
    a1.set_xlabel(r"Energy $E$ (MeV)")
    a1.set_ylabel(r"Counts / $\mu$A$\cdot$s")
    a1.set_title(r"Log axes: $\mathdefault{10^{n}}$ ticks")
    a1.legend(title="Fits")
    a1.annotate("plain annotation", (10, 20))        # Annotation keeps the normal font
    im = a2.imshow(np.random.default_rng(1).normal(size=(20, 20)) * 1e4, cmap='viridis')
    cb = fig.colorbar(im, ax=a2)
    cb.set_label(r"$\sigma$ (arb.)")
    a2.set_title(r"Offset text & colour bar")
    a2.set_xlabel("x")
    a2.set_ylabel("y")
    fig.suptitle(r"Drop-in: $\alpha$, $\beta^2$, ordinary \texttt{plt} calls")
    fig.tight_layout()
    save(fig, "install.png", dpi=110)
    save(fig, "install.pdf")
    save(fig, "install.svg")

    print(Counter(type(t).__name__ for t in fig.findobj(matplotlib.text.Text)))

print("wrote", IMAGES / "install.png")
