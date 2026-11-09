"""Reddit collage (r/dataisbeautiful style), light parchment: the moon-phase wheel of all battles, and the Moon over twelve
famous battles. Builds on release/blog/b_wheel.png from code/05_figures.py. Output: reddit/battle_moons_collage.png (2700 x 3900)."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figstyle import *
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path as MPath
from PIL import Image

R = jload(f"{DATA}/results.json")
A, T = R["all"], R["T"]
B = os.path.join(ROOT, "release", "blog")
fig = plt.figure(figsize=(9, 13), dpi=300); parchment(fig, seed=8, alpha=0.05)
fig.text(0.05, 0.972, "Fighting by moonlight?", fontproperties=HAND, fontsize=36, color=RED, va="center")
fig.text(0.05, 0.947, f"The phase of the Moon on the day of {A['n']:,} battles with an exact date and place (Wikidata), against random",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")
fig.text(0.05, 0.933, f"days from the same centuries. Battles fall on every phase almost equally: the Moon was {T['illum_obs_pc']:.1f}% lit on the",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")
fig.text(0.05, 0.919, f"average battle day and {T['illum_exp_pc']:.1f}% on random days.", fontproperties=FELL, fontsize=11, color=INKC, va="center")
im = Image.open(f"{B}/b_wheel.png").convert("RGB"); w, h = im.size
im = im.crop((int(0.05 * w), int(0.15 * h), int(0.95 * w), int(0.975 * h)))
ax = fig.add_axes([0.06, 0.37, 0.88, 0.88 * 9 * (im.size[1] / im.size[0]) / 13]); ax.imshow(im); ax.axis("off")
# legend for the wheel
lg = fig.add_axes([0.05, 0.338, 0.9, 0.034]); lg.set_xlim(0, 100); lg.set_ylim(0, 2); lg.axis("off")
for k, c in enumerate(PCOL):
    lg.add_patch(plt.Rectangle((0.5 + k * 1.6, 1.25), 1.4, 0.5, fc=c, ec="none"))
lg.text(14.2, 1.5, "Bars: battles on each day of the Moon's age, coloured by phase, clockwise from new Moon", fontproperties=FELL, fontsize=9, color=INKC, va="center")
lg.plot([0.5, 13.1], [0.5, 0.5], ls=(0, (3, 2)), color=RED, lw=1.4)
lg.text(14.2, 0.5, "Dashed line: what random days from each battle's own century would give", fontproperties=FELL, fontsize=9, color=INKC, va="center")
fig.text(0.05, 0.322, "The Moon over twelve famous battles (at the battle site, modern calendar)", fontproperties=FELLSC, fontsize=13, color=RED, va="center")


def moon(ax, x, y, r, ph):
    ax.add_patch(Circle((x, y), r, fc="#3A3550", ec=INKC, lw=0.8, zorder=5))
    ph %= 360; t = np.linspace(-np.pi / 2, np.pi / 2, 60); side = 1 if ph < 180 else -1
    c = math.cos(math.radians(ph if ph < 180 else 360 - ph))
    v = np.vstack([np.c_[side * r * np.cos(t), r * np.sin(t)], np.c_[side * r * np.cos(t[::-1]) * c, r * np.sin(t[::-1])]]) + [x, y]
    ax.add_patch(PathPatch(MPath(np.vstack([v, v[:1]])), fc="#F7EBC4", ec="none", zorder=5.1))
    ax.add_patch(Circle((x, y), r, fc="none", ec=INKC, lw=0.8, zorder=5.2))


F = {f["name"]: f for f in R["famous"]}
pick = ["Pydna, 168 BC", "Hastings, 1066", "Agincourt, 1415", "La Noche Triste, 1520", "Naseby, 1645", "Trafalgar, 1805",
        "Waterloo, 1815", "Gettysburg, 1863", "Isandlwana, 1879", "The Somme, 1916", "Second El Alamein, 1942", "D-Day, 1944"]
g = fig.add_axes([0.03, 0.085, 0.94, 0.25]); g.set_xlim(0, 6); g.set_ylim(0, 2.2); g.set_aspect("equal"); g.axis("off")
for i, nm in enumerate(pick):
    f = F[nm]; x = 0.5 + (i % 6); y = 1.62 - (i // 6) * 1.08
    moon(g, x, y, 0.25, f["phase_ae"])
    g.text(x, y - 0.33, nm.split(",")[0], ha="center", va="top", fontproperties=FELL, fontsize=10.5, color=INKC)
    g.text(x, y - 0.47, f"{f['date'].replace(' (Gregorian)', '')}", ha="center", va="top", fontproperties=FELL, fontsize=8.5, color=MUT)
    g.text(x, y - 0.59, f"{f['phase_name'].lower()}, {round(100 * f['illum_ae'])}% lit", ha="center", va="top", fontproperties=FELLIT, fontsize=8.5, color=INKC)
fig.text(0.05, 0.048, f"Julian dates converted ({R['n']['reflagged_all']} pre-1582 dates had the wrong calendar flag). Pydna (lunar eclipse the night before) and Isandlwana (solar eclipse) check out.",
         fontproperties=FELL, fontsize=9, color=INKC, va="center")
fig.text(0.05, 0.022, "Data: Wikidata (CC0) via QLever. Moon: astronomy-engine, checked with PyEphem. Null: 2,000 sets of random days.   maps.tristanhotham.com/battle-moons",
         fontproperties=FELL, fontsize=8, color=MUT)
fig.savefig(os.path.join(ROOT, "reddit", "battle_moons_collage.png"), dpi=300, facecolor=fig.get_facecolor())
print(Image.open(os.path.join(ROOT, "reddit", "battle_moons_collage.png")).size)
