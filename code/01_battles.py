"""Step 1: read the Wikidata battle and siege rows, settle one date per item in the proleptic Gregorian calendar, one point,
and flag what we know about the calendar. Output: SCR/battles.json (all items) and data/calendar_checks.csv.

Calendar handling (see NOTES.md for the hand checks behind each rule):
  * The RDF/QLever time value is already proleptic Gregorian; the calendar model says what the editor entered.
    Julian-flagged values are used as they are.
  * Gregorian-flagged values before 15 October 1582 are, case by case, the usual Julian dates with the wrong flag
    (Bosworth 22 August 1485, Towton 29 March 1461 ...). They are reinterpreted as Julian and converted.
  * Gregorian-flagged values in Britain, Ireland and British North America from 1582 to 13 September 1752 are often Old Style
    dates with the wrong flag (Naseby, Marston Moor) but sometimes correct (Culloden). They are "uncertain" unless a
    documented override (code/overrides.csv) settles them.
  * Dates before AD 1 come from ancient calendars converted by modern scholars: "uncertain" for the test, kept on the map.
"""
import csv, gzip
from collections import defaultdict
import numpy as np
from shapely.geometry import shape, Point
from shapely.prepared import prep
from common import *

ENT = "http://www.wikidata.org/entity/"


def lit(s):
    s = s.strip()
    if not s: return ""
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^.*)?$', s, re.S)
    v = m.group(1) if m else s
    return v.replace('\\"', '"').replace("\\\\", "\\")


def qid(s):
    return s.strip().strip("<>").replace(ENT, "")


def pt(s):
    m = re.search(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def british_os_region(lon, lat):
    """Britain and Ireland, and British North America (east coast), where Old Style dates were used to 1752"""
    if -11.0 <= lon <= 2.0 and 49.8 <= lat <= 61.0: return True
    if -92.0 <= lon <= -52.0 and 24.0 <= lat <= 52.0: return True
    return False


ov = {r["qid"]: r for r in csv.DictReader(open(os.path.join(ROOT, "code", "overrides.csv"), encoding="utf-8"))}
items = defaultdict(lambda: {"stm": set(), "coord": [], "loc": [], "wars": set(), "sl": 0, "label": "", "files": set()})
nrows = 0
for kind in ("battles", "sieges"):
    for prop in ("p585", "p580"):
        fn = f"{RAW}/{kind}_{prop}.tsv.gz"
        with gzip.open(fn, "rt", encoding="utf-8") as f:
            next(f)
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) < 10: continue
                nrows += 1
                q = qid(c[0]); it = items[q]
                it["label"] = it["label"] or lit(c[1])
                it["files"].add(kind)
                m = re.match(r"^(-?\d+)-(\d\d)-(\d\d)T", c[2].strip())
                if m:
                    it["stm"].add((prop, int(m.group(1)), int(m.group(2)), int(m.group(3)), int(c[3] or 0), qid(c[4])))
                p = pt(c[5]); l = pt(c[6])
                if p and p not in it["coord"]: it["coord"].append(p)
                if l and l not in it["loc"]: it["loc"].append(l)
                if c[8].strip(): it["wars"].add(lit(c[8]))
                try: it["sl"] = max(it["sl"], int(lit(c[9]) or 0))
                except ValueError: pass
print("rows", nrows, "items", len(items))

land = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_10m_land.geojson")["features"]] if os.path.exists(f"{GEO}/ne_10m_land.geojson") else \
       [shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]
from shapely.ops import unary_union
LAND = prep(unary_union(land).buffer(0.03))     # about 3 km of slack for coastal battles

