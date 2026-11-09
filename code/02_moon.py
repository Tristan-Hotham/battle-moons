"""Step 2: the Moon and the Sun for every battle (astronomy-engine), and the null of random nights.

For each item (battles and sieges), at the battle site:
  * phase angle (the Moon's elongation from the Sun in ecliptic longitude: 0 new, 90 first quarter, 180 full, 270 last
    quarter), illuminated fraction and age in days since the last new moon, at local mean noon of the battle day;
  * the night before (local noon of the day before to local noon of the battle day), every STEP_MIN minutes: Sun and Moon
    altitude (topocentric, standard refraction). From these: sunset and sunrise, hours of darkness (Sun below -6 degrees,
    civil twilight), hours of darkness with the Moon up, moonlight (those hours times the illuminated fraction), moonrise
    and moonset, whether the Moon was up at sunrise.
For the null, each battle in the test set gets NULL_K random nights at the same site, in a random year of its own century and
within 15 days of the same date in the year (so the nights are as long as the battle's own), at NULL_STEP minutes.
Output: SCR/moon.json, SCR/null_nights.npz.  Run time about 10 minutes on two cores.
"""
import sys, time
import numpy as np
import astronomy as A
from multiprocessing import Pool
from common import *

J2000 = 2451545.0


def tnoon(J, lon):
    """astronomy Time at local mean noon of the day with Julian day number J (UT)"""
    return A.Time(J - J2000 - lon / 360.0)


def alts(t0, lon, lat, n, step_min):
    obs = A.Observer(lat, lon, 0)
    s = np.empty(n); m = np.empty(n)
    for i in range(n):
        t = t0.AddDays(i * step_min / 1440.0)
        e = A.Equator(A.Body.Sun, t, obs, True, True); s[i] = A.Horizon(t, obs, e.ra, e.dec, A.Refraction.Normal).altitude
        e = A.Equator(A.Body.Moon, t, obs, True, True); m[i] = A.Horizon(t, obs, e.ra, e.dec, A.Refraction.Normal).altitude
    return s, m


def crossings(a, thr, step_h):
    """times (hours from start) where a crosses thr upward (+1) or downward (-1)"""
    out = []
    for i in range(len(a) - 1):
        if (a[i] - thr) * (a[i + 1] - thr) < 0 or (a[i] == thr and a[i + 1] != thr):
            f = (thr - a[i]) / (a[i + 1] - a[i]); out.append(((i + f) * step_h, 1 if a[i + 1] > a[i] else -1))
    return out


def night(J, lon, lat, step_min):
    """the night before day J at (lon, lat): local noon of J-1 to local noon of J"""
    t0 = tnoon(J - 1, lon); n = int(24 * 60 / step_min) + 1; sh = step_min / 60.0
    s, m = alts(t0, lon, lat, n, step_min)
    tm = t0.AddDays(0.5)
    illum = A.Illumination(A.Body.Moon, tm).phase_fraction
    dark = s < -6.0
    up = m > -0.27
    w = np.ones(n); w[0] = w[-1] = 0.5                 # trapezoid weights
    dark_h = float((w * dark).sum() * sh)
    moon_dark_h = float((w * (dark & up)).sum() * sh)
    sun = crossings(s, -0.27, sh); moon = crossings(m, -0.27, sh)
    sunset = next((h for h, d in sun if d < 0), None)
    sunrise = next((h for h, d in sun[::-1] if d > 0), None)
    up_at_rise = bool(np.interp(sunrise / sh, np.arange(n), m) > -0.27) if sunrise is not None else None
    return {"dark_h": dark_h, "moon_dark_h": moon_dark_h, "moonlight": moon_dark_h * illum, "illum_mid": illum,
            "sunset": sunset, "sunrise": sunrise, "moonrise": [h for h, d in moon if d > 0], "moonset": [h for h, d in moon if d < 0],
            "moon_up_at_sunrise": up_at_rise, "moon_alt_mid": float(np.interp(12 / sh, np.arange(n), m)),
            "moon_up_frac": float((w * up).sum() / w.sum())}


def phase(J, lon):
    t = tnoon(J, lon)
    ph = A.MoonPhase(t)
    il = A.Illumination(A.Body.Moon, t).phase_fraction
    nm = A.SearchMoonPhase(0, t.AddDays(-(ph / 360 * SYNODIC) - 2.5), 5)
    fm = A.SearchMoonPhase(180, t.AddDays(-(((ph - 180) % 360) / 360 * SYNODIC) - 2.5), 5)
    fm2 = A.SearchMoonPhase(180, t.AddDays(-2.5), 40)
    dfull = min([t.ut - fm.ut, t.ut - fm2.ut], key=abs) if fm else None
    return {"phase": ph, "illum": il, "age": t.ut - nm.ut if nm else ph / 360 * SYNODIC, "dfull": dfull}


def work(b):
    r = {"q": b["q"]}
    r.update(phase(b["J"], b["lon"]))
    r.update(night(b["J"], b["lon"], b["lat"], STEP_MIN))
    return r


def work_null(args):
    J, lon, lat = args
    n = night(J, lon, lat, NULL_STEP)
    t = tnoon(J, lon)
    return (A.MoonPhase(t), n["dark_h"], n["moon_dark_h"], n["moonlight"], 1.0 if n["moon_up_at_sunrise"] else 0.0)


def in_test(b):
    return (not b["siege"]) and b["cal_ok"] and b["status"] == "ok"


if __name__ == "__main__":
    B = jload(f"{SCR}/battles.json")
    if "--sample" in sys.argv:
        B = B[:200]
    if "--null-only" not in sys.argv:
        t0 = time.time()
        with Pool(2) as pool:
            res = pool.map(work, B, chunksize=50)
        print("battles", len(res), round(time.time() - t0), "s")
        jsave(res, f"{SCR}/moon.json", keepdash=True)
    rng = np.random.default_rng(SEED)
    T = [b for b in B if in_test(b)]
    jobs, owner = [], []
    for i, b in enumerate(T):
        c0 = (b["y"] // 100) * 100
        doy = b["J"] - jdn_greg(b["y"], 1, 1)
        for k in range(NULL_K):
            yy = int(rng.integers(c0, min(c0 + 99, 2025) + 1))
            J = jdn_greg(yy, 1, 1) + doy + int(rng.integers(-15, 16))
            jobs.append((int(J), b["lon"], b["lat"])); owner.append(i)
    t0 = time.time()
    with Pool(2) as pool:
        nres = pool.map(work_null, jobs, chunksize=200)
    print("null nights", len(nres), round(time.time() - t0), "s")
    np.savez_compressed(f"{SCR}/null_nights.npz", owner=np.array(owner), J=np.array([j[0] for j in jobs]), res=np.array(nres),
                        q=np.array([b["q"] for b in T]))
