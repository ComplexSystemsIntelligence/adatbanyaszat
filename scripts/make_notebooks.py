"""A fejezetek Quarto-forrásából Google Colab-jegyzetfüzeteket készít (notebooks/NN-nev.ipynb).

A jegyzetfüzet a fejezet szövegét (Markdown-cellák) és kódját (kódcellák) tartalmazza. A
kereszthivatkozásokat a könyv számozása szerinti szöveggé alakítja, az ábrák és az
interaktív elemek helyére a webkönyvre mutató megjegyzést tesz. A `#| eval: false` jelölésű
(például PyTorch-) cellák `skip-execution` címkét kapnak.

Használat:  python scripts/make_notebooks.py [--repo felhasznalo/tarolo] [--branch main]
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = sorted((ROOT / "chapters").glob("[0-9][0-9]-*.qmd"))
APPENDICES = sorted((ROOT / "appendices").glob("[a-f]-*.qmd"))


def numbering():
    """Kereszthivatkozási címkék → a könyv számozása (fejezet, ábra, táblázat, egyenlet)."""
    refs = {}
    for i, f in enumerate(CHAPTERS, start=1):
        _scan(f.read_text(encoding="utf-8"), str(i), refs)
    for f in APPENDICES:
        _scan(f.read_text(encoding="utf-8"), f.name[0].upper(), refs)
    return refs


def _scan(text, prefix, refs):
    m = re.search(r"^# .*?\{#(sec-[\w-]+)", text, re.M)
    if m:
        refs[m.group(1)] = prefix
    sub = subsub = 0
    counters = {"fig": 0, "tbl": 0, "eq": 0}
    for line in text.splitlines():
        if line.startswith("## ") and ".unnumbered" not in line:
            sub += 1
            subsub = 0
            h = re.search(r"\{#(sec-[\w-]+)", line)
            if h:
                refs[h.group(1)] = f"{prefix}.{sub}"
        elif line.startswith("### ") and ".unnumbered" not in line:
            subsub += 1
            h = re.search(r"\{#(sec-[\w-]+)", line)
            if h:
                refs[h.group(1)] = f"{prefix}.{sub}.{subsub}"
        for kind in counters:
            labs = re.findall(r"\{#(" + kind + r"-[\w-]+)[\s}]", line) + re.findall(r"^#\| label: (" + kind + r"-[\w-]+)", line)
            for lab in labs:
                counters[kind] += 1
                refs[lab] = f"{prefix}.{counters[kind]}"



def number_headings(text, chap):
    """A fejezetcím elhagyása (a jegyzetfüzet fejléce tartalmazza) és az alfejezetek
    számozása a könyvvel egyezően (a .unnumbered címek számozatlanok maradnak)."""
    out, sub, subsub, fence, h1 = [], 0, 0, False, False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fence = not fence
        if not fence:
            if line.startswith("# ") and not h1:
                h1 = True
                continue
            if line.startswith("## ") and ".unnumbered" not in line:
                sub, subsub = sub + 1, 0
                line = f"## {chap}.{sub} " + line[3:]
            elif line.startswith("### ") and ".unnumbered" not in line:
                subsub += 1
                line = f"### {chap}.{sub}.{subsub} " + line[4:]
        out.append(line)
    return "".join(out)


def clean_markdown(md, refs):
    md = re.sub(r"\{\{<.*?>\}\}", "", md)                                  # rövidkódok
    md = re.sub(r"^:::.*$", "", md, flags=re.M)                            # div-kerítések
    md = re.sub(r"!\[(.*?)\]\(\.\./figures/build/(.*?)\.svg\)\{.*?\}",
                lambda m: f"*[Ábra a webkönyvben: {m.group(1)[:90]}…]*", md, flags=re.S)
    md = re.sub(r"\[-@([\w-]+)\]", lambda m: refs.get(m.group(1), "?"), md)
    md = re.sub(r"\[@([\w-]+)(;\s*@[\w-]+)*\]", "", md)                     # irodalmi hivatkozások
    md = re.sub(r"@([a-z][a-z0-9]+[0-9]{4}[a-z]*)", r"\1", md)
    md = re.sub(r"\{#[\w-]+\}", "", md)
    md = re.sub(r"\{\.unnumbered\}", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def cells_from_qmd(text, refs):
    cells, buf = [], []
    parts = re.split(r"(```\{python\}.*?```)", text, flags=re.S)
    for part in parts:
        if part.startswith("```{python}"):
            if buf:
                md = clean_markdown("".join(buf), refs)
                if md:
                    cells.append(("markdown", md, []))
                buf = []
            body = part[len("```{python}"):-3].strip("\n")
            opts = [l for l in body.splitlines() if l.startswith("#|")]
            code = "\n".join(l for l in body.splitlines() if not l.startswith("#|")).strip()
            tags = ["skip-execution"] if any("eval: false" in o for o in opts) else []
            if tags:
                code = "# Ez a cella a PyTorch csomagot igényli (Colabban előre telepítve).\n" + code
            cells.append(("code", code, tags))
        else:
            buf.append(part)
    if buf:
        md = clean_markdown("".join(buf), refs)
        if md:
            cells.append(("markdown", md, []))
    return cells


def notebook(cells, title, nb_name, repo, branch, site):
    def md(src):
        return {"cell_type": "markdown", "metadata": {}, "source": src}

    def code(src, tags=()):
        meta = {"tags": list(tags)} if tags else {}
        return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [], "source": src}

    head = [
        md(f"# {title}\n\n*Abonyi János: Adatbányászat – a hatékonyság eszköze. Elmélet és gyakorlat Pythonban "
           f"(2. kiadás, 2026).* A fejezet webes változata: <{site}>\n\n"
           f"[![Megnyitás Colabban](https://colab.research.google.com/assets/colab-badge.svg)]"
           f"(https://colab.research.google.com/github/{repo}/blob/{branch}/notebooks/{nb_name}.ipynb)\n\n"
           "A szöveg CC BY 4.0, a kód MIT licenc alatt használható fel."),
        code("# A könyv segédcsomagjának telepítése (Colabban; helyi futtatásnál: pip install -e .)\n"
             "import sys\n"
             "if 'google.colab' in sys.modules:\n"
             f"    !pip install -q git+https://github.com/{repo}.git"),
    ]
    body = [md(src) if kind == "markdown" else code(src, tags) for kind, src, tags in cells]
    return {"cells": head + body,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "nbformat": 4, "nbformat_minor": 5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="ComplexSystemsIntelligence/adatbanyaszat")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--site", default="https://complexsystemsintelligence.github.io/adatbanyaszat/")
    a = ap.parse_args()
    refs = numbering()
    out = ROOT / "notebooks"
    out.mkdir(exist_ok=True)
    lista = []
    for i, f in enumerate(CHAPTERS, start=1):
        text = f.read_text(encoding="utf-8")
        title = re.search(r"^# (.*?)\s*\{", text, re.M).group(1)
        cells = cells_from_qmd(number_headings(text, i), refs)
        if not any(k == "code" for k, _, _ in cells):
            continue
        nb = notebook(cells, f"{i}. {title}", f.stem, a.repo, a.branch, a.site + "chapters/" + f.stem + ".html")
        (out / f"{f.stem}.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        lista.append((f.stem, f"{i}. {title}"))
    readme = ["# Colab-jegyzetfüzetek", "",
              "A könyv fejezeteinek kódja futtatható jegyzetfüzetekként. A jegyzetfüzeteket a "
              "`scripts/make_notebooks.py` állítja elő a fejezetek forrásából – kézzel ne szerkesszük őket.", "",
              "| Fejezet | Megnyitás |", "|---|---|"]
    for stem, title in lista:
        readme.append(f"| {title} | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
                      f"(https://colab.research.google.com/github/{a.repo}/blob/{a.branch}/notebooks/{stem}.ipynb) |")
    (out / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(f"{len(lista)} jegyzetfüzet készült a(z) {out} mappában.")


if __name__ == "__main__":
    main()
