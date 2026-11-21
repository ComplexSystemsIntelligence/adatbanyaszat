"""TikZ-ábrák fordítása: figures/tikz/*.tex -> figures/build/*.pdf és *.svg.

Használat:  python scripts/build_figures.py [--force] [név ...]
Követelmény: XeLaTeX (TikZ, pgfplots) és pdftocairo (poppler-utils).
Csak a megváltozott forrásokat fordítja újra (időbélyeg alapján).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "figures" / "tikz"
OUT = ROOT / "figures" / "build"
EXT = ROOT / "_extensions" / "pannon"


def build(tex: Path, force: bool = False) -> bool:
    pdf, svg = OUT / (tex.stem + ".pdf"), OUT / (tex.stem + ".svg")
    deps = [tex, EXT / "pe-tikz.sty"]
    if not force and pdf.exists() and svg.exists() and all(pdf.stat().st_mtime >= d.stat().st_mtime for d in deps):
        return True
    env = dict(os.environ, TEXINPUTS=f"{EXT}{os.pathsep}{SRC}{os.pathsep}")
    tmp = OUT / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                        f"-output-directory={tmp}", tex.name], cwd=SRC, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        log = (tmp / (tex.stem + ".log")).read_text(errors="ignore")
        err = [l for l in log.splitlines() if l.startswith("!")][:3]
        print(f"HIBA  {tex.name}: {' | '.join(err)}")
        return False
    shutil.move(str(tmp / (tex.stem + ".pdf")), pdf)
    subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)], check=True)
    print(f"ok    {tex.stem}")
    return True


def main(argv):
    force = "--force" in argv
    names = [a for a in argv if not a.startswith("--")]
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC.glob("*.tex")) if not names else [SRC / f"{n}.tex" for n in names]
    ok = all([build(f, force) for f in files])
    shutil.rmtree(OUT / "_tmp", ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
