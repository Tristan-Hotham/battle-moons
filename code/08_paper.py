"""Step 8: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Fighting_by_Moonlight.pdf and .tex beside the f_*.png figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24089704 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import csv, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Fighting_by_Moonlight"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    return tex(str(v))


A = R["all"]
rows = "".join(f"{PHASES[k]} & {A['obs'][k]:,} & {A['exp'][k]:,.1f} & {A['obs_pc'][k]:.2f} & {A['ratio'][k]:.3f}\\\\\n" for k in range(8))
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Battles by phase of the Moon (eight equal bins centred on the named phases) against the expectation from 2,000 simulated sets of random days.}\\label{tab:bins}"
      "\\begin{tabular}{lrrrr}\\toprule Phase & Battles & Expected & Share (\\%) & Ratio\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
G = [(R["eras"][k]["name"], R["eras"][k]) for k in R["eras"]] + [(R["kinds"][k]["name"], R["kinds"][k]) for k in ("land", "sea", "raid", "ww1", "ww2", "famous") if k in R["kinds"]] + [("Sieges (start date)", R["sieges"])]
rows = "".join(f"{tex(n)} & {g['n']:,} & {100*g['mean_illum']:.1f} & {100*g['mean_illum_exp']:.1f} & {g['near_full_pc']:.1f} & {g['chi2_p_sim']:.2f} & {g['rayleigh_p_sim']:.3f}\\\\\n" for n, g in G)
TG = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Tests by era and kind of battle: number, mean illuminated fraction (\\%) against random days, share within 1.5 days of full Moon (\\%), and simulated $p$ for the $\\chi^2$ and Rayleigh tests (1,000 to 2,000 simulated sets).}\\label{tab:groups}"
      "\\begin{tabular}{lrrrrrr}\\toprule Group & $n$ & Lit & Random & Near full & $\\chi^2$ $p$ & Rayleigh $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(s['name'])} & {s['n']:,} & {100*s['mean_illum']:.1f} & {s['chi2_p_sim']:.2f} & {s['rayleigh_p_sim']:.3f}\\\\\n" for s in R["sens"].values())
TS = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Sensitivity of the phase tests to the calendar rules and the data.}\\label{tab:sens}"
      "\\begin{tabular}{p{8.2cm}rrrr}\\toprule Variant & $n$ & Lit (\\%) & $\\chi^2$ $p$ & Rayleigh $p$\\\\\\midrule\n"
      f"All battles in the test & {A['n']:,} & {100*A['mean_illum']:.1f} & {A['chi2_p_sim']:.2f} & {A['rayleigh_p_sim']:.3f}\\\\\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(f['name'])} & {tex(f['date'].replace(' (Gregorian)', ''))} & {f['phase_ae']:.1f} & {f['phase_ephem']:.1f} & {100*f['illum_ae']:.0f} & {f['days_from_full_ae']:+.1f} & {f['moon_dark_h']:.1f}/{f['dark_h']:.1f}\\\\\n" for f in R["famous"])
TF = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The Moon over famous battles: Gregorian date, phase angle from astronomy-engine and PyEphem, illuminated share (\\%), days from the nearest full Moon, and hours of darkness with the Moon up on the night before (of the hours of darkness).}\\label{tab:famous}"
      "\\begin{tabular}{llrrrrr}\\toprule Battle & Date & AE & PyEphem & Lit & Full & Moonlit/dark\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
cc = list(csv.DictReader(open(f"{DATA}/calendar_checks.csv", encoding="utf-8")))
rows = "".join(f"{tex(r['label'].replace('Battle of ', ''))} & {tex(r['standard_date'])} & {tex(r['pipeline'])} & {r['flag']} & {tex(r['rule'])}\\\\\n" for r in cc)
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Hand checks of the calendar handling: the date in the standard histories, the date the pipeline settles (Gregorian), the flag in Wikidata and the rule applied. For Bannockburn the pipeline gives the first of the two days.}\\label{tab:cal}"
      "\\begin{tabular}{llllr}\\toprule Battle & Standard date & Pipeline (Gregorian) & Flag & Rule\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_BINS", TB), ("TABLE_GROUPS", TG), ("TABLE_SENS", TS), ("TABLE_FAMOUS", TF), ("TABLE_CAL", TC)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24089704", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
