#!/usr/bin/env python3
"""
Récolte du top 100 Apple Music Canada (chansons les plus écoutées).
Carnet de données — souveraineté culturelle numérique.

Source : flux marketing publics d'Apple (aucune clé requise).
  https://rss.marketingtools.apple.com/api/v2/ca/music/most-played/100/songs.json

Croise les artistes du top 100 avec la récolte MusicBrainz des artistes
québécois (rapprochement par nom normalisé : minuscules, sans accents,
sans ponctuation) et marque les entrées québécoises.

Sortie : Données Québec/apple_top100_ca_AAAA-MM-JJ.json

Usage :  python3 recolter_apple_top100.py
Durée :  ~5 s

Limites documentées :
- Palmarès par storefront pays (Canada) : pas de coupe Québec.
- Rapprochement par nom : les collaborations (« Artiste X & Artiste Y »)
  sont testées sur chaque segment ; un artiste QC absent de MusicBrainz
  ou orthographié différemment échappera au marquage (faux négatifs
  possibles, pas de faux positifs attendus).
"""

import datetime
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

DOSSIER = Path(__file__).parent / "Données Québec"
URL = "https://rss.marketingtools.apple.com/api/v2/ca/music/most-played/100/songs.json"
UA = "CarnetDonneesCultureQC/1.0 (joaoroquer@gmail.com)"


def normaliser(nom):
    """minuscules, sans accents, ligatures dépliées, sans ponctuation."""
    s = nom.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def segments_artiste(artist_name):
    """Découpe « A & B », « A, B », « A feat. B » en segments individuels."""
    s = re.sub(r"(?i)\s+(feat\.?|featuring|avec|with|x)\s+", "&", artist_name)
    parts = re.split(r"[&,;/]| et ", s)
    return [p.strip() for p in parts if p.strip()]


def main():
    # Index des noms QC depuis la récolte MusicBrainz
    fichiers_mb = sorted(DOSSIER.glob("musicbrainz_artistes_qc_*.json"))
    if not fichiers_mb:
        sys.exit("Récolte MusicBrainz absente — lancer moissonneur_musicbrainz.py d'abord.")
    mb = json.loads(fichiers_mb[-1].read_text(encoding="utf-8"))
    index_qc = {}
    for a in mb["artistes"]:
        index_qc[normaliser(a["nom"])] = a["mbid"]
    print(f"Index QC : {len(index_qc)} noms (récolte {mb['date_recolte']})")

    # Flux Apple
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        feed = json.load(resp)["feed"]
    entrees_brutes = feed.get("results", [])
    date_flux = feed.get("updated", "")
    print(f"Flux Apple : {len(entrees_brutes)} entrées (maj {date_flux})")

    entrees = []
    n_qc = 0
    for rang, e in enumerate(entrees_brutes, 1):
        artiste = e.get("artistName", "")
        segments = segments_artiste(artiste)
        mbids = [index_qc.get(normaliser(seg)) for seg in segments]
        mbids_qc = [m for m in mbids if m]
        est_qc = bool(mbids_qc)
        if est_qc:
            n_qc += 1
        entrees.append({
            "rang": rang,
            "titre": e.get("name", ""),
            "artiste": artiste,
            "quebec": est_qc,
            "mbids_qc": mbids_qc,
            "url": e.get("url", ""),
        })

    aujourdhui = datetime.date.today().isoformat()
    sortie = {
        "source": "Apple Music — flux marketing public, chansons les plus écoutées, Canada",
        "url_flux": URL,
        "date_extraction": aujourdhui,
        "date_flux": date_flux,
        "methode_identification": ("Croisement par nom normalisé avec la récolte "
                                   f"MusicBrainz ({fichiers_mb[-1].name}) ; segments "
                                   "de collaborations testés individuellement ; "
                                   "faux négatifs possibles, faux positifs improbables."),
        "n_entrees": len(entrees),
        "n_quebec": n_qc,
        "entrees": entrees,
    }
    fichier = DOSSIER / f"apple_top100_ca_{aujourdhui}.json"
    fichier.write_text(json.dumps(sortie, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    print("=" * 60)
    print(f"Top 100 Apple Canada — artistes QC détectés : {n_qc}")
    for e in entrees:
        if e["quebec"]:
            print(f"  #{e['rang']:>3}  {e['artiste']} — {e['titre']}")
    if n_qc == 0:
        print("  (aucun)")
    print(f"Fichier : {fichier}")
    print("=" * 60)


if __name__ == "__main__":
    main()
