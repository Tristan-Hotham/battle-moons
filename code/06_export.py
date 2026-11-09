"""Step 6: page data. data/points.json (one row per item, compact) and data/site.json (null expectation for the live wheel)."""
from common import *

R = jload(f"{DATA}/results.json")
B = jload(f"{SCR}/battles.json")
MO = {m["q"]: m for m in jload(f"{SCR}/moon.json")}
FIX = {"gregorian": 0, "julian": 1, "reflagged": 2, "os_override": 3, "os_checked": 4, "date_override": 5, "os_uncertain": 6, "ancient": 7}


def clock(h):
    """hours from local mean noon of the day before -> minutes after midnight of that day (local mean time)"""
    return None if h is None else int(round((12 + h) * 60))


rows = []
for b in sorted(B, key=lambda b: b["J"]):
    m = MO[b["q"]]
    test = (not b["siege"]) and b["cal_ok"] and b["status"] == "ok"
    flags = (1 if b["siege"] else 0) | (2 if b["sea"] else 0) | (4 if test else 0) | (8 if b["status"] != "ok" else 0) | (16 if b["psrc"] == "location" else 0) \
        | (32 if m["moon_up_at_sunrise"] else 0)
    jy, jm, jd = jul_from_jdn(b["J"])
    rows.append([b["q"], b["label"], round(b["lon"], 4), round(b["lat"], 4), b["y"], b["m"], b["d"], round(m["phase"], 1), round(m["illum"] * 100),
                 FIX[b["fix"]], flags, b["sl"], round(m["moon_dark_h"], 1), round(m["dark_h"], 1), clock(m["sunset"]), clock(m["sunrise"]),
                 [clock(h) for h in m["moonrise"]], [clock(h) for h in m["moonset"]], round(m["dfull"], 1),
                 [jy, jm, jd] if b["J"] < jdn_greg(1752, 9, 14) and b["fix"] != "ancient" else 0, b["wars"][0] if b["wars"] else ""])
jsave({"cols": ["q", "label", "lon", "lat", "y", "m", "d", "phase", "illum", "fix", "flags", "sl", "moon_dark_h", "dark_h", "sunset", "sunrise", "moonrise", "moonset",
                "dfull", "julian", "war"], "rows": rows}, f"{DATA}/points.json", keepdash=True)
site = {"exp_pc": R["all"]["exp_pc"], "phases": PHASES, "pcol": PCOL, "n_test": R["n"]["test"]}
jsave(site, f"{DATA}/site.json", keepdash=True)
print("points", len(rows), os.path.getsize(f"{DATA}/points.json") // 1024, "KB")
