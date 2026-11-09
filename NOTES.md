# battle-moons: working notes

Brief: /home/claude/work/new10/BRIEFS.md (study 4) + shared rules (new8, new9 BRIEFS, newdata/BRIEF.md).
Format refs: tower-shadows (MapLibre + Positron pattern), river-names, sunless-valleys, church-orientation.
Scratch: /home/claude/scratch/battle-moons (delete at end).

## Calendar facts found (checked by hand in the raw data)
- QLever/Wikidata RDF time values are already converted to the proleptic Gregorian calendar; the calendar model says what
  the editor entered. Hastings (Julian flag) is stored 1066-10-20 = 14 Oct Julian; Agincourt 1415-11-03 = 25 Oct Julian;
  Crecy 1346-09-03 = 26 Aug Julian; Edgehill 1642-11-02 = 23 Oct OS; Sedgemoor 1685-07-16 = 6 Jul OS; Pydna -0167-06-19 =
  22 Jun 168 BC Julian. So Julian-flagged values are used as they are.
- Gregorian-flagged dates BEFORE 15 Oct 1582 are nearly always Julian dates with the wrong flag: Bosworth 1485-08-22,
  Towton 1461-03-29 (Palm Sunday, Julian), Stamford Bridge 1066-09-25, Mohacs 1526-08-29, Poitiers 1356-09-19, Varna
  1444-11-10, Tewkesbury 1471-05-04, Barnet 1471-04-14, Evesham 1265-08-04, Lechfeld 955-08-10, Karbala 680-10-10 are
  all the usual Julian dates. Rule: reinterpret such values as Julian and convert (335 items).
- British Isles 1583 to 1752 with Gregorian flag: mostly Old Style dates mis-flagged (Naseby 14 Jun, Marston Moor 2 Jul,
  Dunbar 3 Sep, Worcester 3 Sep, Killiecrankie 27 Jul, Sheriffmuir 13 Nov, Prestonpans 21 Sep are all OS), but some are
  correctly converted (Culloden 27 Apr = 16 Apr OS, Falkirk Muir 28 Jan = 17 Jan OS, Aughrim 22 Jul = 12 Jul OS, Boyne
  11 Jul = 1 Jul OS, Beachy Head 10 Jul NS). Rule: flag calendar "uncertain", leave out of the main test, keep on the map.
- Kosovo 1389: Wikidata stores 6 July Gregorian (= 28 June Julian, the modern Vidovdan converted twice); override to 15 June
  1389 Julian. Grunwald (24 July Greg = 15 July Julian) is right: the 1400s gap is nine days, not eight.

## Pipeline (battle-moons)
- 01_battles.py: rows -> one date per item (Gregorian JDN), calendar rule, point (own P625, else median of P276 coords),
  siege flag, sea flag (Natural Earth land + 3 km). 12,295 items kept (13,747 in the raw; 1,452 with no point), 2,021 sieges.
- 02_moon.py: astronomy-engine at the site; phase at local mean noon; night before at 10-min steps. Null nights: 10 per battle,
  same site, random year in the same century, within 15 days of the same date in the year (season-matched: first run with
  century-uniform dates showed battles have 0.46 h shorter nights than random days, i.e. a summer bias that would fake a
  moonlight effect).
- 03_checks.py: PyEphem vs astronomy-engine for 21 famous battles: max 0.3 deg. Pydna = full (eclipse the night before),
  Halys = new (solar eclipse), Gaugamela 10.6 days after full (eclipse 11 days before), Badr 1.5 days after full (17 Ramadan).
- 04_results.py: phase tests with simulated null (2000 data sets of random days in each battle's century; fast Meeus phase,
  checked against astronomy-engine on 98,770 null nights: median 0.12 deg, 99th pct 0.5 deg).
- Phase palette validated with the dataviz validator: CVD and normal-vision separation pass; lightness band fails by design (dark = new, gold = full); moon icons give a second encoding.

## Results (battle-moons)
- 9,877 battles in the test. 8-bin chi2 p = 0.20 (simulated); Rayleigh p = 0.016 toward 182 deg; mean lit 51.1% vs 50.0%;
  near full (1.5 d) 10.6% vs 10.0% (~63 battles). Fragile: one-per-date p 0.058, own coords p 0.13, post-1582 p 0.066.
- Night before (season-matched null): Moon up 5.19 of 10.19 dark h vs 5.08 (+6 min, p ~0.004). Up at sunrise 49.9% vs 49.9%.
- No era significant. WWII: full bin 136 vs 113.9 expected (Rayleigh p 0.07).
- Isandlwana (22 Jan 1879, partial solar eclipse seen) = new moon: extra independent check.
- First (century-uniform) null for moonlight: battle nights 0.46 h shorter than random nights (summer bias) -> season matching.

## References to verify (battle-moons)
- Bast & Buchhold 2017 QLever CIKM pp 647-656; Vrandecic & Krotzsch 2014 CACM 57(10) 78-85; Meeus 1998 Astronomical
  Algorithms 2nd ed; Fisher 1993 Statistical Analysis of Circular Data; Reingold & Dershowitz 2018 Calendrical Calculations:
  The Ultimate Edition; Stephenson 1997 Historical Eclipses and Earth's Rotation; Herodotus 1.74; Livy 44.37.
- Claims from general knowledge to verify: D-Day planned for late-rising near-full Moon and rising tide after dawn; El Alamein
  opened at night under bright Moon for mine clearing; Waterloo after a night of heavy rain; partial solar eclipse during
  Isandlwana; La Noche Triste dated 30 June/1 July 1520 Julian.

## Independent review (2026)
- Re-ran 01 to 10 from the raw files: all main results reproduce exactly (9,877 tested; chi2 p 0.20; Rayleigh p 0.016; 51.1% vs 50.0%;
  +6.4 min moonlit; dawn 49.9% vs 49.9%). Sensitivity p values move with Monte Carlo noise (own coords 0.13 -> 0.16, one per date 0.058 -> 0.054).
- 01: date pick among same-day statements made deterministic (was set order, so rule labels varied by hash seed; no change to any date or
  to the test set). Pre-1582 Gregorian-flag count is now 346 (3 sieges also have a Julian statement for the same day). Item counts now come
  from SCR/stats01.json, not hard-coded.
- Independent Moon check (Meeus ch. 49 phase times + astropy/ERFA moon98 illumination) on 20 famous battles: illuminated fraction within
  0.001, days from full within 0.03 d.
- Text fixes: D-Day "late-rising Moon" removed (Sky & Telescope: the Moon rose before sunset on 5 June; the "late-rising" claim is a known
  error); low but rising tide; Isandlwana eclipse "took place", not "was seen" (it went unremarked at the time); "at most 2%" -> "about 2%
  if timed for a full Moon"; British Old Style dates settled by hand are 31 (28 converted + 3 confirmed), Kosovo counted apart; blog
  "from Roman Britain" -> "from the Roman Empire"; multiple-testing caution added on page and blog; Espenak and Meeus (2006) cited.
- Collage: legend added for bar colours and the dashed random-day line.