out, stats = [], defaultdict(int)
for q, it in items.items():
    lab = it["label"] or q
    st = [s for s in it["stm"] if s[4] == 11]
    if not st:
        stats["no_day_precision"] += 1; continue
    pts = it["coord"] or it["loc"]
    if not pts:
        stats["no_point"] += 1; continue
    if it["coord"]:
        lon, lat = sorted(it["coord"])[0]; psrc = "battle"
    else:
        a = np.array(it["loc"]); lon, lat = float(np.median(a[:, 0])), float(np.median(a[:, 1])); psrc = "location"
    cands = []
    for prop, y, mo, d, pr, cal in st:
        g = jdn_greg(y, mo, d)
        if y < 1:
            fix = "ancient"
        elif cal == JUL:
            fix = "julian"
        elif cal == GREG and g < jdn_greg(1582, 10, 15):
            g = jdn_jul(y, mo, d); fix = "reflagged"
        elif cal == GREG and g < jdn_greg(1752, 9, 14) and british_os_region(lon, lat):
            fix = "os_uncertain"
        else:
            fix = "gregorian"
        if q in ov and fix == "os_uncertain":
            if ov[q]["action"] == "os":
                g = jdn_jul(y, mo, d); fix = "os_override"
            elif ov[q]["action"] == "ok":
                fix = "os_checked"
        if q in ov and ov[q]["action"].startswith("jul:"):
            yy, mm, dd = map(int, ov[q]["action"][4:].split("-")); g = jdn_jul(yy, mm, dd); fix = "date_override"
        cands.append((g, prop, fix, cal, jul_from_jdn(g) if cal == JUL or fix in ("reflagged", "os_override", "date_override") else (y, mo, d)))
    js = sorted(set(c[0] for c in cands))
    # several date statements: within three days, take the first day of fighting; further apart, the item is ambiguous
    status = "ambiguous" if js[-1] - js[0] > 3 else "ok"
    stats["ambiguous_dates" if status == "ambiguous" else "single_date"] += 1
    J = js[0]
    # several statements on the same day: pick deterministically, preferring a settled calendar and an explicit Julian flag
    pick = sorted([c for c in cands if c[0] == J], key=lambda c: (c[2] in ("os_uncertain", "ancient"), c[3] != JUL, c[1], c[2]))[0]
    fixes = sorted(set(c[2] for c in cands if c[0] - J <= 3))
    fix = pick[2]
    if len(set(c[2] for c in cands)) > 1:
        stats["mixed_flags"] += 1
    y, mo, d = greg_from_jdn(J)
    is_siege = "sieges" in it["files"] or bool(re.match(r"(?i)^(siege|blockade|investment)\b", lab))
    cal_ok = fix in ("julian", "reflagged", "gregorian", "os_override", "os_checked", "date_override")
    # day of month as the editor entered it, to catch month-only dates saved as the 1st
    oy, om, od = pick[4]
    low = lab.lower()
    tags = []
    if re.search(r"\bnight\b|nocturn", low): tags.append("night")
    if re.search(r"\braid\b|\braids\b|ambush|surprise", low): tags.append("raid")
    if re.search(r"air raid|bombing|\bblitz\b|air battle|airstrike|air attack", low): tags.append("air")
    at_sea = not LAND.contains(Point(lon, lat))
    out.append({"q": q, "label": lab, "J": J, "y": y, "m": mo, "d": d, "entered": [oy, om, od], "entered_cal": "J" if pick[3] == JUL else "G",
                "prop": pick[1], "fix": fix, "cal_ok": cal_ok, "n_dates": len(js), "status": status, "lon": round(lon, 5), "lat": round(lat, 5),
                "psrc": psrc, "siege": is_siege, "wars": sorted(it["wars"])[:4], "sl": it["sl"], "tags": tags, "sea": at_sea,
                "day1": od == 1})
    stats["kept"] += 1
print(dict(stats))
print("fix counts", {k: sum(1 for o in out if o["fix"] == k) for k in sorted(set(o["fix"] for o in out))})
jsave(out, f"{SCR}/battles.json", keepdash=True)
jsave({"items": len(items), "rows": nrows, **stats}, f"{SCR}/stats01.json", keepdash=True)

# hand checks: the famous dates, as the pipeline settles them, against the dates in the standard histories
CHECK = [("Battle of Hastings", 1066, 10, 14, "J"), ("Battle of Agincourt", 1415, 10, 25, "J"), ("Battle of Crécy", 1346, 8, 26, "J"),
         ("Battle of Bosworth Field", 1485, 8, 22, "J"), ("Battle of Towton", 1461, 3, 29, "J"), ("Battle of Stamford Bridge", 1066, 9, 25, "J"),
         ("Battle of Bannockburn", 1314, 6, 24, "J"), ("Battle of Lepanto", 1571, 10, 7, "J"), ("Battle of Naseby", 1645, 6, 14, "J"),
         ("Battle of Marston Moor", 1644, 7, 2, "J"), ("Battle of Edgehill", 1642, 10, 23, "J"), ("Battle of the Boyne", 1690, 7, 1, "J"),
         ("Battle of Culloden", 1746, 4, 16, "J"), ("Battle of Poltava", 1709, 6, 27, "J"), ("Battle of Blenheim", 1704, 8, 13, "G"),
         ("Battle of Waterloo", 1815, 6, 18, "G"), ("Battle of Borodino", 1812, 9, 7, "G"), ("Battle of Gettysburg", 1863, 7, 1, "G"),
         ("Battle of the Somme", 1916, 7, 1, "G"), ("Battle of Pydna", -167, 6, 22, "J"), ("Battle of Halys", -584, 5, 28, "J")]
byl = defaultdict(list)
for o in out:
    byl[o["label"]].append(o)
rows = []
for lab, y, m, d, cal in CHECK:
    exp = jdn_jul(y, m, d) if cal == "J" else jdn_greg(y, m, d)
    for o in byl.get(lab, []):
        if lab == "Battle of Bannockburn":
            exp2 = exp  # two days, 23 and 24 June: Wikidata gives the first, so accept either
            ok = o["J"] in (exp, exp - 1)
        else:
            ok = o["J"] == exp
        gy, gm, gd = greg_from_jdn(exp)
        rows.append({"label": lab, "qid": o["q"], "standard_date": f"{date_text(y, m, d)} ({'Julian' if cal == 'J' else 'Gregorian'})",
                     "gregorian": date_text(gy, gm, gd), "pipeline": date_text(o["y"], o["m"], o["d"]), "flag": o["entered_cal"], "rule": o["fix"],
                     "agrees": ok})
with open(f"{DATA}/calendar_checks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    print(("OK " if r["agrees"] else "XX ") + r["label"], r["pipeline"], "|", r["gregorian"], r["rule"])
assert sum(r["agrees"] for r in rows) >= len(rows) - 1
