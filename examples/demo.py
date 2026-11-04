"""Convert an existing figure's text to stroke fonts with ``stroke_texts``."""

from _common import IMAGES, np, plt, save, sf, setup

setup()

fig, ax = plt.subplots(figsize=(6, 4))
x = np.linspace(0, 10, 200)
ax.plot(x, np.sin(x) * np.exp(-x / 5))
ax.set_title(r"Damped oscillation  $e^{-t/\tau}\,\sin(\omega t)$")
ax.set_xlabel(r"time $t$ ($\mu$s)")
ax.set_ylabel(r"$\Delta V / V_{0}$")
ax.text(5, 0.6, "rotated 30\xb0", rotation=30, ha="center", va="center")
fig.canvas.draw()

sf.stroke_texts(fig, "TRIUMF.2")   # see demo_install.py for sf.use()

r = fig.canvas.get_renderer()
for t in fig.findobj(sf.StrokeText):
    b = t.get_window_extent(r)
    if b.height > 60 or b.width > 400:
        print(repr(t.get_text()), b.bounds)

fig.tight_layout()
for ext in ("png", "pdf", "svg"):
    save(fig, f"demo.{ext}", dpi=130, bbox_inches="tight")

print("wrote", IMAGES / "demo.png")
