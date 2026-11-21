"""A 3. fejezetben kidolgozott adatelőkészítési lépések újrahasznosítható formában.

A későbbi fejezetek ezeket a függvényeket hívják, így minden fejezet ugyanabból a
megtisztított adatból indul.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# PannonShop
# ---------------------------------------------------------------------------
def clean_transactions(tx: pd.DataFrame, products: pd.DataFrame | None = None,
                       keep_cancellations: bool = False) -> pd.DataFrame:
    """A számlatételek tisztítása.

    Lépések: szöveges mezők egységesítése, teljesen azonos (duplikált) sorok törlése,
    a nem termék jellegű tételek (postaköltség) és a nulla árú sorok elhagyása,
    a listaár többszörösével rögzített (elírt) egységárak javítása, valamint – alapértelmezés
    szerint – a sztornózott számlák és sztornóik eltávolítása.
    """
    d = tx.copy()
    d["Description"] = d.Description.str.strip().str.capitalize()
    d = d.drop_duplicates()
    d = d[d.StockCode != "POST"]
    d = d[d.Price > 0]
    if products is not None:
        lista = d.StockCode.map(products.set_index("StockCode").ListaAr)
        elirt = d.Price > 20 * lista
        d.loc[elirt, "Price"] = d.loc[elirt, "Price"] / 100
        # a megnevezést a törzsadatból vesszük (egységes írásmód)
        d["Description"] = d.StockCode.map(products.set_index("StockCode").Description)
    if not keep_cancellations:
        storno = d.Invoice.str.startswith("C")
        eredeti = "S" + d.loc[storno, "Invoice"].str[1:]
        d = d[~storno & ~d.Invoice.isin(set(eredeti))]
    d["Ertek"] = d.Quantity * d.Price
    return d.reset_index(drop=True)


def customer_features(tx_clean: pd.DataFrame, ref_date: str | pd.Timestamp | None = None,
                      products: pd.DataFrame | None = None) -> pd.DataFrame:
    """Vevőszintű jellemzők (RFM és vásárlási szerkezet) a megtisztított számlatételekből.

    R (recency): az utolsó vásárlás óta eltelt napok száma a referencia-dátumig;
    F (frequency): a számlák száma; M (monetary): a teljes nettó vásárlási érték.
    Ezen kívül: átlagos kosárérték, kosárméret, a vásárlások közötti átlagos idő,
    tételenkénti átlagos mennyiség, akciós hetekben történt vásárlások aránya és
    kategóriánkénti költési arányok.
    """
    d = tx_clean[tx_clean.CustomerID.notna()].copy()
    if ref_date is None:
        ref_date = d.InvoiceDate.max().normalize() + pd.Timedelta(days=1)
    ref_date = pd.Timestamp(ref_date)
    d = d[d.InvoiceDate < ref_date]
    inv = (d.groupby(["CustomerID", "Invoice"])
             .agg(datum=("InvoiceDate", "first"), ertek=("Ertek", "sum"),
                  tetel=("StockCode", "nunique"), menny=("Quantity", "mean"))
             .reset_index())
    g = inv.groupby("CustomerID")
    feats = pd.DataFrame({
        "R_nap": (ref_date - g.datum.max()).dt.days,
        "F_szamla": g.size(),
        "M_ertek": g.ertek.sum(),
        "atl_kosarertek": g.ertek.mean(),
        "atl_kosarmeret": g.tetel.mean(),
        "atl_mennyiseg": g.menny.mean(),
        "elso_vasarlas_nap": (ref_date - g.datum.min()).dt.days,
    })
    span = feats.elso_vasarlas_nap - feats.R_nap
    feats["atl_koztes_nap"] = np.where(feats.F_szamla > 1, span / (feats.F_szamla - 1).clip(lower=1), np.nan)
    wk = inv.datum.dt.isocalendar()
    promo = ((wk.week.isin([2, 3, 47, 48])).astype(float)).groupby(inv.CustomerID).mean()
    feats["akcios_arany"] = promo
    if products is not None:
        cat = d.merge(products[["StockCode", "Kategoria"]], on="StockCode")
        share = cat.pivot_table(index="CustomerID", columns="Kategoria", values="Ertek",
                                aggfunc="sum", fill_value=0)
        share = share.div(share.sum(axis=1), axis=0)
        short = {"Kávé és tea": "kave", "Háztartási gépek": "gep", "Konyhai eszközök": "konyha",
                 "Dekoráció": "dekor", "Ajándék": "ajandek", "Írószer": "iroszer"}
        share.columns = ["arany_" + short.get(c, c) for c in share.columns]
        feats = feats.join(share)
    return feats


# ---------------------------------------------------------------------------
# Pannon üzem
# ---------------------------------------------------------------------------
def hampel(x: pd.Series, window: int = 7, k: float = 3.0, min_scale: float | None = None) -> pd.Series:
    """Hampel-szűrő: a mozgó medián körüli k·MAD-on kívüli pontokat jelöli kiugrónak.

    Visszatérési érték: logikai sorozat (True = kiugró). A MAD-ot az 1,4826-os
    szorzóval tesszük normális eloszlás esetén a szórással összemérhetővé. Rövid ablakban
    a helyi MAD-becslés nagyon kicsi is lehet (különösen kerekített adatoknál), ami téves
    jelzésekhez vezet; ezért a skálát alulról korlátozzuk (alapértelmezés szerint a helyi
    MAD-értékek mediánjával).
    """
    med = x.rolling(window, center=True, min_periods=1).median()
    mad = (x - med).abs().rolling(window, center=True, min_periods=1).median() * 1.4826
    if min_scale is None:
        min_scale = float(mad[mad > 0].median())
    scale = mad.clip(lower=min_scale)
    return (x - med).abs() > k * scale


def clean_plant(m: pd.DataFrame, max_gap: int = 3) -> pd.DataFrame:
    """A 10 perces üzemi mérések tisztítása.

    Lépések: a fizikailag lehetetlen értékek (pl. 0 bar nyomás üzem közben) és a
    Hampel-szűrő által jelölt tüskék hiányzóvá alakítása, majd a legfeljebb
    ``max_gap`` hosszú hiányok lineáris interpolációja. A tisztítási leállások
    (``F_betap`` < 1) sorai ``leallas`` jelölést kapnak.
    """
    d = m.copy().set_index("ido")
    sensors = ["T_reaktor", "F_hutoviz", "P_reaktor", "T_hutoviz"]
    d["leallas"] = d.F_betap < 1.0
    for c in sensors:
        s = d[c].copy()
        s[(s <= 0) & ~d.leallas] = np.nan
        s[hampel(s.interpolate(limit=max_gap), window=7, k=5.0) & ~d.leallas] = np.nan
        d[c] = s.interpolate(limit=max_gap, limit_area="inside")
    return d.reset_index()


# ---------------------------------------------------------------------------
# Modellezési táblák a felügyelt tanulási fejezetekhez
# ---------------------------------------------------------------------------
def churn_dataset(tx_clean: pd.DataFrame, products: pd.DataFrame, cutoff: str = "2025-07-01",
                  horizon_days: int = 183, active_days: int = 365) -> pd.DataFrame:
    """Lemorzsolódás-előrejelzési tábla.

    A jellemzőket a ``cutoff`` előtti vásárlásokból számoljuk (a jövőbe nem látunk), a
    célváltozó 1, ha a vevő a ``cutoff`` utáni ``horizon_days`` napban nem vásárolt.
    Csak azokat a vevőket vesszük figyelembe, akik a ``cutoff`` előtti ``active_days`` napban
    legalább egyszer vásároltak (aktív vevők).
    """
    cutoff = pd.Timestamp(cutoff)
    feats = customer_features(tx_clean, cutoff, products)
    feats = feats[feats.R_nap <= active_days]
    jovo = tx_clean[(tx_clean.InvoiceDate >= cutoff) &
                    (tx_clean.InvoiceDate < cutoff + pd.Timedelta(days=horizon_days))]
    vasarolt = set(jovo.CustomerID.dropna())
    feats["lemorzsolodik"] = (~feats.index.isin(vasarolt)).astype(int)
    return feats


def quality_dataset(m_clean: pd.DataFrame, lab: pd.DataFrame, window: str = "60min") -> pd.DataFrame:
    """Laborminták és a mintavétel előtti időablak átlagolt folyamatváltozói egy táblában.

    Visszaad: ido, termek, a folyamatváltozók ablakátlagai, ``c_termek`` (labor),
    ``szennyezes`` (labor) és ``megfelelo`` (minőségi címke).
    """
    num = ["T_kornyezet", "F_betap", "c_betap", "T_betap", "T_reaktor", "T_alapjel",
           "F_hutoviz", "T_hutoviz", "P_reaktor", "P_kevero", "E_fogyasztas"]
    d = m_clean.set_index("ido")[num].rolling(window, min_periods=3).mean()
    out = lab.set_index("ido").join(d, how="left")
    out = out.dropna(subset=num).reset_index()
    out["dT"] = out.T_reaktor - out.T_alapjel
    return out
