"""Step 10: README.md, LICENSE and reddit/post.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
A, T, N, F = R["all"], R["T"], R["n"], R["F"]
rows = "\n".join(f"| {PHASES[k]} | {A['obs'][k]:,} | {A['exp'][k]:,.0f} | {A['obs_pc'][k]:.1f}% |" for k in range(8))
readme = f"""# Fighting by moonlight

The phase of the Moon on the day, and the moonlight of the night before, at the site of every battle in Wikidata with a date to the day and a place: {N['test']:,} battles from AD {N['first_year']} to 2026 after calendar checks, tested against random days from each battle's own century.

Interactive page: https://maps.tristanhotham.com/battle-moons/
Paper: {{https://doi.org/10.5281/zenodo.24089704}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/battle-moons/}}
Code and data: https://github.com/Tristan-Hotham/battle-moons

## Headline results

- Battles fall on every phase of the Moon almost equally: each eighth of the lunar month holds {T['min_bin_pc']:.1f}% to {T['max_bin_pc']:.1f}% of battles (12.5% expected); the eight-bin test does not differ from chance (simulated p = {A['chi2_p_sim']:.2f}). No era shows a pattern.
- A faint lean to the bright half of the month: mean lit fraction {T['illum_obs_pc']:.1f}% against {T['illum_exp_pc']:.1f}% for random days; {A['near_full_pc']:.1f}% of battles within 1.5 days of full Moon against {A['near_full_exp_pc']:.1f}% (Rayleigh p = {A['rayleigh_p_sim']:.3f}). About {T['implied_share_pc']:.0f}% of battles timed for a full Moon would explain it, and it is not robust (p = {R['sens']['one_per_day']['rayleigh_p_sim']:.3f} counting one battle per date, {R['sens']['own_point']['rayleigh_p_sim']:.2f} with only battles' own coordinates).
- The night before: the Moon was up for {R['night']['moon_dark_h']['obs']:.2f} of {R['night']['dark_h']['obs']:.2f} dark hours against {R['night']['moon_dark_h']['null']:.2f} on season-matched random nights (about {T['moonlit_extra_min']:.0f} minutes more); no difference in whether it was up at dawn.
- Famous cases: D-Day and Second El Alamein at full Moon, as planned; Gettysburg and La Noche Triste full; Hastings and Agincourt last quarter; the Somme, Trafalgar and Naseby new Moon. Eclipse checks: Pydna full, Halys and Isandlwana new.
- Calendars: Wikidata's RDF values are proleptic Gregorian with a flag for the calendar of entry; {N['reflagged_all']} pre-1582 dates flagged Gregorian are Julian dates and were converted; British Old Style dates before 1752 were settled by hand ({N['os_hand']}, plus Kosovo 1389 corrected) or left out ({N['os_uncertain']}). All {R['calendar_checks']['n']} hand-checked famous dates agree.

| Phase | Battles | Expected | Share |
|---|---|---|---|
{rows}

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: MapLibre on OpenFreeMap Positron, battles coloured by phase, phase filter, year range, layers, live moon-phase wheel, popups with the Moon and the night before. |
| `header.png` | Social card, 1200 x 630. |
| `data/battles.csv` | Every item ({N['items']:,}): settled Gregorian (and Julian) date, calendar flag and rule, test flag, siege, point, phase, lit share, age, days from full, darkness and moonlight the night before. |
| `data/calendar_checks.csv`, `data/famous.csv` | Hand checks of dates and of the Moon over famous battles (astronomy-engine and PyEphem). |
| `data/points.json`, `data/site.json` | Page data. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, `overrides.csv` (hand calendar decisions), templates, `qa.js`. |
| `release/` | Paper, blog post and figures, Zenodo files. |
| `reddit/` | Collage and post text. |

## Method in brief

- Battles: Wikidata Q178561 and subclasses with P585 or P580 at day precision and P625 or P276 coordinates (QLever). Sieges (Q188055) kept apart. Several dates within three days: the first; further apart: excluded.
- Calendars: values used as stored (proleptic Gregorian) when flagged Julian; Gregorian flag before 15 October 1582 read as Julian; Britain, Ireland and British North America with a Gregorian flag before 14 September 1752 uncertain unless settled in `code/overrides.csv`; dates before AD 1 out of the test.
- Moon: astronomy-engine at the battle site; phase at local mean noon; Sun and Moon every 10 minutes through the night before (darkness: Sun below -6 degrees).
- Null: 2,000 sets of random days from each battle's century (Meeus phase formula, checked against astronomy-engine); moonlight: 10 random nights per battle, same site, same century, within 15 days of the same date in the year.

## How to rerun

Needs Python 3 with numpy, scipy, shapely, astronomy-engine, ephem, matplotlib, Pillow; xelatex; node with Playwright for `code/qa.js`.

```
python3 code/01_battles.py     # dates, calendars, points
python3 code/02_moon.py        # Moon and Sun per battle and null nights (about 15 minutes on two cores)
python3 code/03_checks.py      # famous battles, PyEphem cross-check
python3 code/04_results.py     # tests and results.json
python3 code/06_export.py      # page data
python3 code/05_figures.py     # figures and header
python3 code/07_build_site.py  # index.html
python3 code/08_paper.py       # paper PDF (set DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage
python3 code/10_readme.py      # README, LICENSE, Reddit post
python3 code/09_release.py     # blog post, Zenodo files
```

## Sources and licences

- Wikidata (https://www.wikidata.org/), CC0, queried with QLever. Derived data CC0.
- astronomy-engine (Don Cross, MIT licence); PyEphem.
- Base map: OpenFreeMap Positron style, OpenStreetMap contributors (ODbL). Static maps: Natural Earth. Fonts: MedievalSharp, IM Fell (SIL OFL).
- Text and figures CC BY 4.0; code MIT.

## Citation

Hotham, T. (2026) Fighting by moonlight: the phase of the Moon on the days of {N['test']:,} battles. Zenodo. {{10.5281/zenodo.24089704}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(open("/home/claude/studies/renamed-world/LICENSE", encoding="utf-8").read())
post = f"""**Title:** [OC] I worked out the Moon over {N['test']:,} battles, from Hastings to D-Day. Battles fall on every phase of the Moon almost equally

**Body:**

Every battle in Wikidata with an exact day and a place, the Moon's phase at the battle site that day, and the moonlight of the night before, compared with random days from the same centuries (2,000 simulations).

- Each eighth of the lunar month holds {T['min_bin_pc']:.1f}% to {T['max_bin_pc']:.1f}% of battles, against 12.5% for random days. No era shows a lunar rhythm.
- A faint lean to the bright Moon: {T['illum_obs_pc']:.1f}% lit on the average battle day against {T['illum_exp_pc']:.1f}%. About {T['implied_share_pc']:.0f} battles in 100 timed for a full Moon would do it, and it fades if same-day sub-battles are counted once.
- D-Day ({round(100*F['d_day']['illum_ae'])}% lit) and Second El Alamein ({round(100*F['second_el_alamein']['illum_ae'])}%) were full-Moon battles by design; the Somme, Trafalgar and Naseby fell at new Moon; Hastings and Agincourt at last quarter.
- The hard part was calendars: {N['reflagged_all']} pre-1582 dates in Wikidata carry a Gregorian flag but are Julian dates, and English Civil War dates are often Old Style. Ten days move the Moon a third of its cycle.
- Checks: Pydna (lunar eclipse the night before, 168 BC) comes out full; Halys (solar eclipse, 585 BC) and Isandlwana (partial solar eclipse, 1879) new.

Interactive map (phase filter, year range, tap a battle for its Moon): https://maps.tristanhotham.com/battle-moons/

**Source comment:**

Data: Wikidata (CC0) via QLever. Moon: astronomy-engine, cross-checked with PyEphem. Tools: Python (numpy, scipy, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/battle-moons
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS"):
        assert bad not in t, bad
print("readme", len(readme.split()), "words")
