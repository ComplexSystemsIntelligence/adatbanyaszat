"""A GitHub-tároló közösségimédia-előnézeti képének (1280×640) előállítása.

Használat:  python scripts/make_social_preview.py   ->  assets/social-preview.png
A képet a tároló Settings → Social preview menüpontjában lehet feltölteni.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
BLUE = "#285780"


def fp(name: str, size: float) -> FontProperties:
    return FontProperties(fname=FONTS / name, size=size)


def main() -> None:
    fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1280)
    ax.set_ylim(0, 640)
    ax.axis("off")
    ax.add_patch(Polygon([[0, 0], [1280, 0], [1280, 150], [0, 92]], closed=True, color=BLUE))
    rng = np.random.default_rng(2026)
    for cx, cy, c in [(990, 440, "#285780"), (1130, 335, "#5f8fbf"), (935, 275, "#9bbbd9")]:
        p = rng.normal([cx, cy], [42, 34], size=(70, 2))
        ax.scatter(p[:, 0], p[:, 1], s=26, color=c, alpha=0.55, lw=0)
        ax.scatter([cx], [cy], s=150, marker="x", color=BLUE, lw=2.4, alpha=0.9)
    ax.text(80, 470, "Adatbányászat", fontproperties=fp("Raleway-Black.otf", 64), color=BLUE)
    ax.text(84, 405, "a hatékonyság eszköze", fontproperties=fp("IBMPlexSerif-Regular.otf", 34), color="#1d2733")
    ax.text(84, 335, "Elmélet és gyakorlat Pythonban", fontproperties=fp("IBMPlexSerif-Italic.otf", 24), color="#3a4654")
    ax.text(84, 295, "2., teljesen átdolgozott kiadás", fontproperties=fp("IBMPlexSans-Regular.otf", 20), color="#3a4654")
    ax.text(84, 205, "Abonyi János", fontproperties=fp("Raleway-Bold.otf", 27), color=BLUE)
    ax.text(84, 168, "Pannon Egyetem · Veszprém · 2026", fontproperties=fp("IBMPlexSans-Regular.otf", 18), color="#3a4654")
    ax.text(84, 40, "complexsystemsintelligence.github.io/adatbanyaszat",
            fontproperties=fp("IBMPlexSans-SemiBold.otf", 18), color="white")
    ax.text(1196, 40, "webkönyv · PDF · EPUB · Colab", fontproperties=fp("IBMPlexSans-Regular.otf", 16),
            color="white", ha="right")
    out = ROOT / "assets" / "social-preview.png"
    fig.savefig(out, dpi=100, facecolor="white")
    print("kész:", out)


if __name__ == "__main__":
    main()
