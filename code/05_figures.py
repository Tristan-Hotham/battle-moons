"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png), the paper (release/paper/f_*.png), and header.png."""
import csv
import numpy as np
from PIL import Image
import matplotlib.patheffects as pe
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path as MPath
from figstyle import *

R = jload(f"{DATA}/results.json")
B = list(csv.DictReader(open(f"{DATA}/battles.csv", encoding="utf-8")))
BLOG, PAPERD = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (BLOG, PAPERD):
    os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
DARKM, LITM = "#3A3550", "#F7EBC4"


def out(fig, name, page=True, blog=True, paper=True, dpi=200):
    fig.savefig(f"{SCR}/{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=84, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        w = min(2000, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{PAPERD}/f_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def moon(ax, x, y, r, phase, transform=None, z=5, edge=INKC, lw=0.8):
    """the Moon as seen from the northern hemisphere at a phase angle (0 new, 180 full; waxing lit on the right)"""
    tr = transform or ax.transData
    ax.add_patch(Circle((x, y), r, fc=DARKM, ec=edge, lw=lw, transform=tr, zorder=z))
    ph = phase % 360
    t = np.linspace(-np.pi / 2, np.pi / 2, 60)
    side = 1 if ph < 180 else -1
    c = math.cos(math.radians(ph if ph < 180 else 360 - ph))
    limb = np.c_[side * r * np.cos(t), r * np.sin(t)]
    term = np.c_[side * r * np.cos(t[::-1]) * c, r * np.sin(t[::-1])]
    v = np.vstack([limb, term, limb[:1]]) + [x, y]
    ax.add_patch(PathPatch(MPath(v), fc=LITM, ec="none", transform=tr, zorder=z + 0.1))
    ax.add_patch(Circle((x, y), r, fc="none", ec=edge, lw=lw, transform=tr, zorder=z + 0.2))


A = R["all"]
# ---------- 1. the wheel: battles by age of the Moon, against random days
fig = plt.figure(figsize=(12, 12)); parchment(fig)
ax = fig.add_axes([0.18, 0.11, 0.64, 0.64], projection="polar")
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
obs = np.array(R["age_hist"], float); nul = np.array(R["age_hist_null"], float)
# the last bin is only part of a day (the synodic month is 29.53 days): show counts per full day of age
width = np.ones(30); width[29] = SYNODIC - 29
rate, nrate = obs / width, nul / width
th = (np.arange(30) + width / 2) / SYNODIC * 2 * np.pi
for i in range(30):
    col = PCOL[phase_bin((i + 0.5) / SYNODIC * 360)]
    ax.bar(th[i], rate[i], width=width[i] / SYNODIC * 2 * np.pi * 0.86, bottom=0, color=col, edgecolor=INKC, lw=0.5, alpha=0.95, zorder=3)
tt = np.r_[th, th[0] + 2 * np.pi]; nn = np.r_[nrate, nrate[0]]
ax.plot(tt, nn, color=RED, lw=1.8, ls=(0, (4, 2)), zorder=4)
ax.set_ylim(0, rate.max() * 1.18)
ax.set_xticks([]); ax.set_yticks([])
ax.spines["polar"].set_color(INKC); ax.set_facecolor("none")
ax.grid(False)
for v in (100, 200, 300):
    ax.plot(np.linspace(0, 2 * np.pi, 200), np.full(200, v), color=MUT, lw=0.4, alpha=0.5, zorder=1)
    ax.text(np.radians(4), v, f"{v}", fontproperties=FELL, fontsize=10, color=MUT, va="bottom", zorder=6, path_effects=HALO)
lab = ["New moon", "First quarter", "Full moon", "Last quarter"]
mx = fig.add_axes([0, 0, 1, 1], zorder=10); mx.set_xlim(0, 1); mx.set_ylim(0, 1); mx.axis("off")
for k in range(8):
    a = math.radians(k * 45)
    cx, cy = 0.5 + 0.372 * math.sin(a), 0.43 + 0.372 * math.cos(a)
    moon(mx, cx, cy, 0.024, k * 45)
    if k % 2 == 0:
        if k in (0, 4):
            mx.text(cx + 0.034, cy, lab[k // 2], fontproperties=FELLSC, fontsize=15, color=INKC, ha="left", va="center", path_effects=HALO)
        else:
            mx.text(cx, cy - 0.04, lab[k // 2], fontproperties=FELLSC, fontsize=15, color=INKC, ha="center", va="top", path_effects=HALO)
fig.text(0.04, 0.965, "Fighting by moonlight?", fontproperties=HAND, fontsize=34, color=RED, va="center")
fig.text(0.04, 0.932, f"{A['n']:,} dated battles from Wikidata by the age of the Moon on the day (bars: battles per day of the lunar month);",
         fontproperties=FELL, fontsize=14, color=INKC, va="center")
fig.text(0.04, 0.910, "dashed red line: what random days from each battle's own century would give. The two are almost the same.",
         fontproperties=FELL, fontsize=14, color=INKC, va="center")
fig.text(0.04, 0.012, f"Moon at local noon of the battle day, at the battle site (astronomy-engine). Julian dates converted. Mean lit fraction {A['mean_illum']*100:.1f}% against {A['mean_illum_exp']*100:.1f}% for random days.",
         fontproperties=FELL, fontsize=11.5, color=MUT)
out(fig, "wheel")

# ---------- 2. by era: observed against expected in each phase
eras = [k for k, *_ in ERAS if k in R["eras"]]
EP = [R["eras"][k] for k in eras] + [dict(R["all"], name="All battles")]
fig = plt.figure(figsize=(14, 8.6)); parchment(fig)
fig.text(0.04, 0.955, "No era shows a clear lunar rhythm", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.917, "Battles in each phase of the Moon as a share of what random days in the same centuries would give (100 = as expected); bars show the 95% range of chance",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
for i, E in enumerate(EP):
    ax = fig.add_axes([0.06 + (i % 3) * 0.315, 0.53 - (i // 3) * 0.42, 0.27, 0.30])
    o = np.array(E["obs"], float); e = np.array(E["exp"]); sd = np.array(E["exp_sd"])
    idx = 100 * o / e; lo = 100 * (e - 1.96 * sd) / e; hi = 100 * (e + 1.96 * sd) / e
    ax.fill_between(np.arange(8), lo, hi, step="mid", color="#D9C9A3", alpha=0.7, lw=0, zorder=1)
    ax.axhline(100, color=INKC, lw=0.8, zorder=2)
    ax.bar(np.arange(8), idx - 100, bottom=100, color=PCOL, edgecolor=INKC, lw=0.5, width=0.72, zorder=3)
    ax.set_ylim(55, 145); ax.set_xlim(-0.6, 7.6)
    ax.set_xticks([]); ax.set_yticks([60, 80, 100, 120, 140])
    ax.tick_params(labelsize=10)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.set_title(f"{E['name']}", fontproperties=HAND, fontsize=17, color=RED, loc="left", pad=20)
    ax.text(0, 1.02, f"{E['n']:,} battles; chance of a pattern this strong or more: {pval(E['chi2_p_sim'])}", transform=ax.transAxes, fontproperties=FELL, fontsize=10.5, color=INKC, va="bottom")
    mx2 = ax.inset_axes([0, -0.2, 1, 0.16]); mx2.set_xlim(-0.6, 7.6); mx2.set_ylim(-1, 1); mx2.axis("off"); mx2.set_aspect("equal", adjustable="datalim")
    for j in range(8):
        moon(mx2, j, 0, 0.33, j * 45, lw=0.5)
fig.text(0.04, 0.03, "Phases in eight equal parts of the lunar month, from new moon (left) through full (centre) to the last crescent. Null: 2,000 simulated sets of random days.",
         fontproperties=FELL, fontsize=11.5, color=MUT)
out(fig, "eras")

# ---------- 3. famous battles and their moons
F = R["famous"]
fig = plt.figure(figsize=(14, 0.62 * len(F) + 2.2)); parchment(fig)
H = 0.62 * len(F) + 2.2
fig.text(0.04, 1 - 0.55 / H, "The Moon over some famous battles", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 1 - 1.0 / H, "At the battle site on the day (Gregorian dates; Julian ones converted), with the hours of darkness the night before when the Moon was up",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.03, 0.03, 0.94, 1 - 1.55 / H - 0.03]); ax.set_xlim(0, 100); ax.set_ylim(len(F) - 0.5, -0.8); ax.axis("off")
ax.set_aspect("auto")
for k, (x, t) in enumerate([(1, "Battle"), (30, "Date"), (57, "Moon"), (61, "Phase"), (79, "Moon up in the dark, night before")]):
    ax.text(x, -0.55, t, fontproperties=FELLSC, fontsize=13, color=RED, va="center", ha="center" if t == "Moon" else "left")
yr = 0.62
for i, f in enumerate(F):
    ax.plot([0, 100], [i + 0.5, i + 0.5], color=MUT, lw=0.3, alpha=0.5)
    ax.text(1, i, f["name"].rsplit(",", 1)[0], fontproperties=FELL, fontsize=13.5, color=INKC, va="center")
    ax.text(30, i, f["date"].replace(" (Gregorian)", ""), fontproperties=FELL, fontsize=12.5, color=INKC, va="center")
# moons need equal aspect: an overlay axis in figure fraction
ov = fig.add_axes([0, 0, 1, 1], zorder=5); ov.set_xlim(0, 14); ov.set_ylim(0, H); ov.axis("off")
for i, f in enumerate(F):
    fx, fy = fig.transFigure.inverted().transform(ax.transData.transform((57, i)))
    moon(ov, fx * 14, fy * H, 0.21, f["phase_ae"], lw=0.6)
    d = f["days_from_full_ae"]
    ptxt = f"{f['phase_name']}, {round(f['illum_ae'] * 100)}% lit"
    ax.text(61, i, ptxt, fontproperties=FELL, fontsize=12.5, color=INKC, va="center")
    frac = f["moon_dark_h"] / f["dark_h"] if f["dark_h"] else 0
    ax.add_patch(plt.Rectangle((79, i - 0.18), 14 * 1.0, 0.36, fc="#2F2A45", ec=INKC, lw=0.5))
    ax.add_patch(plt.Rectangle((79, i - 0.18), 14 * frac, 0.36, fc="#F0C24B", ec="none"))
    ax.text(94, i, f"{f['moon_dark_h']:.0f} of {f['dark_h']:.0f} h", fontproperties=FELL, fontsize=11.5, color=INKC, va="center")
out(fig, "famous")

# ---------- 4. map of Europe and the Mediterranean, battles coloured by phase
T = [b for b in B if b["in_test"] == "True"]
crs = "+proj=laea +lat_0=48 +lon_0=12 +datum=WGS84 +units=m"
fig = plt.figure(figsize=(14, 11)); parchment(fig)
ax = fig.add_axes([0.02, 0.06, 0.96, 0.84])
ext, f = ink_base(ax, crs, (-13, 44, 30, 63), ripple_m=(12e3, 30e3), coast_lw=0.6)
xs, ys = f(np.array([float(b["lon"]) for b in T]), np.array([float(b["lat"]) for b in T]))
cols = [PCOL[PHASES.index(b["phase_name"])] for b in T]
ax.scatter(xs, ys, s=11, c=cols, edgecolors=INKC, linewidths=0.25, zorder=6, alpha=0.95)
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
fig.text(0.04, 0.955, "A map with no tides of the Moon in it", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.922, "Dated battles in Europe and around the Mediterranean, coloured by the phase of the Moon on the day", fontproperties=FELL, fontsize=13, color=MUT, va="center")
lx = fig.add_axes([0.02, 0.005, 0.96, 0.05]); lx.set_xlim(0, 100); lx.set_ylim(-1, 1); lx.axis("off"); lx.set_aspect("equal", adjustable="datalim")
for j in range(8):
    x = 4 + j * 12
    lx.scatter([x], [0], s=60, c=[PCOL[j]], edgecolors=INKC, linewidths=0.5)
    lx.text(x + 1.2, 0, PHASES[j], fontproperties=FELL, fontsize=12, color=INKC, va="center")
out(fig, "map")

# ---------- 5. the night before: darkness and moonlight, battles against season-matched random nights
fig = plt.figure(figsize=(14, 7.2)); parchment(fig)
fig.text(0.04, 0.95, "Moonlight on the night before", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 0.905, "Average hours of darkness with the Moon up, the night before each battle, against random nights at the same place and season in the same century",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.08, 0.16, 0.88, 0.65])
names = [R["eras"][k]["name"] for k in eras] + ["All"]
ob = [R["eras"][k]["night"]["moon_dark_h"]["obs"] for k in eras] + [R["night"]["moon_dark_h"]["obs"]]
nu = [R["eras"][k]["night"]["moon_dark_h"]["null"] for k in eras] + [R["night"]["moon_dark_h"]["null"]]
se = [R["eras"][k]["night"]["moon_dark_h"]["se"] for k in eras] + [R["night"]["moon_dark_h"]["se"]]
x = np.arange(len(names))
ax.bar(x - 0.19, nu, width=0.36, color="#D9C9A3", edgecolor=INKC, lw=0.5, label="random nights, same place and season")
ax.bar(x + 0.19, ob, width=0.36, color="#F0C24B", edgecolor=INKC, lw=0.5, label="the night before the battle")
ax.errorbar(x + 0.19, ob, yerr=1.96 * np.array(se), fmt="none", ecolor=INKC, lw=1, capsize=3)
ax.set_xticks(x); ax.set_xticklabels(names, fontproperties=FELL, fontsize=13)
ax.set_ylabel("hours", fontproperties=FELL, fontsize=13)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(prop=FELL, frameon=False, fontsize=12, loc="upper left")
for i in range(len(names)):
    ax.text(x[i] + 0.19, ob[i] + 1.96 * se[i] + 0.12, f"{ob[i]:.1f}", ha="center", fontproperties=FELL, fontsize=11, color=INKC)
fig.text(0.04, 0.03, "Darkness: the Sun more than 6 degrees below the horizon. Moon up: its upper edge above the horizon, with refraction. Bars: 95% confidence intervals.",
         fontproperties=FELL, fontsize=11.5, color=MUT)
out(fig, "night")

# ---------- 6. groups: mean lit fraction against chance
G = [("All battles", R["all"])] + [(R["eras"][k]["name"], R["eras"][k]) for k in eras] + \
    [(R["kinds"][k]["name"], R["kinds"][k]) for k in ("land", "sea", "raid", "ww1", "ww2", "famous") if k in R["kinds"]] + [("Sieges (start date)", R["sieges"])]
fig = plt.figure(figsize=(13, 0.5 * len(G) + 2.4)); parchment(fig)
Hh = 0.5 * len(G) + 2.4
fig.text(0.04, 1 - 0.5 / Hh, "How bright was the Moon on battle days?", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.04, 1 - 0.95 / Hh, "Average share of the Moon's disc lit, by group; the band is the 95% range for random days from the same centuries",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.40, 0.9 / Hh, 0.55, 1 - 2.2 / Hh])
for i, (nm, g) in enumerate(G):
    m0, sd = g["mean_illum_exp"] * 100, g["mean_illum_null_sd"] * 100
    ax.add_patch(plt.Rectangle((m0 - 1.96 * sd, i - 0.3), 3.92 * sd, 0.6, fc="#D9C9A3", ec="none", alpha=0.8))
    ax.plot([m0, m0], [i - 0.3, i + 0.3], color=MUT, lw=0.8)
    ax.scatter([g["mean_illum"] * 100], [i], s=70, c=["#F0C24B"], edgecolors=INKC, linewidths=0.8, zorder=5)
    fig.text(0.39, (0.9 + (1 - 2.2 / Hh) * Hh * (len(G) - 0.5 - i) / len(G)) / Hh, f"{nm} ({g['n']:,})", fontproperties=FELL, fontsize=12.5, color=INKC, ha="right", va="center")
ax.set_ylim(len(G) - 0.5, -0.5); ax.set_yticks([])
ax.set_xlim(35, 65); ax.axvline(50, color=INKC, lw=0.5, ls=":")
ax.set_xlabel("per cent of the disc lit, on average", fontproperties=FELL, fontsize=12.5)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
out(fig, "groups")

# ---------- 7. the calendar: what ten days do to the Moon (Naseby, 1645)
fig = plt.figure(figsize=(14, 5.4)); parchment(fig)
fig.text(0.04, 0.92, "Why the calendar matters: Naseby, June 1645", fontproperties=FELL, fontsize=24, color=INKC, va="center")
import astronomy as AE
_pw = PHASES[phase_bin(AE.MoonPhase(AE.Time(jdn_greg(1645, 6, 14) - 2451545.0 + 1 / 360)))].lower()
_pr = PHASES[phase_bin(AE.MoonPhase(AE.Time(jdn_greg(1645, 6, 24) - 2451545.0 + 1 / 360)))].lower()
assert _pr == "new moon"
fig.text(0.04, 0.83, f"England still kept the Julian calendar. Read as a Gregorian date, Wikidata's 14 June puts a {_pw} over the battle; the real day, 24 June in the",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
fig.text(0.04, 0.775, "modern calendar, had a new moon. Ten days move the Moon a third of the way round its cycle.", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.03, 0.08, 0.94, 0.6]); ax.set_xlim(-0.8, 21.8); ax.set_ylim(-1.6, 1.4); ax.set_aspect("equal"); ax.axis("off")
import astronomy as AE
J0 = jdn_greg(1645, 6, 10)
for i in range(22):
    J = J0 + i
    ph = AE.MoonPhase(AE.Time(J - 2451545.0 + 1 / 360))
    moon(ax, i, 0, 0.36, ph, lw=0.5)
    gy, gm, gd = greg_from_jdn(J)
    ax.text(i, -0.62, f"{gd}", ha="center", fontproperties=FELL, fontsize=11.5, color=INKC)
    if gd in (10, 1):
        ax.text(i, -0.95, MONTHS[gm - 1], ha="center", fontproperties=FELLIT, fontsize=11, color=MUT)
for J, txt, col in ((jdn_greg(1645, 6, 14), "Wikidata's date\nread as Gregorian", MUT), (jdn_greg(1645, 6, 24), "the battle:\n14 June Old Style", RED)):
    i = J - J0
    ax.add_patch(plt.Rectangle((i - 0.48, -0.78), 0.96, 1.62, fc="none", ec=col, lw=1.6))
    ax.text(i, 0.95, txt, ha="center", va="bottom", fontproperties=FELL, fontsize=12, color=col)
ax.text(-0.6, -1.35, "Days in the modern (Gregorian) calendar", fontproperties=FELLIT, fontsize=11, color=MUT)
out(fig, "calendar")

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3)); parchment(fig)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 12); ax.set_ylim(0, 6.3); ax.axis("off")
ax.text(0.6, 4.75, "Fighting by", fontproperties=FELL, fontsize=50, color=INKC, va="center")
ax.text(0.6, 3.75, "moonlight", fontproperties=HAND, fontsize=64, color=RED, va="center")
ax.text(0.62, 2.75, f"The Moon over {A['n']:,} battles, from Hastings to D-Day.", fontproperties=FELL, fontsize=17, color=INKC, va="center")
ax.text(0.62, 2.30, "Did commanders time their fights by it?", fontproperties=FELL, fontsize=17, color=INKC, va="center")
ax.text(0.62, 0.55, "maps.tristanhotham.com/battle-moons", fontproperties=FELL, fontsize=13, color=MUT, va="center")
for k in range(8):
    a = math.radians(k * 45 + 22.5)
    moon(ax, 9.2 + 1.85 * math.sin(a), 3.25 + 1.85 * math.cos(a), 0.42, k * 45 + 22.5, lw=0.9)
ax.text(9.2, 3.25, "every phase\nabout equally", ha="center", va="center", fontproperties=FELLIT, fontsize=15, color=INKC)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
