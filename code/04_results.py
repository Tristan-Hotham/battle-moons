"""Step 4: the tests and every number for the texts. Output: data/results.json, data/battles.csv, data/null_expectation.csv.

Test set: battles (not sieges) with a single day (or dates within three days), a point, and a settled calendar.
Null: phases of random days from each battle's own century, at the battle site (the fast Meeus phase, checked here against
astronomy-engine on the null nights from step 2); moonlight from those null nights (astronomy-engine).
"""
import csv
from collections import Counter, defaultdict
import numpy as np
from scipy import stats
from common import *

B = jload(f"{SCR}/battles.json")
MO = {m["q"]: m for m in jload(f"{SCR}/moon.json")}
NZ = np.load(f"{SCR}/null_nights.npz")
FAM = jload(f"{SCR}/famous.json")
rng = np.random.default_rng(SEED + 1)
for b in B:
    b.update({k: v for k, v in MO[b["q"]].items() if k != "q"})
    b["era"] = era_of(b["y"])
    b["bin"] = phase_bin(b["phase"])


def in_test(b):
    return (not b["siege"]) and b["cal_ok"] and b["status"] == "ok"


T = [b for b in B if in_test(b)]
qi = {q: i for i, q in enumerate(NZ["q"])}
assert len(qi) == len(T) and all(b["q"] in qi for b in T)
R = {"n": {"items": len(B), "rows": None}}
cnt = Counter()
for b in B:
    if b["siege"]: cnt["siege"] += 1
    elif b["status"] != "ok": cnt["ambiguous"] += 1
    elif not b["cal_ok"]: cnt["cal_" + b["fix"]] += 1
    else: cnt["test"] += 1
R["n"].update({"battles": sum(1 for b in B if not b["siege"]), "sieges": cnt["siege"], "test": len(T), "ambiguous": cnt["ambiguous"],
               "ancient": cnt["cal_ancient"], "os_uncertain": cnt["cal_os_uncertain"],
               "reflagged": sum(1 for b in T if b["fix"] == "reflagged"), "julian": sum(1 for b in T if b["fix"] == "julian"),
               "os_override": sum(1 for b in T if b["fix"] in ("os_override", "date_override")), "os_checked": sum(1 for b in T if b["fix"] == "os_checked"),
               "point_location": sum(1 for b in T if b["psrc"] == "location"), "sea": sum(1 for b in T if b["sea"]),
               "first_year": min(b["y"] for b in T), "since1800": sum(1 for b in T if b["y"] >= 1800)})
R["n"]["since1800_pc"] = 100 * R["n"]["since1800"] / len(T)
R["n"]["reflagged_all"] = sum(1 for b in B if b["fix"] == "reflagged")
# British Old Style dates settled by hand: converted from Old Style, or confirmed as correctly converted (Kosovo is counted apart)
R["n"]["os_hand"] = sum(1 for b in T if b["fix"] in ("os_override", "os_checked"))
R["n"]["date_override"] = sum(1 for b in T if b["fix"] == "date_override")
S01 = jload(f"{SCR}/stats01.json")
R["n"]["no_point"] = S01["no_point"]
R["n"]["no_day"] = None
R["n"]["wikidata_items"] = S01["items"]
print(R["n"])

