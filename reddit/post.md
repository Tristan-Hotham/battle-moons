**Title:** [OC] I worked out the Moon over 9,877 battles, from Hastings to D-Day. Battles fall on every phase of the Moon almost equally

**Body:**

Every battle in Wikidata with an exact day and a place, the Moon's phase at the battle site that day, and the moonlight of the night before, compared with random days from the same centuries (2,000 simulations).

- Each eighth of the lunar month holds 11.8% to 13.0% of battles, against 12.5% for random days. No era shows a lunar rhythm.
- A faint lean to the bright Moon: 51.1% lit on the average battle day against 50.0%. About 2 battles in 100 timed for a full Moon would do it, and it fades if same-day sub-battles are counted once.
- D-Day (100% lit) and Second El Alamein (99%) were full-Moon battles by design; the Somme, Trafalgar and Naseby fell at new Moon; Hastings and Agincourt at last quarter.
- The hard part was calendars: 346 pre-1582 dates in Wikidata carry a Gregorian flag but are Julian dates, and English Civil War dates are often Old Style. Ten days move the Moon a third of its cycle.
- Checks: Pydna (lunar eclipse the night before, 168 BC) comes out full; Halys (solar eclipse, 585 BC) and Isandlwana (partial solar eclipse, 1879) new.

Interactive map (phase filter, year range, tap a battle for its Moon): https://maps.tristanhotham.com/battle-moons/

**Source comment:**

Data: Wikidata (CC0) via QLever. Moon: astronomy-engine, cross-checked with PyEphem. Tools: Python (numpy, scipy, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/battle-moons
