"""Legend with title, multi-line entries, Greek letters and sub/superscripts."""

from _common import IMAGES, np, plt, save, sf, setup

setup()

fig, ax = plt.subplots(figsize=(6, 4))
x = np.linspace(0, 10, 200)
ax.plot(x, np.sin(x), label=r"$\alpha = 1$, $\sin x$")
ax.plot(x, np.cos(x), '--', label=r"$x^2_i$ multi" + "\nline")
ax.plot(x, np.sin(x) * np.cos(x), 'o', ms=2, label=r"$\Delta E$ ($\mu$eV)")
ax.legend(title=r"Series $\beta$", loc='upper right', ncol=1)
fig.legend(loc='lower left', ncol=3, labels=['a', 'b', 'c'], handles=ax.lines[:3])
fig.canvas.draw()
sf.stroke_texts(fig, 'TRIUMF.2')
fig.tight_layout()
save(fig, "demo_legend.png", dpi=130, bbox_inches='tight')
save(fig, "demo_legend.pdf")

print("wrote", IMAGES / "demo_legend.png")
