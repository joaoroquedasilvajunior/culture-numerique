#!/usr/bin/env python3
"""
Enrichissement Deezer des artistes québécois — alternative ouverte à Spotify.
Carnet de données — souveraineté culturelle numérique.

L'API publique Deezer ne demande AUCUNE authentification pour les métadonnées
d'artistes, et son rate limit est généreux (50 requêtes / 5 s). L'endpoint
https://api.deezer.com/artist/{id} retourne notamment nb_fan (followers)
et nb_album — les proxys de popularité qui nous manquent côté Spotify.

Périmètre : les artistes de la récolte MusicBrainz ayant un lien Deezer
documenté (précision maximale, pas de recherche par nom).

Usage :  python3 enrichir_deezer.py
Durée :  ~2-4 min selon le nombre de liens Deezer dans la récolte
Sortie : Données Québec/deezer_artistes_qc_AAAA-MM-JJ.json
"""

import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

DOSSIER = Path(__file__).parent / "Données Québec"
FICHIER_ETAT = Path(__file__).parent / ".deezer_etat.json"
PAUSE = 0.15          # ~6-7 req/s, bien sous 50/5 s
UA = "CarnetDonneesCultureQC/1.0 (joaoroquer@gmail.com)"


def trouver_recolte():
    fichiers = sorted(DOSSIER.glob("musicbrainz_artistes_qc_*.json"))
    if not fichiers:
        sys.exit("Aucun musicbrainz_artistes_qc_*.json — lancer le moissonneur d'abord.")
    return fichiers[-1]


def deezer_id(url):
    """Extrait l'ID numérique d'une URL Deezer artiste (gère /fr/, ancres, etc.)."""
    m = re.search(r"deezer\.com/(?:\w{2}/)?artist/(\d+)", url)
    return m.group(1) if m else None


def get_artiste(did, retries=4):
    url = f"https://api.deezer.com/artist/{did}"
    for tentative in range(retries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=30) as resp:
                data = json.load(resp)
        except Exception:
            if tentative < retries - 1:
                time.sleep(2 * (tentative + 1))
                continue
            return None
        # Deezer signale le dépassement de quota par un objet error code 4
        if isinstance(data, dict) and data.get("error", {}).get("code") == 4:
            time.sleep(5)
            continue
        if isinstance(data, dict) and "error" in data:
            return None          # artiste supprimé / ID invalide
        return data
    return None


def main():
    fichier_recolte = trouver_recolte()
    print(f"Récolte source : {fichier_recolte.name}")
    donnees = json.loads(fichier_recolte.read_text(encoding="utf-8"))

    cibles = []
    for a in donnees["artistes"]:
        lien = a.get("liens", {}).get("deezer")
        if not lien:
            continue
        did = deezer_id(lien)
        if did:
            cibles.append((did, a))
    print(f"Artistes avec lien Deezer exploitable : {len(cibles)}")

    enrichis = {}
    if FICHIER_ETAT.exists():
        enrichis = json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
        print(f"Reprise : {len(enrichis)} artistes déjà enrichis.")

    restants = [(did, a) for did, a in cibles if did not in enrichis]
    debut = time.time()
    for i, (did, mb) in enumerate(restants, 1):
        sp = get_artiste(did)
        if sp:
            enrichis[did] = {
                "mbid": mb["mbid"],
                "nom_mb": mb["nom"],
                "zone": mb["zone"],
                "deezer_id": did,
                "nom_deezer": sp.get("name"),
                "nb_fan": sp.get("nb_fan"),
                "nb_album": sp.get("nb_album"),
                "url": sp.get("link"),
            }
        if i % 50 == 0:
            FICHIER_ETAT.write_text(json.dumps(enrichis, ensure_ascii=False),
                                    encoding="utf-8")
            ecoule = time.time() - debut
            reste = ecoule / i * (len(restants) - i)
            print(f"  {i}/{len(restants)} — ETA {reste/60:.1f} min", end="\r")
        time.sleep(PAUSE)

    print()
    liste = sorted(enrichis.values(), key=lambda a: -(a["nb_fan"] or 0))
    aujourdhui = datetime.date.today().isoformat()
    sortie = {
        "source": "API publique Deezer (métadonnées artistes) — attribution Deezer requise",
        "source_identification": f"MusicBrainz ({fichier_recolte.name})",
        "date_extraction": aujourdhui,
        "nb_artistes": len(liste),
        "note_methodo": ("Périmètre : artistes de la récolte MusicBrainz avec lien "
                         "Deezer documenté (aucune recherche par nom). nb_fan est le "
                         "proxy de popularité ; échelle propre à Deezer, marché fort "
                         "en francophonie — pertinent pour le répertoire québécois."),
        "artistes": liste,
    }
    fichier = DOSSIER / f"deezer_artistes_qc_{aujourdhui}.json"
    fichier.write_text(json.dumps(sortie, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    print("=" * 70)
    print(f"Enrichissement Deezer : {len(liste)} artistes")
    print("\nTop 10 par nombre de fans Deezer :")
    for a in liste[:10]:
        fans = f"{a['nb_fan']:,}".replace(",", " ") if a["nb_fan"] is not None else "?"
        print(f"  {(a['nom_deezer'] or a['nom_mb']):<32} fans={fans:>10}  albums={a['nb_album']}")
    print(f"\nFichier : {fichier}")
    print("=" * 70)
    FICHIER_ETAT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
