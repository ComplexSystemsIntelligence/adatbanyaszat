"""Kézzel is végigszámolható mini-adatsorok a fejezetek mintapéldáihoz."""
from __future__ import annotations

import numpy as np
import pandas as pd


def minoseg_tabla() -> pd.DataFrame:
    """14 gyártási tétel minősítése – a döntési fák és a naiv Bayes kézi példája (9. fejezet)."""
    rows = [
        # Hőmérséklet, Alapanyag, Műszak, Karbantartva, Minőség
        ("magas",   "A", "nappali",  "nem",  "selejt"),
        ("magas",   "A", "nappali",  "igen", "selejt"),
        ("normál",  "A", "nappali",  "nem",  "jó"),
        ("alacsony", "B", "nappali", "nem",  "jó"),
        ("alacsony", "B", "éjszakai", "nem", "jó"),
        ("alacsony", "B", "éjszakai", "igen", "selejt"),
        ("normál",  "B", "éjszakai", "igen", "jó"),
        ("magas",   "B", "nappali",  "nem",  "selejt"),
        ("magas",   "B", "éjszakai", "nem",  "jó"),
        ("alacsony", "A", "nappali", "nem",  "jó"),
        ("magas",   "A", "éjszakai", "igen", "jó"),
        ("normál",  "B", "nappali",  "igen", "jó"),
        ("normál",  "A", "éjszakai", "nem",  "jó"),
        ("alacsony", "A", "nappali", "igen", "selejt"),
    ]
    return pd.DataFrame(rows, columns=["Homerseklet", "Alapanyag", "Muszak", "Karbantartva", "Minoseg"])


def kosar_mini() -> list[list[str]]:
    """Nyolc vásárlói kosár az Apriori és az FP-growth kézi példájához (6. fejezet)."""
    return [
        ["kávé", "tej", "cukor"],
        ["kávé", "tej"],
        ["tea", "citrom", "cukor"],
        ["kávé", "tej", "keksz"],
        ["tea", "citrom"],
        ["kávé", "cukor", "keksz"],
        ["kávé", "tej", "cukor", "keksz"],
        ["tea", "tej", "keksz"],
    ]


def pontok_mini() -> pd.DataFrame:
    """Hét pont a síkon a hierarchikus és a k-átlag csoportosítás kézi példájához (5. fejezet)."""
    return pd.DataFrame({"x1": [1.0, 1.5, 3.0, 5.0, 3.5, 4.5, 3.5],
                         "x2": [1.0, 2.0, 4.0, 7.0, 5.0, 5.0, 4.5]},
                        index=list("ABCDEFG"))


def regresszio_mini() -> pd.DataFrame:
    """Hat mérés: hűtővízáram (m3/h) és villamosenergia-fogyasztás (kW) – 8. fejezet."""
    return pd.DataFrame({"F_hutoviz": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
                         "E_fogyasztas": [64.1, 66.0, 69.2, 70.1, 73.4, 74.8]})


def idosor_mini() -> tuple[np.ndarray, np.ndarray]:
    """Két rövid, időben eltolt jelalak a dinamikus idővetemítés kézi példájához (12. fejezet)."""
    a = np.array([0.0, 1.0, 3.0, 4.0, 3.0, 1.0, 0.0, 0.0])
    b = np.array([0.0, 0.0, 1.0, 3.0, 4.0, 3.0, 1.0, 0.0])
    return a, b


def szoveg_mini() -> list[str]:
    """Öt rövid dokumentum a TF-IDF kézi példájához (13. fejezet)."""
    return [
        "a kávé friss és a kávé illatos",
        "a tea friss",
        "a szállítás lassú volt",
        "a kávé szállítás gyors volt",
        "illatos tea és friss kávé",
    ]
