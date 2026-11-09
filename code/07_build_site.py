"""Step 7: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24089704, https://doi.org/10.5281/zenodo.24089704 and https://blog.tristanhotham.com/2026/10/31/battle-moons/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
F = R["F"]
# facts stated in words, checked against the data
assert F["d_day"]["phase_name"] == "Full moon" and -1 < F["d_day"]["days_from_full_ae"] < 0
assert F["second_el_alamein"]["phase_name"] == "Full moon"
assert F["hastings"]["phase_name"] == "Last quarter" and F["agincourt"]["phase_name"] == "Last quarter"
assert F["waterloo"]["phase_name"] == "Waxing gibbous" and F["gettysburg"]["phase_name"] == "Full moon"
assert all(F[k]["phase_name"] == "New moon" for k in ("the_somme", "trafalgar", "naseby", "isandlwana", "halys"))
assert F["pydna"]["phase_name"] == "Full moon" and F["la_noche_triste"]["phase_name"] == "Full moon"
assert R["all"]["chi2_p_sim"] > 0.1 and all(R["eras"][k]["chi2_p_sim"] > 0.1 for k in R["eras"])
assert R["all"]["rayleigh_p_sim"] < 0.05 and R["sens"]["own_point"]["rayleigh_p_sim"] > 0.05
assert abs(R["all"]["mean_dir"] - 180) < 30 and R["calendar_checks"]["agree"] == R["calendar_checks"]["n"]
assert R["night"]["moon_dark_h"]["diff"] > 0 and abs(R["night"]["moon_up_at_sunrise"]["diff"]) < 0.02
assert R["kinds"]["ww2"]["obs"][4] == max(R["kinds"]["ww2"]["obs"])
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261109")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
