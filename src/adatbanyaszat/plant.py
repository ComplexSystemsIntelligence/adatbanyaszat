"""Pannon üzem – a könyv mérnöki futó esete.

Egy folyamatos üzemű, kevert tankreaktorban (CSTR) három termékminőséget (A, B, C)
gyártanak kampányokban. A szimulátor egyszerűsített, de fizikailag konzisztens:

* elsőrendű, exoterm reakció Arrhenius-kinetikával, stacionárius CSTR-konverzió
  :math:`X = k\\tau/(1+k\\tau)`;
* hűtőköpeny, amelynek hőátadási tényezője (UA) a lerakódás miatt két tisztítás között
  fokozatosan romlik – nyáron, melegebb hűtővíznél ez a hűtés telítődéséhez vezethet;
* 10 perces mintavétel, mérési zaj, kiesett mérések, 4 óránként laboratóriumi minta;
* ismert időpontokban beültetett hibák (szenzor-drift, betáplálási zavar, szelepakadás,
  hűtővíz-kiesés) és tisztítási leállások.

Mivel a hibák és az üzemállapotok ismertek, az anomália-észlelő, osztályozó és
regressziós módszerek eredménye pontosan kiértékelhető.

Fő függvény: :func:`generate_plant`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

R_GAS = 8.314          # J/(mol K)
EA = 60_000.0          # aktiválási energia, J/mol
K0 = 1.7e9             # preexponenciális tényező, 1/h
DH = 80_000.0          # reakcióhő (exoterm), J/mol
V_REACTOR = 10.0       # m3
RHO_CP = 1161.0        # víz: W/(K · m3/h)
UA0 = 7.0              # tiszta hőcserélő, kW/K
FC_MAX = 9.0           # hűtővíz-szelep maximuma, m3/h

GRADES = {  # termék: (T alapjel °C, betáplálás m3/h, betáplált koncentráció mol/L, keverő kW)
    "A": (82.0, 11.0, 2.0, 15.0),
    "B": (86.0, 10.0, 2.2, 18.0),
    "C": (90.0, 12.0, 1.8, 13.0),
}


@dataclass
class PlantData:
    """A generált üzemi adatok és a háttérigazság."""
    measurements: pd.DataFrame      # 10 perces folyamatadatok
    hourly: pd.DataFrame            # órás összesítés (adattárház, idősor)
    alarms: pd.DataFrame            # riasztásnapló (eseménysor)
    lab: pd.DataFrame               # laboratóriumi minták
    truth: dict = field(default_factory=dict)


def _ar1(rng, n, phi, sigma):
    e = rng.normal(0, sigma * np.sqrt(1 - phi ** 2), n)
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def _lag(x, alpha):
    """Elsőrendű késleltetés (diszkrét szűrő): y_k = y_{k-1} + alpha (x_k - y_{k-1})."""
    y = np.empty_like(x)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = y[i - 1] + alpha * (x[i] - y[i - 1])
    return y


def conversion(T_celsius, F):
    """Stacionárius CSTR-konverzió elsőrendű reakcióra."""
    k = K0 * np.exp(-EA / (R_GAS * (np.asarray(T_celsius) + 273.15)))
    tau = V_REACTOR / np.maximum(F, 1e-6)
    return k * tau / (1 + k * tau)


def generate_plant(seed: int = 2026, start: str = "2025-01-01", days: int = 365,
                   freq_min: int = 10) -> PlantData:
    """A Pannon üzem egyéves folyamatadatainak előállítása.

    Returns
    -------
    PlantData
        ``measurements`` (10 perces mérések), ``hourly`` (órás összesítés),
        ``alarms`` (riasztásnapló), ``lab`` (laborminták) és ``truth`` (hibák, tisztítások).
    """
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=days * 24 * 60 // freq_min, freq=f"{freq_min}min")
    n = len(t)
    hours = (t - t[0]) / pd.Timedelta(hours=1)
    doy = t.dayofyear.values
    hod = t.hour.values + t.minute.values / 60

    # ---------------- környezet ----------------
    T_amb = (11.5 + 11.0 * np.sin(2 * np.pi * (doy - 110) / 365.25)
             + 4.0 * np.sin(2 * np.pi * (hod - 9) / 24) + _ar1(rng, n, 0.995, 1.8))

    # ---------------- termékkampányok ----------------
    grade = np.empty(n, dtype=object)
    i = 0
    seq = []
    while i < n:
        g = rng.choice(list(GRADES), p=[0.45, 0.35, 0.20])
        if seq and g == seq[-1]:
            g = rng.choice([x for x in GRADES if x != g])
        length = int(rng.integers(3, 11) * 24 * 60 / freq_min)
        grade[i:i + length] = g
        seq.append(g)
        i += length
    T_sp = np.array([GRADES[g][0] for g in grade])
    F_nom = np.array([GRADES[g][1] for g in grade])
    c_nom = np.array([GRADES[g][2] for g in grade])
    P_mix_nom = np.array([GRADES[g][3] for g in grade])

    # ---------------- tisztítások és lerakódás ----------------
    clean_days = np.cumsum(rng.integers(42, 58, size=12))
    clean_days = clean_days[clean_days < days - 5]
    clean_idx = [int(d * 24 * 60 / freq_min) for d in clean_days]
    fouling = np.zeros(n)
    last = 0
    for k in range(n):
        if clean_idx and k in clean_idx:
            last = k
        fouling[k] = min(1.0, (k - last) * freq_min / (60 * 24) / 60.0)  # 60 nap alatt telítődik
    UA = UA0 * (1 - 0.40 * fouling)
    stop = np.zeros(n, dtype=bool)  # 8 órás tisztítási leállás
    for k in clean_idx:
        stop[k:k + 8 * 60 // freq_min] = True

    # ---------------- beültetett hibák ----------------
    fault = np.array(["normál"] * n, dtype=object)
    faults = []

    def window(day, dur_h):
        a = int(day * 24 * 60 / freq_min) + int(rng.integers(0, 24 * 60 // freq_min))
        return a, min(n, a + int(dur_h * 60 / freq_min))

    plan = [("szenzor_drift", [40, 190, 300], 120), ("betap_zavar", [75, 230], 48),
            ("szelep_akadas", [120, 265], 72), ("hutoviz_kieses", [150, 163, 178, 191, 204, 216, 229, 243], 5)]
    for name, day_list, dur in plan:
        for d in day_list:
            a, b = window(d, dur)
            fault[a:b] = name
            faults.append({"hiba": name, "kezdet": t[a], "veg": t[b - 1]})
    fault[stop] = "tisztitas"

    # ---------------- betáplálás ----------------
    F = F_nom * (1 + _ar1(rng, n, 0.98, 0.03))
    c_in = c_nom * (1 + _ar1(rng, n, 0.99, 0.025))
    c_in[fault == "betap_zavar"] *= 0.85
    T_in = T_sp - 10 + 0.15 * (T_amb - 12) + _ar1(rng, n, 0.95, 0.4)   # előmelegített betáplálás
    F[stop] = 0.0

    # ---------------- hűtővíz ----------------
    T_cw = 18 + 0.45 * (T_amb - 12) + _ar1(rng, n, 0.97, 0.5)
    T_cw[fault == "hutoviz_kieses"] += 12.0

    # ---------------- szenzor-drift: a mért hőmérséklet a valódinál nagyobb ----------------
    drift = np.zeros(n)
    for f in faults:
        if f["hiba"] == "szenzor_drift":
            m = (t >= f["kezdet"]) & (t <= f["veg"])
            drift[m] = np.linspace(0, 4.0, m.sum())
    # a szabályozó a mért értéket tartja az alapjelen -> a valódi hőmérséklet alacsonyabb
    T_true_target = T_sp - drift + _ar1(rng, n, 0.9, 0.25)

    # ---------------- hőmérleg és hűtés ----------------
    X0 = conversion(T_true_target, F)
    Q_rx = DH * (F / 3600) * (c_in * 1000) * X0 / 1000        # kW
    Q_sens = RHO_CP * F * (T_true_target - T_in) / 1000         # kW
    Q_c = np.maximum(Q_rx - Q_sens, 1.0)
    denom = 2 * RHO_CP / 1000 * (T_true_target - T_cw - Q_c / UA)
    Fc_req = np.where(denom > 0.05, Q_c / np.maximum(denom, 0.05), FC_MAX * 2)
    Fc = np.minimum(Fc_req, FC_MAX)
    # telítődött hűtés -> túlmelegedés
    sat = Fc_req > FC_MAX
    Q_max = UA * (T_true_target - T_cw - Q_c / (2 * RHO_CP / 1000 * FC_MAX))
    dT = np.where(sat, np.clip((Q_c - np.maximum(Q_max, 0)) / (UA + RHO_CP * F / 1000), 0, 15), 0)
    T_true = _lag(T_true_target + dT, 0.35)
    # szelepakadás: fűrészfog-szerű oszcilláció a hűtővízáramban és a hőmérsékletben
    osc = np.where(fault == "szelep_akadas",
                   np.sign(np.sin(2 * np.pi * hours / 0.75)) * 1.1, 0.0)
    Fc = _lag(Fc, 0.5) + osc + rng.normal(0, 0.05, n)
    T_true = T_true + 0.6 * np.where(fault == "szelep_akadas", np.sin(2 * np.pi * hours / 0.75 - 1.0), 0.0)
    Fc[stop] = 0.0

    X = conversion(T_true, F)
    c_out = c_in * X                                             # termékkoncentráció, mol/L
    impurity = 0.45 + 0.25 * np.exp(0.45 * np.clip(T_true - T_sp, -10, 12)) + _ar1(rng, n, 0.9, 0.04)
    T_meas = T_true + drift + rng.normal(0, 0.15, n)
    P = 2.0 + 0.025 * (T_true - 80) + 0.04 * F + _ar1(rng, n, 0.9, 0.03)
    P_mix = P_mix_nom * (1 + 0.01 * (c_in - c_nom)) + rng.normal(0, 0.4, n)
    P_mix[stop] = 0.0
    E = 35 + P_mix + 2.4 * Fc + 0.09 * Q_sens + rng.normal(0, 1.2, n)

    # specifikáció: termékenként a névleges konverzióhoz tartozó koncentráció ±5%
    c_target = np.array([GRADES[g][2] for g in grade]) * conversion(T_sp, F_nom)
    in_spec = (np.abs(c_out - c_target) <= 0.05 * c_target) & (impurity <= 1.5)

    df = pd.DataFrame({
        "ido": t,
        "termek": grade,
        "T_kornyezet": T_amb.round(2),
        "F_betap": F.round(3),
        "c_betap": c_in.round(4),
        "T_betap": T_in.round(2),
        "T_reaktor": T_meas.round(2),
        "T_alapjel": T_sp,
        "F_hutoviz": np.maximum(Fc, 0).round(3),
        "T_hutoviz": T_cw.round(2),
        "P_reaktor": P.round(3),
        "P_kevero": P_mix.round(2),
        "E_fogyasztas": E.round(1),
    })
    # laborminták 4 óránként: termékkoncentráció és szennyezőtartalom
    lab_mask = (t.hour % 4 == 2) & (t.minute == 0) & ~stop
    lab = pd.DataFrame({"ido": t[lab_mask], "termek": grade[lab_mask],
                        "c_termek": (c_out[lab_mask] + rng.normal(0, 0.015, lab_mask.sum())).round(4),
                        "szennyezes": (impurity[lab_mask] + rng.normal(0, 0.03, lab_mask.sum())).round(3)})
    lab["megfelelo"] = in_spec[lab_mask]
    df["c_termek_labor"] = np.nan
    df.loc[lab_mask, "c_termek_labor"] = lab.c_termek.values

    # ---------------- mérési hibák: kiesések és tüskék ----------------
    for col in ["T_reaktor", "F_hutoviz", "P_reaktor", "T_hutoviz"]:
        miss = rng.random(n) < 0.003
        df.loc[miss, col] = np.nan
        spike = rng.random(n) < 0.0007
        df.loc[spike, col] = df.loc[spike, col] * rng.choice([0.0, 1.6], spike.sum())
    df.loc[stop, ["T_reaktor", "P_reaktor"]] = np.nan

    # ---------------- órás összesítés ----------------
    num = df.drop(columns=["termek"]).set_index("ido")
    hourly = num.resample("1h").mean()
    hourly["termek"] = df.set_index("ido")["termek"].resample("1h").agg(lambda s: s.mode().iat[0])
    hourly["muszak"] = pd.cut(hourly.index.hour, [-1, 5, 13, 21, 23],
                              labels=["éjszakai", "délelőtti", "délutáni", "éjszakai"], ordered=False)
    hourly = hourly.reset_index()

    alarms = _alarm_log(df, fault, lab)

    truth = {
        "fault": pd.Series(fault, index=t, name="hiba"),
        "faults": pd.DataFrame(faults).sort_values("kezdet").reset_index(drop=True),
        "cleanings": pd.Series(t[clean_idx], name="tisztitas"),
        "fouling": pd.Series(fouling, index=t, name="lerakodas"),
        "T_valodi": pd.Series(T_true, index=t, name="T_valodi"),
        "c_termek": pd.Series(c_out, index=t, name="c_termek"),
        "szennyezes": pd.Series(impurity, index=t, name="szennyezes"),
        "megfelelo": pd.Series(in_spec, index=t, name="megfelelo"),
    }
    return PlantData(measurements=df, hourly=hourly, alarms=alarms, lab=lab, truth=truth)


def _alarm_log(df: pd.DataFrame, fault: np.ndarray, lab: pd.DataFrame) -> pd.DataFrame:
    """Riasztásnapló: egy riasztás akkor keletkezik, amikor a feltétel hamisról igazra vált."""
    x = df.ffill()
    osc = x.F_hutoviz.rolling(6, min_periods=3).std() > 0.6
    cond = {
        "T_MAGAS": x.T_reaktor > x.T_alapjel + 1.5,
        "HUTES_TELITETT": x.F_hutoviz > 0.95 * FC_MAX,
        "HUTOVIZ_MELEG": x.T_hutoviz > 25.0,
        "NYOMAS_MAGAS": x.P_reaktor > 2.85,
        "BETAP_KONC_ALACSONY": x.c_betap < 0.9 * x.c_betap.rolling(144, min_periods=10).median(),
        "HUTOVIZ_OSZCILLACIO": osc,
        "BETAP_LEALLT": x.F_betap < 1.0,
    }
    rows = []
    for name, c in cond.items():
        c = c.fillna(False).to_numpy()
        onset = np.flatnonzero(c[1:] & ~c[:-1]) + 1
        # 30 perces "holtsáv": egy riasztás ne ismétlődjön folyamatosan
        last = -10 ** 9
        for k in onset:
            if k - last >= 3:
                rows.append((df.ido.iat[k], name))
                last = k
    for _, r in lab[~lab.megfelelo].iterrows():
        rows.append((r.ido + pd.Timedelta(minutes=50), "MINOSEG_ELTERES"))
    out = pd.DataFrame(rows, columns=["ido", "riasztas"]).sort_values("ido").reset_index(drop=True)
    return out


# ---------------------------------------------------------------------------
# Műszaknapló: a kezelők rövid, szabad szöveges bejegyzései (13. fejezet).
# Saját véletlenszám-generátorral készül, így a mérési adatokat nem változtatja meg.
# A bejegyzések stílusa a valódi naplókat követi: rövidítések, elírások, ékezethiányok.
# ---------------------------------------------------------------------------
_NAPLO = {
    "hutoviz_kieses": [
        "hűtővíz hőfok magas, hűtés max-on", "HV hőmérséklet emelkedik, szólni a közműnek",
        "hutoviz meleg, reaktor T felfele megy", "hűtővíz előremenő meleg, hűtőtorony?",
        "hűtés telítésben, T magas riasztás", "HV temp 30 fok felett, terhelést csökkentettem",
        "hűtővíz ellátás gond, közmű értesítve", "reaktor melegszik, hűtővíz nem hűt rendesen",
    ],
    "szelep_akadas": [
        "hűtővíz szelep akad, áram ingadozik", "szelep beragad, kézi üzembe tettem",
        "HV szabályzószelep rángat, karbantartás értesítve", "hűtővízáram oszcillál, szelep?",
        "szelep nem követi az alapjelet, ugrál", "szabalyzoszelep akadozik, pozicio ingadozik",
        "hűtővízáram leng, szelepet megnézetni", "szelep pozicioner hibas lehet, leng a T",
    ],
    "betap_zavar": [
        "betáp konc. alacsony, labor értesítve", "betáplálás híg, alapanyag tétel ellenőrzés",
        "betap koncentracio esett, uj tartaly?", "alapanyag hígabb a szokásosnál",
        "betáp minta gyenge, raktár értesítve", "konc. alacsony a betápban, termék gyenge lesz",
        "beta koncentracio alacsony riasztas, tetelszamot felirtam", "alapanyag minőség gyanús, labor vizsgálja",
    ],
    "szenzor_drift": [
        "T mérés gyanús, nyomással nem stimmel", "hőmérő elmászott? kézi méréssel eltér",
        "reaktor T jel furcsa, nyomás alacsonyabb mint szokott", "hőelem kalibrálást kérni",
        "T távadó eltérés a kézi mérőtől", "homero gyanus, MSZ ertesitve",
        "hőmérséklet-jel lassan kúszik, ellenőrizni", "nyomás és T nem passzol, műszerész kell",
    ],
    "rutin": [
        "műszakátadás rendben", "mintavétel megtörtént", "minden paraméter rendben",
        "termékváltás rendben lezajlott", "nincs rendkívüli esemény", "szűrőcsere megtörtént",
        "keverő rendben, zaj nincs", "rendben, labor minta elküldve", "terv szerinti termelés",
        "napi bejárás megvolt, rendben", "muszakatadas ok", "kenés elvégezve a keverőn",
    ],
    "tisztitas": [
        "tisztítás miatt leállás", "hűtőköpeny tisztítás, leállítva", "CIP tisztítás folyamatban",
        "tisztítás után újraindítás", "leallas tisztitas miatt, ujrainditas holnap",
    ],
}


def generate_shift_log(plant: PlantData, seed: int = 2026) -> pd.DataFrame:
    """Műszaknapló-bejegyzések a hibaeseményekhez, tisztításokhoz és rutinműszakokhoz.

    Visszaad: ``ido``, ``muszak``, ``szoveg`` és – csak az értékeléshez – ``esemeny``
    (a bejegyzés hátterében álló esemény típusa).
    """
    rng = np.random.default_rng(seed + 13)
    rows = []

    def add(t, kind):
        txt = rng.choice(_NAPLO[kind])
        if rng.random() < 0.25:                      # második, rövid kiegészítés
            txt += ", " + rng.choice(["megfigyelés alatt", "jelezve a műszakvezetőnek", "folyt. köv.",
                                      "következő műszak figyelje", "beírtam a hibajegybe"])
        if rng.random() < 0.15:                      # ékezethiány
            txt = txt.translate(str.maketrans("áéíóöőúüűÁÉÍÓÖŐÚÜŰ", "aeiooouuuAEIOOOUUU"))
        rows.append({"ido": t, "szoveg": txt, "esemeny": kind})

    for _, f in plant.truth["faults"].iterrows():
        n = 1 + int((f.veg - f.kezdet) / pd.Timedelta(hours=12))
        for k in range(min(n, 6)):
            add(f.kezdet + pd.Timedelta(minutes=int(rng.integers(20, 90))) + k * pd.Timedelta(hours=12), f.hiba)
    for d in plant.truth["cleanings"]:
        add(pd.Timestamp(d) + pd.Timedelta(hours=int(rng.integers(1, 6))), "tisztitas")
    days = pd.date_range(plant.measurements.ido.min().normalize(), plant.measurements.ido.max().normalize(), freq="D")
    for d in days:
        for start in (6, 14, 22):                    # háromműszakos rend
            if rng.random() < 0.35:
                add(d + pd.Timedelta(hours=start + 7, minutes=int(rng.integers(0, 50))), "rutin")
    out = pd.DataFrame(rows).sort_values("ido").reset_index(drop=True)
    h = out.ido.dt.hour
    out.insert(1, "muszak", np.select([(h >= 6) & (h < 14), (h >= 14) & (h < 22)], ["délelőtt", "délután"], "éjszaka"))
    return out
