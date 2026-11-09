"""Shared paths, constants and helpers for the battle-moons study ("Fighting by moonlight").

Inputs (read in place, never modified):
  RAW/battles_p585.tsv.gz, battles_p580.tsv.gz  Wikidata battles (Q178561 and subclasses) with a point in time (P585) or start
                                                time (P580) at day precision: value (already proleptic Gregorian in the RDF),
                                                precision, calendar model as entered (Q1985727 Gregorian, Q1985786 Julian),
                                                coordinates (P625) or the coordinates of the location (P276), war, sitelinks.
  RAW/sieges_p585.tsv.gz, sieges_p580.tsv.gz    the same for sieges (Q188055 and subclasses): kept apart, a siege lasts weeks.
  GEO/ne_50m_land.geojson etc.                  Natural Earth outlines for the static figures.
Moon and Sun: astronomy-engine (Don Cross, MIT licence), computed on the fly; no data download.
Intermediates go to SCR, outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("BM_RAW", "/home/claude/newdata/raw_new10")
GEO = os.environ.get("BM_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("BM_FONTS", "/home/claude/ref/fonts")
INK = os.environ.get("BM_INK", "/home/claude/studies/ink-map")
INKFONTS = os.path.join(INK, "fonts", "ttf")
SCR = os.environ.get("BM_SCRATCH", "/home/claude/scratch/battle-moons")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "battle-moons"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
GREG = "Q1985727"
JUL = "Q1985786"
SYNODIC = 29.530589
STEP_MIN = 10              # minutes between Sun and Moon positions through the night
NULL_K = 10                # random nights per battle for the moonlight null
NULL_STEP = 30             # minutes between positions for the null nights
NULL_PHASE_REPS = 2000     # simulated data sets for the phase tests
SEED = 20261109
ERAS = [("medieval", "Before 1500", -3000, 1499), ("early", "1500 to 1799", 1500, 1799),
        ("c19", "1800 to 1899", 1800, 1899), ("ww", "1900 to 1945", 1900, 1945), ("modern", "1946 to 2026", 1946, 2026)]
# eight phase bins centred on the named phases (phase angle = Moon's elongation from the Sun, 0 new, 180 full)
PHASES = ["New moon", "Waxing crescent", "First quarter", "Waxing gibbous", "Full moon", "Waning gibbous", "Last quarter", "Waning crescent"]


def phase_bin(angle):
    return int(((angle + 22.5) % 360) // 45)


def era_of(year):
    for k, _, a, b in ERAS:
        if a <= year <= b:
            return k
    return None


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "p": return pval(v)
    if f == "f0": return f"{round(float(v))}"
    if f == "pc_frac": return f"{round(float(v) * 100)}%"
    if f == "pc_frac1": return f"{float(v) * 100:.1f}%"
    raise ValueError(f)


def pval(p):
    p = float(p)
    if p < 0.001: return "below 0.001"
    if p < 0.01: return f"{p:.3f}"
    return f"{p:.2f}"


# ---------- calendars: Julian day numbers for proleptic Gregorian and Julian dates (astronomical years: 0 = 1 BC)
def jdn_greg(y, m, d):
    a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def jdn_jul(y, m, d):
    a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083


def greg_from_jdn(J):
    a = J + 32044; b = (4 * a + 3) // 146097; c = a - 146097 * b // 4
    d = (4 * c + 3) // 1461; e = c - 1461 * d // 4; m = (5 * e + 2) // 153
    return 100 * b + d - 4800 + m // 10, m + 3 - 12 * (m // 10), e - (153 * m + 2) // 5 + 1


def jul_from_jdn(J):
    c = J + 32082; d = (4 * c + 3) // 1461; e = c - 1461 * d // 4; m = (5 * e + 2) // 153
    return d - 4800 + m // 10, m + 3 - 12 * (m // 10), e - (153 * m + 2) // 5 + 1


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def year_text(y):
    return f"{y}" if y > 0 else f"{1 - y} BC"


def date_text(y, m, d):
    return f"{d} {MONTHS[m - 1]} {year_text(y)}"


def fast_phase(jd_ut):
    """Moon's phase angle (elongation, degrees, 0 new, 180 full) from Meeus, Astronomical Algorithms, ch. 47 to 48 (mean
    elements with the six largest terms of the phase angle i, eq. 48.4). Accurate to about a degree; used only for the
    random-date null, and checked against astronomy-engine in 04_results.py."""
    import numpy as np
    T = (np.asarray(jd_ut, float) - 2451545.0) / 36525.0
    r = np.radians
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2 + T ** 3 / 545868.0
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2 + T ** 3 / 69699.0
    i = (180 - D - 6.289 * np.sin(r(Mp)) + 2.100 * np.sin(r(M)) - 1.274 * np.sin(r(2 * D - Mp)) - 0.658 * np.sin(r(2 * D))
         - 0.214 * np.sin(r(2 * Mp)) - 0.110 * np.sin(r(D)))
    return (180 - i) % 360


# phase colours, a cycle: dark at new moon, gold at full, cool while waxing, warm while waning (page, figures, collage)
PCOL = ["#232046", "#3A5A97", "#4E8DB6", "#8CC0BB", "#F0C24B", "#D46A35", "#B04E8E", "#563575"]
