# Fighting by moonlight

The phase of the Moon on the day, and the moonlight of the night before, at the site of every battle in Wikidata with a date to the day and a place: 9,877 battles from AD 69 to 2026 after calendar checks, tested against random days from each battle's own century.

Interactive page: https://maps.tristanhotham.com/battle-moons/
Paper: https://doi.org/10.5281/zenodo.24089704
Blog post: https://blog.tristanhotham.com/2026/10/31/battle-moons/
Code and data: https://github.com/Tristan-Hotham/battle-moons

## Headline results

- Battles fall on every phase of the Moon almost equally: each eighth of the lunar month holds 11.8% to 13.0% of battles (12.5% expected); the eight-bin test does not differ from chance (simulated p = 0.20). No era shows a pattern.
- A faint lean to the bright half of the month: mean lit fraction 51.1% against 50.0% for random days; 10.6% of battles within 1.5 days of full Moon against 10.0% (Rayleigh p = 0.016). About 2% of battles timed for a full Moon would explain it, and it is not robust (p = 0.054 counting one battle per date, 0.16 with only battles' own coordinates).
- The night before: the Moon was up for 5.19 of 10.19 dark hours against 5.08 on season-matched random nights (about 6 minutes more); no difference in whether it was up at dawn.
- Famous cases: D-Day and Second El Alamein at full Moon, as planned; Gettysburg and La Noche Triste full; Hastings and Agincourt last quarter; the Somme, Trafalgar and Naseby new Moon. Eclipse checks: Pydna full, Halys and Isandlwana new.
- Calendars: Wikidata's RDF values are proleptic Gregorian with a flag for the calendar of entry; 346 pre-1582 dates flagged Gregorian are Julian dates and were converted; British Old Style dates before 1752 were settled by hand (31, plus Kosovo 1389 corrected) or left out (175). All 21 hand-checked famous dates agree.

| Phase | Battles | Expected | Share |
|---|---|---|---|
| New moon | 1,169 | 1,213 | 11.8% |
| Waxing crescent | 1,189 | 1,231 | 12.0% |
| First quarter | 1,224 | 1,256 | 12.4% |
| Waxing gibbous | 1,280 | 1,238 | 13.0% |
| Full moon | 1,274 | 1,216 | 12.9% |
| Waning gibbous | 1,278 | 1,235 | 12.9% |
| Last quarter | 1,248 | 1,254 | 12.6% |
| Waning crescent | 1,215 | 1,235 | 12.3% |

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: MapLibre on OpenFreeMap Positron, battles coloured by phase, phase filter, year range, layers, live moon-phase wheel, popups with the Moon and the night before. |
| `header.png` | Social card, 1200 x 630. |
| `data/battles.csv` | Every item (12,295): settled Gregorian (and Julian) date, calendar flag and rule, test flag, siege, point, phase, lit share, age, days from full, darkness and moonlight the night before. |
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

Hotham, T. (2026) Fighting by moonlight: the phase of the Moon on the days of 9,877 battles. Zenodo. 10.5281/zenodo.24089704

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
