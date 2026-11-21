# Interaktív gyakorló alkalmazások

A könyv tizennégy, böngészőben futó gyakorló alkalmazása. Mindegyik önálló HTML-oldal,
telepítést és internetkapcsolatot nem igényel: a webkönyvben a fejezetbe ágyazva jelenik
meg, de közvetlenül is megnyitható. A paraméterek csúszkákkal állíthatók, az eredmény
azonnal látszik, így egy-egy módszer viselkedése a képletek mellett kísérletezéssel is
megérthető.

| Fejezet | Alkalmazás | Megnyitás |
|---|---|---|
| 2. Adattárházak | OLAP-kocka: összesítés, lefúrás, szeletelés | [olap-kocka](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/olap-kocka.html) |
| 3. Adatelőkészítés | Adattisztítás: Hampel-szűrő és hiánypótlás | [adattisztitas](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/adattisztitas.html) |
| 4. Feltáró elemzés | Főkomponens-elemzés: a vetítési irány forgatása | [pca-forgatas](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/pca-forgatas.html) |
| 5. Csoportosítás | A k-átlag algoritmus lépésről lépésre | [kmeans](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/kmeans.html) |
| 6. Asszociációs szabályok | Apriori: gyakori elemhalmazok és szabályok | [apriori](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/apriori.html) |
| 7. Modellértékelés | ROC-görbe, PR-görbe és döntési küszöb | [roc-kuszob](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/roc-kuszob.html) |
| 8. Regresszió | Polinomiális regresszió és ridge-regularizáció | [regresszio](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/regresszio.html) |
| 9. Osztályozás | Döntési fa építése: vágások, entrópia, Gini-index | [dontesi-fa](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/dontesi-fa.html) |
| 10. Neurális hálózatok | Neurális hálózat tanítása a böngészőben | [neuralis-halo](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/neuralis-halo.html) |
| 11. Anomáliák | Anomália-észlelők összehasonlítása | [anomalia](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/anomalia.html) |
| 12. Idősorok | Dinamikus idővetemítés (DTW) | [dtw](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/dtw.html) |
| 13. Szövegbányászat | TF-IDF és koszinusz-hasonlóság | [tfidf](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/tfidf.html) |
| 14. Ügyfélanalitika | Ügyfélérték-kalkulátor | [clv](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/clv.html) |
| 15. Folyamatanalitika | Lágy szenzor: bemenetek, modell és laboreredmények | [lagy-szenzor](https://complexsystemsintelligence.github.io/adatbanyaszat/apps/lagy-szenzor.html) |

## Felépítés

Az alkalmazások külső könyvtárat nem használnak: a közös stílust a `common.css`, a
segédfüggvényeket (véletlenszám-generátor, tengelyek, hőtérkép) a `common.js` adja. Új
alkalmazás ezek mintájára készíthető, és a fejezetbe a `{{< app név >}}` rövidkóddal
illeszthető be.