# ---------- the null for phases: random days in each battle's own century at local noon of the site
def century_bounds(y):
    c0 = (y // 100) * 100
    return jdn_greg(c0, 1, 1), min(jdn_greg(c0 + 99, 12, 31), jdn_greg(2025, 12, 31))


# check the fast phase against astronomy-engine on the null nights
res = NZ["res"]
lon_of = np.array([T[i]["lon"] for i in NZ["owner"]])
fp = fast_phase(NZ["J"] - lon_of / 360.0)
dd = np.abs((fp - res[:, 0] + 180) % 360 - 180)
R["fast_phase_check"] = {"n": int(len(dd)), "median_deg": float(np.median(dd)), "p99_deg": float(np.percentile(dd, 99)), "max_deg": float(dd.max()),
                         "bin_agree_pc": float(100 * np.mean([phase_bin(a) == phase_bin(b) for a, b in zip(fp, res[:, 0])]))}
print("fast phase vs astronomy-engine", R["fast_phase_check"])
assert R["fast_phase_check"]["p99_deg"] < 3


def null_phases(sub, reps=NULL_PHASE_REPS, season=False):
    """phase angles of random days in each battle's century (season=True: also within 15 days of its date in the year)"""
    lon = np.array([b["lon"] for b in sub])
    if season:
        c0 = np.array([(b["y"] // 100) * 100 for b in sub]); c1 = np.minimum(c0 + 99, 2025)
        yy = c0[None, :] + np.floor(rng.random((reps, len(sub))) * (c1 - c0 + 1)[None, :]).astype(int)
        doy = np.array([b["J"] - jdn_greg(b["y"], 1, 1) for b in sub])
        jan1 = jdn_greg(yy, 1, 1)
        J = jan1 + doy[None, :] + rng.integers(-15, 16, (reps, len(sub)))
    else:
        lo = np.array([century_bounds(b["y"])[0] for b in sub]); hi = np.array([century_bounds(b["y"])[1] for b in sub])
        J = lo[None, :] + np.floor(rng.random((reps, len(sub))) * (hi - lo + 1)[None, :])
    return fast_phase(J - lon[None, :] / 360.0)


def phase_tests(sub, reps=NULL_PHASE_REPS, season=False):
    th = np.radians([b["phase"] for b in sub]); n = len(sub)
    obs = np.bincount([b["bin"] for b in sub], minlength=8)
    NP = null_phases(sub, reps, season)
    nb = ((NP + 22.5) % 360 // 45).astype(int)
    ncount = np.stack([np.bincount(r, minlength=8) for r in nb])
    exp = ncount.mean(0)
    chi = float(((obs - exp) ** 2 / exp).sum())
    chin = ((ncount - exp) ** 2 / exp).sum(1)
    def R1(t, k=1): return np.abs(np.exp(1j * k * t).mean(-1))
    r1 = float(R1(th)); r1n = R1(np.radians(NP)); r2 = float(R1(th, 2)); r2n = R1(np.radians(NP), 2)
    mean_dir = float(np.degrees(np.angle(np.exp(1j * th).mean())) % 360)
    nf = sum(1 for b in sub if abs(b["dfull"]) <= 1.5)
    nfn = (np.abs((NP - 180 + 180) % 360 - 180) <= 1.5 / SYNODIC * 360).sum(1)
    nn = sum(1 for b in sub if min(b["phase"], 360 - b["phase"]) <= 1.5 / SYNODIC * 360)
    nnn = (np.minimum(NP, 360 - NP) <= 1.5 / SYNODIC * 360).sum(1)
    illum = float(np.mean([b["illum"] for b in sub])); illn = ((1 - np.cos(np.radians(NP))) / 2).mean(1)
    return {"n": n, "obs": obs.tolist(), "exp": exp.round(2).tolist(), "obs_pc": (100 * obs / n).round(2).tolist(), "exp_pc": (100 * exp / n).round(2).tolist(),
            "ratio": (obs / exp).round(3).tolist(),
            "chi2": chi, "chi2_p_sim": float((1 + (chin >= chi).sum()) / (reps + 1)), "chi2_p_asym": float(stats.chi2.sf(chi, 7)),
            "rayleigh_R": r1, "rayleigh_p_sim": float((1 + (r1n >= r1).sum()) / (reps + 1)), "rayleigh_p_asym": float(np.exp(-n * r1 ** 2) * (1 + (2 * n * r1 ** 2 - (n * r1 ** 2) ** 2) / (4 * n) - (24 * n * r1 ** 2 - 132 * (n * r1 ** 2) ** 2 + 76 * (n * r1 ** 2) ** 3 - 9 * (n * r1 ** 2) ** 4) / (288 * n ** 2))),
            "R2": r2, "R2_p_sim": float((1 + (r2n >= r2).sum()) / (reps + 1)), "mean_dir": mean_dir,
            "near_full": nf, "near_full_pc": 100 * nf / n, "near_full_exp_pc": float(100 * nfn.mean() / n), "near_full_p": float((1 + (nfn >= nf).sum()) / (reps + 1)),
            "near_new": nn, "near_new_pc": 100 * nn / n, "near_new_exp_pc": float(100 * nnn.mean() / n),
            "mean_illum": illum, "mean_illum_exp": float(illn.mean()), "mean_illum_null_sd": float(illn.std()), "exp_sd": ncount.std(0).round(2).tolist(), "mean_illum_p2": float((1 + (np.abs(illn - illn.mean()) >= abs(illum - illn.mean())).sum()) / (reps + 1))}


R["all"] = phase_tests(T)
R["all_season"] = phase_tests(T, 500, season=True)
print("ALL", {k: R["all"][k] for k in ("n", "obs_pc", "exp_pc", "chi2", "chi2_p_sim", "rayleigh_R", "rayleigh_p_sim", "rayleigh_p_asym", "mean_dir", "R2_p_sim", "near_full_pc", "near_full_exp_pc", "mean_illum", "mean_illum_exp", "mean_illum_p2")})
print("SEASON", {k: R["all_season"][k] for k in ("chi2_p_sim", "rayleigh_p_sim", "exp_pc")})
# the null expectation per bin is flat to within a fraction of a per cent: say how flat
R["null_flatness_pc"] = float(np.max(np.abs(np.array(R["all"]["exp_pc"]) - 12.5)))


# ---------- moonlight on the night before: battles against random nights at the same site in the same century
def moon_tests(sub):
    idx = np.array([qi[b["q"]] for b in sub])
    own = NZ["owner"]
    by = defaultdict(list)
    for k, o in enumerate(own):
        by[o].append(k)
    N = np.array([by[i] for i in idx])                        # (n, K) rows into res
    out = {}
    for j, key in ((2, "moon_dark_h"), (3, "moonlight"), (1, "dark_h"), (4, "moon_up_at_sunrise")):
        obs = np.array([float(b[key]) if b[key] is not None else 0.0 for b in sub])
        nul = res[N, j]
        d = obs - nul.mean(1)
        t = stats.ttest_1samp(d, 0.0)
        boot = nul[np.arange(len(sub))[None, :], rng.integers(0, N.shape[1], (2000, len(sub)))].mean(1)
        out[key] = {"obs": float(obs.mean()), "null": float(nul.mean()), "diff": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d))),
                    "t_p": float(t.pvalue), "p_sim": float((1 + (np.abs(boot - nul.mean()) >= abs(obs.mean() - nul.mean())).sum()) / 2001)}
    out["moon_up_at_sunrise"]["obs_pc"] = 100 * out["moon_up_at_sunrise"]["obs"]; out["moon_up_at_sunrise"]["null_pc"] = 100 * out["moon_up_at_sunrise"]["null"]
    out["moonlit_share_pc"] = 100 * out["moon_dark_h"]["obs"] / out["dark_h"]["obs"]
    out["moonlit_share_null_pc"] = 100 * out["moon_dark_h"]["null"] / out["dark_h"]["null"]
    return out


R["night"] = moon_tests(T)
print("NIGHT", R["night"])

# ---------- by era and by kind
R["eras"] = {}
for k, name, a, z in ERAS:
    sub = [b for b in T if b["era"] == k]
    if len(sub) < 30: continue
    r = phase_tests(sub); r.update({"name": name, "night": moon_tests(sub)})
    R["eras"][k] = r
    print(name, r["n"], r["chi2_p_sim"], r["rayleigh_p_sim"], r["near_full_pc"], r["night"]["moonlight"]["diff"], r["night"]["moonlight"]["p_sim"])
KINDS = {"sea": ("At sea", lambda b: b["sea"]), "land": ("On land", lambda b: not b["sea"]), "night": ("Named a night attack or night battle", lambda b: "night" in b["tags"]),
         "raid": ("Raids, ambushes and surprise attacks", lambda b: "raid" in b["tags"]), "air": ("Air raids and air battles", lambda b: "air" in b["tags"]),
         "famous": ("Well known (30 or more Wikipedia editions)", lambda b: b["sl"] >= 30), "ww2": ("Second World War, 1939 to 1945", lambda b: 1939 <= b["y"] <= 1945),
         "ww1": ("First World War, 1914 to 1918", lambda b: 1914 <= b["y"] <= 1918)}
R["kinds"] = {}
for k, (name, f) in KINDS.items():
    sub = [b for b in T if f(b)]
    if len(sub) < 15: continue
    r = phase_tests(sub, 1000); r.update({"name": name, "night": moon_tests(sub)})
    R["kinds"][k] = r
    print(name, r["n"], r["obs"], r["chi2_p_sim"], r["rayleigh_p_sim"], round(r["near_full_pc"], 1), round(r["mean_illum"], 3), round(r["mean_illum_exp"], 3))
S = [b for b in B if b["siege"] and b["cal_ok"] and b["status"] == "ok"]
R["sieges"] = phase_tests(S, 1000); R["sieges"]["name"] = "Sieges (start date)"
# ---------- sensitivity to the calendar rules and the data
SENS = {"no_reflag": ("Leaving out the pre-1582 dates whose flag I corrected", lambda b: in_test(b) and b["fix"] != "reflagged"),
        "post1582": ("Only dates after the Gregorian reform (from 15 October 1582)", lambda b: in_test(b) and b["J"] >= jdn_greg(1582, 10, 15)),
        "with_uncertain": ("Adding the uncertain British Old Style dates and the ancient dates", lambda b: (not b["siege"]) and b["status"] == "ok"),
        "no_day1": ("Leaving out dates on the 1st of a month (possible month-only dates)", lambda b: in_test(b) and not b["day1"]),
        "own_point": ("Only battles with their own coordinates", lambda b: in_test(b) and b["psrc"] == "battle"),
        "one_per_day": ("One battle per date (sub-battles of the same day counted once)", None)}
R["sens"] = {}
for k, (name, f) in SENS.items():
    if f is None:
        seen, sub = set(), []
        for b in sorted(T, key=lambda b: -b["sl"]):
            if b["J"] not in seen: seen.add(b["J"]); sub.append(b)
    else:
        sub = [b for b in B if f(b)]
    r = phase_tests(sub, 1000)
    R["sens"][k] = {"name": name, "n": r["n"], "chi2_p_sim": r["chi2_p_sim"], "rayleigh_p_sim": r["rayleigh_p_sim"], "near_full_pc": r["near_full_pc"],
                    "near_full_exp_pc": r["near_full_exp_pc"], "mean_illum": r["mean_illum"], "mean_illum_exp": r["mean_illum_exp"], "R2_p_sim": r["R2_p_sim"]}
    print("SENS", name, R["sens"][k])
# how much the calendar matters: phase moved by the Julian-Gregorian gap
R["gap_days_1066"] = jdn_jul(1066, 10, 14) - jdn_greg(1066, 10, 14)
R["gap_days_1600"] = jdn_jul(1645, 6, 14) - jdn_greg(1645, 6, 14)
R["gap_phase_deg_1600"] = R["gap_days_1600"] / SYNODIC * 360

# ---------- age in days (30 bins) for the wheel, with the null
age = np.array([b["age"] for b in T])
R["age_hist"] = np.bincount(np.clip(age.astype(int), 0, 29), minlength=30).tolist()
NP = null_phases(T, 200)
R["age_hist_null"] = (np.bincount(np.clip((NP / 360 * SYNODIC).astype(int).ravel(), 0, 29), minlength=30) / 200).round(2).tolist()

# ---------- calendar checks and famous cases
cc = list(csv.DictReader(open(f"{DATA}/calendar_checks.csv", encoding="utf-8")))
R["calendar_checks"] = {"n": len(cc), "agree": sum(r["agrees"] == "True" for r in cc)}
fam = FAM["rows"]
R["famous"] = fam
R["famous_max_diff"] = FAM["max_diff"]
F = {r["name"]: r for r in fam}
R["F"] = {k.split(",")[0].replace(" ", "_").replace("-", "_").lower(): v for k, v in F.items()}
for k in ("halys", "pydna", "d_day", "hastings", "waterloo", "agincourt", "the_somme"):
    assert k in R["F"], k
assert R["F"]["pydna"]["phase_name"] == "Full moon" and R["F"]["halys"]["phase_name"] == "New moon"
# the most moonlit and darkest well-known battles
W = sorted([b for b in T if b["sl"] >= 25], key=lambda b: b["dfull"] ** 2)
R["full_famous"] = [{"label": b["label"], "date": date_text(b["y"], b["m"], b["d"]), "dfull": round(b["dfull"], 1), "sl": b["sl"]} for b in W[:12]]
W = sorted([b for b in T if b["sl"] >= 25], key=lambda b: min(b["phase"], 360 - b["phase"]))
R["new_famous"] = [{"label": b["label"], "date": date_text(b["y"], b["m"], b["d"]), "phase": round(b["phase"], 1), "sl": b["sl"]} for b in W[:12]]
R["n_famous25"] = sum(1 for b in T if b["sl"] >= 25)
# night-labelled battles listed
R["night_list"] = sorted([{"label": b["label"], "date": date_text(b["y"], b["m"], b["d"]), "phase": round(b["phase"]), "illum": round(b["illum"], 2), "name": PHASES[b["bin"]]}
                          for b in T if "night" in b["tags"]], key=lambda x: x["label"])
# the year of the most battles, eras counts
R["era_n"] = {k: sum(1 for b in T if b["era"] == k) for k, *_ in ERAS}
R["phases"] = PHASES
# numbers in words for the texts
A = R["all"]
R["T"] = {"illum_obs_pc": 100 * A["mean_illum"], "illum_exp_pc": 100 * A["mean_illum_exp"], "illum_diff_pc": 100 * (A["mean_illum"] - A["mean_illum_exp"]),
          "implied_share_pc": 200 * (A["mean_illum"] - A["mean_illum_exp"]),
          "near_full_extra": A["near_full"] - A["near_full_exp_pc"] * A["n"] / 100,
          "full_bin_pc": A["obs_pc"][4], "new_bin_pc": A["obs_pc"][0], "min_bin_pc": min(A["obs_pc"]), "max_bin_pc": max(A["obs_pc"]),
          "bright_half_pc": sum(A["obs_pc"][3:6]) + (A["obs_pc"][2] + A["obs_pc"][6]) / 2, "moonlit_extra_min": 60 * R["night"]["moon_dark_h"]["diff"],
          "ww2_full": R["kinds"]["ww2"]["obs"][4], "ww2_full_exp": R["kinds"]["ww2"]["exp"][4], "ww2_n": R["kinds"]["ww2"]["n"],
          "fragile_max_p": max(R["sens"][k]["rayleigh_p_sim"] for k in R["sens"]), "fragile_min_p": min(R["sens"][k]["rayleigh_p_sim"] for k in R["sens"])}
assert 49 < R["T"]["illum_exp_pc"] < 51 and abs(A["mean_dir"] - 180) < 30
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)

with open(f"{DATA}/battles.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["qid", "label", "date_gregorian", "year", "month", "day", "date_julian", "calendar_flag", "calendar_rule", "in_test", "siege", "lon", "lat",
                "point_from", "at_sea", "sitelinks", "phase_angle", "phase_name", "illuminated", "age_days", "days_from_full", "dark_hours_night_before",
                "moonlit_dark_hours_night_before", "moonlight_index", "moon_up_at_sunrise", "wars"])
    for b in sorted(B, key=lambda b: b["J"]):
        jy, jm, jd = jul_from_jdn(b["J"])
        w.writerow([b["q"], b["label"], f"{b['y']:05d}-{b['m']:02d}-{b['d']:02d}" if b["y"] < 0 else f"{b['y']:04d}-{b['m']:02d}-{b['d']:02d}", b["y"], b["m"], b["d"],
                    f"{jy}-{jm:02d}-{jd:02d}" if b["J"] < jdn_greg(1752, 9, 14) else "", b["entered_cal"], b["fix"], in_test(b), b["siege"], b["lon"], b["lat"],
                    b["psrc"], b["sea"], b["sl"], round(b["phase"], 2), PHASES[b["bin"]], round(b["illum"], 4), round(b["age"], 2), round(b["dfull"], 2),
                    round(b["dark_h"], 2), round(b["moon_dark_h"], 2), round(b["moonlight"], 3), b["moon_up_at_sunrise"], "; ".join(b["wars"])])
print("battles.csv", len(B))
