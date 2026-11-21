"""adatbanyaszat – segédcsomag az „Adatbányászat – a hatékonyság eszköze” című tankönyvhöz.

A csomag két futó esettanulmány adatait állítja elő determinisztikusan (internet nélkül
is), kézi mintapéldákhoz mini-adatsorokat ad, és beállítja a könyv ábrastílusát.

Példa::

    import adatbanyaszat as ab
    ab.set_style()
    shop = ab.load_shop()          # PannonShop – üzleti futó eset
    plant = ab.load_plant()        # Pannon üzem – mérnöki futó eset
    shop.transactions.head()
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .mini import (idosor_mini, kosar_mini, minoseg_tabla, pontok_mini,
                   regresszio_mini, szoveg_mini)
from .plant import PlantData, generate_plant, generate_shift_log
from .shop import ShopData, generate_shop
from . import prep

__version__ = "2.0.0"
__all__ = ["load_shop", "load_plant", "generate_shop", "generate_plant", "set_style",
           "load_penguins", "minoseg_tabla", "kosar_mini", "pontok_mini",
           "regresszio_mini", "idosor_mini", "szoveg_mini", "ShopData", "PlantData", "PALETTE",
           "prep", "shop_clean", "customer_table", "plant_clean", "churn_table", "quality_table"]

#: A könyv színtévesztés-biztos, validált kategorikus palettája.
PALETTE = ["#2E6DB4", "#C8711E", "#7A4EAB", "#1F9077", "#B23A48", "#6B7785"]
PE_BLUE = "#285780"


@lru_cache(maxsize=4)
def load_shop(seed: int = 2026) -> ShopData:
    """A PannonShop adatai (gyorsítótárazva: egy munkameneten belül csak egyszer generál)."""
    return generate_shop(seed=seed)


@lru_cache(maxsize=4)
def load_plant(seed: int = 2026) -> PlantData:
    """A Pannon üzem adatai (gyorsítótárazva)."""
    return generate_plant(seed=seed)


@lru_cache(maxsize=2)
def load_shift_log(seed: int = 2026):
    """A Pannon üzem műszaknaplója (szabad szöveges kezelői bejegyzések, 13. fejezet)."""
    return generate_shift_log(load_plant(seed), seed=seed)


def set_style() -> None:
    """A könyv matplotlib-stílusának beállítása (a csomaggal szállított IBM Plex Sans betűtípussal)."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f in (Path(__file__).parent / "fonts").glob("*.otf"):
        try:
            font_manager.fontManager.addfont(str(f))
        except Exception:  # pragma: no cover
            pass
    style = Path(__file__).with_name("pe.mplstyle")
    plt.style.use(str(style))


def load_penguins():
    """A Palmer-pingvinek adatsor (Horst és mtsai, 2020; CC0) – az Iris korszerű alternatívája.

    Először a seaborn beépített betöltőjét próbálja, majd a csomag GitHub-forrását.
    """
    import pandas as pd
    try:
        import seaborn as sns
        return sns.load_dataset("penguins")
    except Exception:  # pragma: no cover - hálózatfüggő
        url = ("https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/"
               "inst/extdata/penguins.csv")
        return pd.read_csv(url)


@lru_cache(maxsize=2)
def shop_clean(seed: int = 2026):
    """A 3. fejezetben megtisztított PannonShop-számlatételek (sztornók nélkül)."""
    s = load_shop(seed)
    return prep.clean_transactions(s.transactions, s.products)


@lru_cache(maxsize=4)
def customer_table(ref_date: str = "2026-01-01", seed: int = 2026):
    """Vevőszintű jellemzőtábla (RFM és vásárlási szerkezet) a megadott referencia-dátumig."""
    s = load_shop(seed)
    return prep.customer_features(shop_clean(seed), ref_date, s.products)


@lru_cache(maxsize=2)
def plant_clean(seed: int = 2026):
    """A 3. fejezetben megtisztított 10 perces Pannon üzem mérések."""
    return prep.clean_plant(load_plant(seed).measurements)


@lru_cache(maxsize=4)
def churn_table(cutoff: str = "2025-07-01", horizon_days: int = 183, seed: int = 2026):
    """Lemorzsolódás-előrejelzési tábla (jellemzők a cutoff előttről, címke a cutoff utánról)."""
    s = load_shop(seed)
    return prep.churn_dataset(shop_clean(seed), s.products, cutoff, horizon_days)


@lru_cache(maxsize=2)
def quality_table(seed: int = 2026):
    """A Pannon üzem laborminták és a mintavétel előtti órában mért folyamatváltozók táblája."""
    return prep.quality_dataset(plant_clean(seed), load_plant(seed).lab)
