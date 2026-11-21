"""PannonShop – a könyv üzleti futó esete.

Egy kitalált magyar webáruház két évnyi tranzakciós adatát állítja elő, az
Online Retail II (UCI, Chen és mtsai, 2012) adatsor sémáját követve. Mivel az adatokat
mi generáljuk, a "valódi" háttérstruktúra (vevőszegmensek, lemorzsolódás, beültetett
vásárlási szabályok, rendellenes tranzakciók) ismert, így a módszerek eredménye
ellenőrizhető. A generálás determinisztikus: ugyanaz a `seed` ugyanazt az adatot adja.

Fő függvény: :func:`generate_shop`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Termékkatalógus: kategória -> alkategória -> (termék, átlagár Ft)
# ---------------------------------------------------------------------------
CATALOG: dict[str, dict[str, list[tuple[str, float]]]] = {
    "Kávé és tea": {
        "Kávé": [("Kávébab 1 kg", 7990), ("Őrölt kávé 250 g", 2490), ("Kávékapszula 30 db", 3290),
                 ("Koffeinmentes kávé 250 g", 2790)],
        "Tea": [("Zöld tea 50 filter", 1490), ("Fekete tea 50 filter", 1290), ("Gyümölcstea 40 g", 1190),
                ("Matcha por 30 g", 3990)],
        "Kiegészítő": [("Vízkőoldó 500 ml", 1990), ("Tejhabosító kancsó", 4490), ("Kávéfilter papír 100 db", 890)],
    },
    "Háztartási gépek": {
        "Kávégép": [("Kávéfőző gép", 89990), ("Kotyogós kávéfőző", 8990), ("Kávédaráló", 19990)],
        "Konyhai gép": [("Vízforraló", 12990), ("Turmixgép", 24990), ("Kenyérpirító", 14990)],
    },
    "Konyhai eszközök": {
        "Edény": [("Teáskanna", 6990), ("Öntöttvas serpenyő", 15990), ("Fazékkészlet", 29990)],
        "Eszköz": [("Szilikon spatula", 1490), ("Konyhai mérleg", 6490), ("Késkészlet", 18990),
                   ("Vágódeszka", 4990)],
        "Bögre": [("Porcelán bögre", 2490), ("Termosz bögre", 5990), ("Eszpresszó csészekészlet", 7990)],
    },
    "Dekoráció": {
        "Gyertya": [("Illatgyertya", 3490), ("Teamécses 50 db", 1990), ("Gyertyatartó", 4990)],
        "Lakástextil": [("Díszpárna", 5990), ("Pléd", 9990), ("Asztali futó", 4490)],
        "Ünnepi": [("Adventi koszorú", 7990), ("Karácsonyi égősor", 6990), ("Karácsonyfadísz készlet", 5490)],
    },
    "Ajándék": {
        "Csomagolás": [("Ajándékcsomagolás", 990), ("Díszdoboz", 1990), ("Ajándékkísérő kártya", 490)],
        "Ajándéktárgy": [("Ajándékutalvány 10 000 Ft", 10000), ("Kerámia hűtőmágnes", 1290),
                         ("Fotóalbum", 6990)],
    },
    "Írószer": {
        "Papír": [("Pontozott füzet A5", 1990), ("Határidőnapló", 4990), ("Jegyzettömb", 990)],
        "Íróeszköz": [("Tollkészlet", 2990), ("Töltőtoll", 12990), ("Kiemelő 4 db", 1490)],
    },
}

#: Beültetett vásárlási szabályok: ha a kosárban van az előzmény, az utód ilyen
#: valószínűséggel bekerül. Ezeket a 6. fejezet algoritmusainak meg kell találniuk.
PLANTED_RULES: list[tuple[tuple[str, ...], str, float]] = [
    (("Kávéfőző gép",), "Kávébab 1 kg", 0.70),
    (("Kávéfőző gép",), "Vízkőoldó 500 ml", 0.45),
    (("Kávédaráló",), "Kávébab 1 kg", 0.60),
    (("Teáskanna",), "Zöld tea 50 filter", 0.55),
    (("Teáskanna",), "Fekete tea 50 filter", 0.40),
    (("Pontozott füzet A5",), "Tollkészlet", 0.50),
    (("Tejhabosító kancsó",), "Kávébab 1 kg", 0.50),
    (("Illatgyertya",), "Gyertyatartó", 0.35),
]

SEGMENTS = {
    # név: (arány, éves rendelésszám-várható érték, kosárméret-várható érték,
    #       mennyiségi szorzó, éves lemorzsolódási ráta, kategóriapreferencia)
    "törzsvásárló":  (0.22, 9.0, 4.0, 1.0, 0.15, {"Kávé és tea": 3, "Konyhai eszközök": 2, "Írószer": 1}),
    "alkalmi":       (0.38, 1.6, 2.5, 1.0, 0.55, {"Ajándék": 2, "Dekoráció": 2, "Konyhai eszközök": 1}),
    "akcióvadász":   (0.20, 3.5, 3.5, 1.3, 0.35, {"Háztartási gépek": 2, "Dekoráció": 2, "Konyhai eszközök": 2}),
    "viszonteladó":  (0.05, 6.0, 9.0, 12.0, 0.10, {"Kávé és tea": 3, "Ajándék": 2, "Dekoráció": 2}),
    "lemorzsolódó":  (0.15, 5.0, 3.0, 1.0, 2.50, {"Kávé és tea": 2, "Írószer": 2, "Ajándék": 1}),
}

REGIONS = {
    "Közép-Magyarország": 0.34, "Közép-Dunántúl": 0.11, "Nyugat-Dunántúl": 0.10,
    "Dél-Dunántúl": 0.08, "Észak-Magyarország": 0.09, "Észak-Alföld": 0.11, "Dél-Alföld": 0.10,
    "Ausztria": 0.03, "Szlovákia": 0.02, "Németország": 0.02,
}

PROMO_WEEKS = {  # akciós időszakok (ISO-hét): Black Friday és január eleji kiárusítás
    2024: [2, 3, 47, 48], 2025: [2, 3, 47, 48],
}


@dataclass
class ShopData:
    """A generált adatok és a háttérigazság egy csomagban."""
    transactions: pd.DataFrame
    products: pd.DataFrame
    customers: pd.DataFrame
    reviews: pd.DataFrame
    truth: dict = field(default_factory=dict)


def _product_table() -> pd.DataFrame:
    rows = []
    code = 10001
    for cat, subs in CATALOG.items():
        for sub, items in subs.items():
            for name, price in items:
                rows.append({"StockCode": str(code), "Description": name, "Kategoria": cat,
                             "Alkategoria": sub, "ListaAr": float(price)})
                code += 1
    return pd.DataFrame(rows)


def _seasonality(dates: pd.DatetimeIndex) -> np.ndarray:
    """Napi relatív forgalmi intenzitás: éves (karácsonyi csúcs, nyári visszaesés) és heti mintázat."""
    doy = dates.dayofyear.values
    yearly = 1.0 + 0.25 * np.cos(2 * np.pi * (doy - 15) / 365.25)          # tél > nyár
    xmas = 1.0 + 1.6 * np.exp(-0.5 * ((doy - 345) / 12.0) ** 2)             # december közepe
    weekly = np.array([0.95, 0.92, 0.95, 1.0, 1.08, 1.12, 0.98])[dates.dayofweek.values]
    return yearly * xmas * weekly


def generate_shop(seed: int = 2026, n_customers: int = 3000,
                  start: str = "2024-01-01", end: str = "2025-12-31") -> ShopData:
    """A PannonShop adatainak előállítása.

    Parameters
    ----------
    seed : int
        Véletlenszám-generátor kezdőértéke (reprodukálhatóság).
    n_customers : int
        Regisztrált vevők száma.
    start, end : str
        A vizsgált időszak első és utolsó napja.

    Returns
    -------
    ShopData
        ``transactions`` (számlatételek, az Online Retail II sémájában),
        ``products``, ``customers``, ``reviews`` és ``truth`` (a háttérigazság).
    """
    rng = np.random.default_rng(seed)
    products = _product_table()
    name2code = dict(zip(products.Description, products.StockCode))
    days = pd.date_range(start, end, freq="D")
    season = _seasonality(days)
    season = season / season.mean()
    horizon_years = len(days) / 365.25

    # ---------------- vevők ----------------
    seg_names = list(SEGMENTS)
    seg_p = np.array([SEGMENTS[s][0] for s in seg_names])
    seg = rng.choice(seg_names, size=n_customers, p=seg_p / seg_p.sum())
    region_names = list(REGIONS)
    reg_p = np.array(list(REGIONS.values()))
    region = rng.choice(region_names, size=n_customers, p=reg_p / reg_p.sum())
    # regisztráció: az időszak első 60%-ában egyenletesen
    reg_day = rng.integers(0, int(0.6 * len(days)), size=n_customers)
    reg_day[rng.random(n_customers) < 0.35] = 0  # már az időszak elején meglévő vevők
    churn_rate = np.array([SEGMENTS[s][4] for s in seg])
    lifetime_days = rng.exponential(365.25 / churn_rate)
    churn_day = reg_day + lifetime_days
    customers = pd.DataFrame({
        "CustomerID": np.arange(12001, 12001 + n_customers).astype(str),
        "Regio": region,
        "Regisztracio": days[reg_day],
    })

    # ---------------- rendelések ----------------
    cat_names = list(CATALOG)
    prod_by_cat = {c: products.index[products.Kategoria == c].to_numpy() for c in cat_names}
    promo_mask = np.array([d.isocalendar().week in PROMO_WEEKS.get(d.year, []) for d in days])

    lines = []
    inv_no = 240001
    for i in range(n_customers):
        s = seg[i]
        _, rate, basket_mu, qty_mult, _, pref = SEGMENTS[s]
        lo = reg_day[i]
        hi = int(min(len(days) - 1, churn_day[i]))
        if hi <= lo:
            hi = lo + 1 if lo + 1 < len(days) else lo
        intensity = season[lo:hi + 1].copy()
        if s == "akcióvadász":
            intensity = intensity * np.where(promo_mask[lo:hi + 1], 6.0, 0.6)
        lam = rate / 365.25 * intensity
        n_orders_day = rng.poisson(lam)
        order_days = np.repeat(np.arange(lo, hi + 1), n_orders_day)
        if i < 40:  # garantáljunk legalább egy rendelést néhány korai vevőnek
            order_days = np.append(order_days, lo)
        w = np.array([pref.get(c, 0.4) for c in cat_names], dtype=float)
        w /= w.sum()
        for d in order_days:
            k = max(1, rng.poisson(basket_mu - 1) + 1)
            cats = rng.choice(cat_names, size=k, p=w)
            items = {int(rng.choice(prod_by_cat[c])) for c in cats}
            # decemberben ajándékcsomagolás gyakran kerül a kosárba
            if days[d].month == 12 and rng.random() < 0.35:
                items.add(int(products.index[products.Description == "Ajándékcsomagolás"][0]))
            # beültetett szabályok
            names = set(products.Description.values[list(items)])
            for ante, cons, p in PLANTED_RULES:
                if set(ante) <= names and rng.random() < p:
                    items.add(int(products.index[products.Description == cons][0]))
            hour = int(np.clip(rng.normal(14, 4), 6, 23))
            ts = days[d] + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)))
            disc = 0.8 if (promo_mask[d] and rng.random() < 0.7) else 1.0
            for it in items:
                base_q = rng.geometric(0.6)
                q = int(np.ceil(base_q * qty_mult * rng.uniform(0.6, 1.4))) if qty_mult > 1 else int(base_q)
                price = products.ListaAr.values[it] * disc
                lines.append((f"S{inv_no}", products.StockCode.values[it],
                              products.Description.values[it], q, ts, round(price, 0),
                              customers.CustomerID.values[i], region[i]))
            inv_no += 1

    tx = pd.DataFrame(lines, columns=["Invoice", "StockCode", "Description", "Quantity",
                                      "InvoiceDate", "Price", "CustomerID", "Regio"])

    # ---------------- vendégvásárlások (hiányzó vevőazonosító) ----------------
    guest_inv = tx.Invoice.drop_duplicates().sample(frac=0.07, random_state=seed).values
    tx.loc[tx.Invoice.isin(guest_inv), "CustomerID"] = np.nan

    # ---------------- adatminőségi hibák ----------------
    # sztornó: a számlák ~2%-a "C" előtagú negatív tükörszámlát kap
    canc_inv = tx.Invoice.drop_duplicates().sample(frac=0.02, random_state=seed + 1).values
    canc = tx[tx.Invoice.isin(canc_inv)].copy()
    canc["Invoice"] = "C" + canc.Invoice.str[1:]
    canc["Quantity"] = -canc.Quantity
    canc["InvoiceDate"] = (canc.InvoiceDate + pd.to_timedelta(rng.integers(1, 72, len(canc)), unit="h")).clip(upper=pd.Timestamp(end) + pd.Timedelta(hours=23))
    # postaköltség-sorok (nem termék!)
    post_inv = tx.Invoice.drop_duplicates().sample(frac=0.15, random_state=seed + 2).values
    post = (tx[tx.Invoice.isin(post_inv)].groupby("Invoice", as_index=False).first())
    post["StockCode"], post["Description"], post["Quantity"], post["Price"] = "POST", "Postaköltség", 1, 1490.0
    # duplikált sorok és szöveges zaj a leírásban
    dup = tx.sample(frac=0.004, random_state=seed + 3)
    tx = pd.concat([tx, canc, post, dup], ignore_index=True)
    noisy = rng.random(len(tx)) < 0.01
    tx.loc[noisy, "Description"] = tx.loc[noisy, "Description"].str.upper() + "  "
    # néhány nulla árú (ajándék) és hibásan rögzített extrém ár
    zero = rng.random(len(tx)) < 0.002
    tx.loc[zero, "Price"] = 0.0
    typo = rng.random(len(tx)) < 0.0005
    tx.loc[typo, "Price"] = tx.loc[typo, "Price"] * 100

    # ---------------- rendellenes (csalásgyanús) rendelések – 11. fejezet ----------------
    n_fraud = 25
    fraud_rows = []
    fraud_inv = []
    for j in range(n_fraud):
        d = days[rng.integers(len(days) // 3, len(days))]
        ts = d + pd.Timedelta(hours=int(rng.choice([1, 2, 3, 4])), minutes=int(rng.integers(0, 60)))
        cid = str(19001 + j)  # új, korábban nem látott vevő
        inv = f"S{inv_no}"
        inv_no += 1
        fraud_inv.append(inv)
        for it in rng.choice(products.index[products.ListaAr > 15000], size=rng.integers(2, 5), replace=False):
            fraud_rows.append((inv, products.StockCode.values[it], products.Description.values[it],
                               int(rng.integers(8, 30)), ts, products.ListaAr.values[it], cid,
                               rng.choice(["Németország", "Ausztria", "Szlovákia"])))
    tx = pd.concat([tx, pd.DataFrame(fraud_rows, columns=tx.columns)], ignore_index=True)

    tx = tx.sort_values(["InvoiceDate", "Invoice"]).reset_index(drop=True)
    tx["InvoiceDate"] = pd.to_datetime(tx.InvoiceDate)

    # ---------------- vásárlói értékelések (13. fejezet) ----------------
    reviews = _generate_reviews(rng, products, tx, n=3000)

    truth = {
        "segment": pd.Series(seg, index=customers.CustomerID, name="szegmens"),
        "churn_date": pd.Series(days[0] + pd.to_timedelta(churn_day, unit="D"),
                                index=customers.CustomerID, name="lemorzsolodas"),
        "planted_rules": PLANTED_RULES,
        "fraud_invoices": fraud_inv,
        "cancel_invoices": ["C" + s[1:] for s in canc_inv],
        "promo_weeks": PROMO_WEEKS,
    }
    customers["Szegmens_valodi"] = seg  # csak ellenőrzésre! a modellek ne használják
    return ShopData(transactions=tx, products=products, customers=customers,
                    reviews=reviews, truth=truth)


# ---------------------------------------------------------------------------
# Szöveges vásárlói vélemények: szempontonként (termék, szállítás, ár, ügyfélszolgálat)
# összerakott mondatok. A csillagszám a szempontok súlyozott hangulatából adódik, így a
# szöveg és az értékelés kapcsolata erős, de nem tökéletes – ahogy a valóságban.
# ---------------------------------------------------------------------------
_ASPECT = {
    "termek": {
        +1: ["Nagyon elégedett vagyok {a} {t} termékkel.", "{A} {t} kiváló minőségű.",
             "{A} {t} pontosan olyan, mint a képen.", "Gyönyörű kivitel, {a} {t} ajándéknak is tökéletes.",
             "{A} {t} hibátlanul működik.", "Jobb {a} {t}, mint amire számítottam.",
             "Strapabíró, igényes {t}.", "{A} {t} remekül bevált a mindennapokban."],
        0:  ["Átlagos {t}, megfelel a célnak.", "{A} {t} rendben van, de nem különleges.",
             "Közepes minőségű {t}.", "{A} {t} használható, bár vannak hiányosságai."],
        -1: ["Csalódás volt {a} {t}.", "{A} {t} két hét után elromlott.", "Rossz minőségű {a} {t}.",
             "{A} {t} egyáltalán nem olyan, mint a leírásban.", "Hamar kopik {a} {t}.",
             "Nem működik rendesen {a} {t}.", "{A} {t} gyenge anyagból készült."],
    },
    "szallitas": {
        +1: ["Gyors volt a szállítás.", "Másnapra megérkezett a csomag.", "Gondos csomagolásban érkezett."],
        0:  ["A szállítás a megígért időn belül megtörtént.", "A futár rendben kihozta."],
        -1: ["A szállítás egy hetet késett.", "Sérült dobozban érkezett.", "A futár nem jött ki időben."],
    },
    "ar": {
        +1: ["Ár-érték arányban verhetetlen.", "Akciósan nagyon kedvező áron vettem.", "Megéri az árát."],
        0:  ["Az ára elfogadható.", "Nem olcsó, de nem is drága."],
        -1: ["Túl drága ahhoz képest, amit nyújt.", "Kidobott pénz volt.", "Máshol olcsóbban kapható."],
    },
    "ugyfelszolgalat": {
        +1: ["Az ügyfélszolgálat gyorsan és kedvesen segített.", "A reklamációt azonnal intézték."],
        0:  ["Az ügyfélszolgálattal nem volt dolgom."],
        -1: ["Az ügyfélszolgálat nem válaszolt a levelemre.", "A reklamációt hetekig húzták."],
    },
}
_CLOSE = {+1: ["Csak ajánlani tudom!", "Biztosan rendelek még.", "Öt csillag.", ""],
          0: ["", "Majd meglátjuk, mennyire tartós."],
          -1: ["Nem ajánlom.", "Soha többet.", "Csalódott vagyok.", ""]}


def _article(word: str) -> str:
    """Határozott névelő: "az" magánhangzóval kezdődő szó előtt, egyébként "a"."""
    return "az" if word[:1].lower() in "aáeéiíoóöőuúüű" else "a"


def _sent(x: float) -> int:
    return 1 if x > 0.45 else (-1 if x < -0.45 else 0)


def _generate_reviews(rng, products, tx, n=3000) -> pd.DataFrame:
    sold = tx[(tx.StockCode != "POST") & tx.CustomerID.notna() & (tx.Quantity > 0)]
    sample = sold.sample(n=min(n, len(sold)), random_state=int(rng.integers(1e9)))
    # termékenként eltérő "valódi" minőség -> eltérő értékelés-eloszlás
    quality = dict(zip(products.StockCode, rng.normal(0.3, 0.8, len(products))))
    rows = []
    for _, r in sample.iterrows():
        name = r.Description.strip().lower()
        s_t = _sent(quality[r.StockCode] + rng.normal(0, 0.8))
        s_d = _sent(rng.normal(0.35, 0.9))
        s_a = _sent(rng.normal(0.1, 0.9))
        s_u = _sent(rng.normal(-0.1, 0.9)) if s_t < 0 and rng.random() < 0.5 else 0
        score = 3.2 + 1.3 * s_t + 0.5 * s_d + 0.45 * s_a + 0.4 * s_u + rng.normal(0, 0.45)
        stars = int(np.clip(np.round(score), 1, 5))
        art = _article(name)
        parts = [rng.choice(_ASPECT["termek"][s_t]).format(t=name, a=art, A=art.capitalize())]
        if rng.random() < 0.6:
            parts.append(rng.choice(_ASPECT["szallitas"][s_d]))
        if rng.random() < 0.45:
            parts.append(rng.choice(_ASPECT["ar"][s_a]))
        if s_u != 0:
            parts.append(rng.choice(_ASPECT["ugyfelszolgalat"][s_u]))
        middle = parts[1:]
        rng.shuffle(middle)
        parts = [parts[0]] + middle
        overall = 1 if stars >= 4 else (-1 if stars <= 2 else 0)
        parts.append(rng.choice(_CLOSE[overall]))
        rows.append({"CustomerID": r.CustomerID, "StockCode": r.StockCode,
                     "Datum": r.InvoiceDate + pd.Timedelta(days=int(rng.integers(3, 20))),
                     "Csillag": stars, "Szoveg": " ".join(p for p in parts if p)})
    out = pd.DataFrame(rows)
    out["Hangulat"] = np.select([out.Csillag >= 4, out.Csillag <= 2], ["pozitív", "negatív"], "semleges")
    return out.reset_index(drop=True)
