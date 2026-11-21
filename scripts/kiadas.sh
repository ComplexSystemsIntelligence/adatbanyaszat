#!/usr/bin/env bash
# Kiadás előkészítése: a GitHub-munkafolyamat által lefordított és a gh-pages ágon közzétett PDF és EPUB
# bemásolása a kiadas/ mappába, hogy a GitHub-kiadás forráscsomagjával a Zenodo az olvasható könyvet is
# archiválja. Előtte frissítendő a változatszám és a dátum (CITATION.cff, .zenodo.json és a
# _extensions/pannon/pannon-header.tex \peverzio sora), és a main ágra feltöltött változat fordításának
# sikeresen le kell futnia.
set -euo pipefail
cd "$(dirname "$0")/.."
git fetch -q --depth=1 origin gh-pages
mkdir -p kiadas
git show FETCH_HEAD:adatbanyaszat.pdf > kiadas/adatbanyaszat.pdf
git show FETCH_HEAD:adatbanyaszat.epub > kiadas/adatbanyaszat.epub
ls -la kiadas
