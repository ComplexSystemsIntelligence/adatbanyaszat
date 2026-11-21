"""A tároló nevének beállítása a könyv minden konfigurációs fájljában.

Használat:  python scripts/set_repo.py felhasznalo/tarolo [--site https://felhasznalo.github.io/tarolo/]

A parancs frissíti a _quarto.yml, a
CITATION.cff, a .zenodo.json, a README.md, az index.qmd és a függelékek hivatkozásait, majd
újragenerálja a Colab-jegyzetfüzeteket. A borítók (figures/tikz/00-*.tex) és az előnézeti kép
újrafordítása: python scripts/build_figures.py 00-borito 00-hatso-borito és python scripts/make_social_preview.py.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["_quarto.yml", "CITATION.cff", ".zenodo.json", "README.md", "index.qmd",
         "appendices/a-python.qmd", "_extensions/pannon/pannon-shortcodes.lua",
         "scripts/make_notebooks.py", "apps/README.md", "_extensions/pannon/pannon-header.tex",
         "figures/tikz/00-borito.tex", "figures/tikz/00-hatso-borito.tex", "scripts/make_social_preview.py"]

ap = argparse.ArgumentParser()
ap.add_argument("repo", help="GitHub-tároló: felhasznalo/tarolo")
ap.add_argument("--site", help="a GitHub Pages webhely címe (alapértelmezés: https://felhasznalo.github.io/tarolo/)")
a = ap.parse_args()
if not re.fullmatch(r"[\w.-]+/[\w.-]+", a.repo):
    sys.exit("A tároló nevét felhasznalo/tarolo alakban adja meg.")
user, name = a.repo.split("/")
site = a.site or f"https://{user.lower()}.github.io/{name}/"
cfg = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
old_repo = re.search(r'book-repo:\s*"([^"]+)"', cfg).group(1)
old_site = re.search(r'book-site:\s*"([^"]+)"', cfg).group(1)
for f in FILES:
    p = ROOT / f
    if p.exists():
        t = p.read_text(encoding="utf-8").replace(old_site, site).replace(old_repo, a.repo)
        # a borítókon és az előnézeti képen a cím séma és záró perjel nélkül szerepel
        t = t.replace(old_site.split("://", 1)[1].rstrip("/"), site.split("://", 1)[1].rstrip("/"))
        p.write_text(t, encoding="utf-8")
        print("frissítve:", f)
subprocess.run([sys.executable, str(ROOT / "scripts" / "make_notebooks.py"), "--repo", a.repo, "--site", site], check=True)
print(f"Kész: {old_repo} → {a.repo}, {old_site} → {site}")
