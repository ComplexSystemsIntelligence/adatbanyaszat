"""A futó esetek adatainak exportja a data/ mappába (CSV), Excelhez, SQL-hez, más eszközökhöz.

A könyv kódjai az adatokat közvetlenül az `adatbanyaszat` csomagból állítják elő, ezért ezek
a fájlok csak kényelmi célt szolgálnak. Használat:  python scripts/gen_data.py
"""
from pathlib import Path

import adatbanyaszat as ab

D = Path(__file__).resolve().parents[1] / "data"
D.mkdir(exist_ok=True)
s = ab.load_shop()
s.transactions.to_csv(D / "pannonshop_tranzakciok.csv.gz", index=False)
s.products.to_csv(D / "pannonshop_termekek.csv", index=False)
s.customers.drop(columns=["Szegmens_valodi"]).to_csv(D / "pannonshop_vevok.csv", index=False)
s.reviews.to_csv(D / "pannonshop_ertekelesek.csv.gz", index=False)
p = ab.load_plant()
p.measurements.to_csv(D / "pannonuzem_meresek_10perc.csv.gz", index=False)
p.hourly.to_csv(D / "pannonuzem_oras.csv.gz", index=False)
p.alarms.to_csv(D / "pannonuzem_riasztasok.csv", index=False)
p.lab.to_csv(D / "pannonuzem_labor.csv", index=False)
ab.load_shift_log().drop(columns=["esemeny"]).to_csv(D / "pannonuzem_muszaknaplo.csv", index=False)
print("Kész:", sorted(f.name for f in D.iterdir()))
