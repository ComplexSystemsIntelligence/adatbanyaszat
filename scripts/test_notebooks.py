"""A Colab-jegyzetfüzetek végrehajtásának ellenőrzése (CI-ben is fut).

Használat:  python scripts/test_notebooks.py [notebooks/09-osztalyozas.ipynb ...]
A `skip-execution` címkéjű cellákat (PyTorch) kihagyja.
"""
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "notebooks").glob("*.ipynb"))
hibak = 0
for f in files:
    nb = nbformat.read(f, as_version=4)
    nb.cells = [c for c in nb.cells if "skip-execution" not in c.get("metadata", {}).get("tags", [])]
    t0 = time.time()
    try:
        NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
        print(f"ok    {f.name}  ({time.time() - t0:.0f} s)")
    except Exception as e:                       # noqa: BLE001
        hibak += 1
        print(f"HIBA  {f.name}: {str(e).splitlines()[-1][:200]}")
sys.exit(1 if hibak else 0)
