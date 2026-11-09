"""Step 3: hand checks. An independent second ephemeris (PyEphem, the libastro code of XEphem) for the famous battles, against
astronomy-engine; plus what the historical record says about the Moon on some of those days (eclipses, the lunar calendar).
Output: data/famous.csv, SCR/famous.json.  Dates go to PyEphem as Dublin Julian dates, so its own Julian/Gregorian switch
in 1582 plays no part."""
import csv
import ephem
from common import *

B = {b["q"]: b for b in jload(f"{SCR}/battles.json")}
MO = {m["q"]: m for m in jload(f"{SCR}/moon.json")}
# (Wikidata label, short name, what the record says about the Moon on the day; "" if nothing independent)
FAMOUS = [
    ("Battle of Halys", "Halys, 585 BC", "Herodotus: a total eclipse of the Sun stopped the battle (28 May 585 BC, Julian), so a new Moon"),
    ("Battle of Gaugamela", "Gaugamela, 331 BC", "a lunar eclipse eleven days before (20 September 331 BC, Julian)"),
    ("Battle of Pydna", "Pydna, 168 BC", "Livy: a lunar eclipse the night before (21 June 168 BC, Julian), so a full Moon"),
    ("Battle of Badr", "Badr, 624", "17 Ramadan in the Islamic lunar calendar, whose months begin at the new crescent"),
    ("Battle of Hastings", "Hastings, 1066", ""),
    ("Battle of Crécy", "Crécy, 1346", ""),
    ("Battle of Kosovo", "Kosovo, 1389", ""),
    ("Battle of Agincourt", "Agincourt, 1415", ""),
    ("Battle of Bosworth Field", "Bosworth, 1485", ""),
    ("Battle of Lepanto", "Lepanto, 1571", ""),
    ("La Noche Triste", "La Noche Triste, 1520", ""),
    ("Battle of Naseby", "Naseby, 1645", ""),
    ("Battle of Culloden", "Culloden, 1746", ""),
    ("Battle of Trafalgar", "Trafalgar, 1805", ""),
    ("Battle of Waterloo", "Waterloo, 1815", ""),
    ("Battle of Gettysburg", "Gettysburg, 1863", ""),
    ("Battle of Isandlwana", "Isandlwana, 1879", "a partial eclipse of the Sun took place during the battle, so a new Moon"),
    ("Battle of the Somme", "The Somme, 1916", ""),
    ("Battle of Britain", "Battle of Britain, 1940", ""),
    ("Attack on Pearl Harbor", "Pearl Harbor, 1941", ""),
    ("Battle of Stalingrad", "Stalingrad, 1942", ""),
    ("Second Battle of El Alamein", "Second El Alamein, 1942", "the night attack opened under a Moon just short of full"),
    ("Normandy landings", "D-Day, 1944", "the date was set for a bright Moon near full, for the airborne drops, and a low but rising tide soon after dawn"),
    ("Tet Offensive", "Tet Offensive, 1968", "launched at the lunar New Year, which falls at a new Moon"),
    ("Yom Kippur War", "Yom Kippur War, 1973", "10 Tishri in the Hebrew lunisolar calendar, about nine days after the new Moon"),
]
byq = {}
for lab, nm, note in FAMOUS:
    c = [b for b in B.values() if b["label"] == lab and b["status"] == "ok"]
    if not c:
        print("not in data:", lab); continue
    b = max(c, key=lambda x: x["sl"]); byq[b["q"]] = (nm, note)
rows = []
for q, (nm, note) in byq.items():
    b, m = B[q], MO[q]
    jd_noon = b["J"] - b["lon"] / 360.0                   # JD (UT) of local mean noon
    d = ephem.Date(jd_noon - 2415020.0)                  # Dublin Julian date
    mo, su = ephem.Moon(d), ephem.Sun(d)
    elong = math.degrees(ephem.Ecliptic(mo).lon - ephem.Ecliptic(su).lon) % 360
    pf = ephem.previous_full_moon(d); nf = ephem.next_full_moon(d)
    dfull = min(d - pf, d - nf, key=abs)
    rows.append({"name": nm, "qid": q, "label": b["label"], "date": date_text(b["y"], b["m"], b["d"]) + " (Gregorian)",
                 "date_julian": date_text(*jul_from_jdn(b["J"])) + " (Julian)" if b["J"] < jdn_greg(1752, 9, 14) else "",
                 "rule": b["fix"], "phase_ae": round(m["phase"], 1), "phase_ephem": round(elong, 1), "illum_ae": round(m["illum"], 3),
                 "illum_ephem": round(mo.moon_phase, 3), "days_from_full_ae": round(m["dfull"], 2), "days_from_full_ephem": round(dfull, 2),
                 "phase_name": PHASES[phase_bin(m["phase"])], "moon_dark_h": round(m["moon_dark_h"], 1), "dark_h": round(m["dark_h"], 1),
                 "moon_up_at_sunrise": m["moon_up_at_sunrise"], "record": note,
                 "lon": b["lon"], "lat": b["lat"]})
rows.sort(key=lambda r: B[r["qid"]]["J"])
dmax = max(min(abs(r["phase_ae"] - r["phase_ephem"]), 360 - abs(r["phase_ae"] - r["phase_ephem"])) for r in rows)
print("max phase difference astronomy-engine vs PyEphem:", round(dmax, 2), "deg over", len(rows))
for r in rows:
    print(f"{r['name']:34s} {r['date']:32s} {r['phase_ae']:6.1f} {r['phase_ephem']:6.1f} illum {r['illum_ae']:.2f} full {r['days_from_full_ae']:+.1f} d  {r['phase_name']:16s} moon-dark {r['moon_dark_h']}/{r['dark_h']} h")
assert dmax < 1.0
with open(f"{DATA}/famous.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
jsave({"rows": rows, "max_diff": dmax}, f"{SCR}/famous.json", keepdash=True)
