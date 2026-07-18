#!/usr/bin/env python3
"""
Moissonneur MusicBrainz — artistes du Québec.
Carnet de données — souveraineté culturelle numérique.

Récolte complète des artistes rattachés aux zones québécoises dans MusicBrainz,
avec leurs liens externes (Spotify, Bandcamp, etc.) et leurs genres.

Les MBID des zones ont été validés par la sonde des 2026-07-18 :
  province 9 731 artistes · Montréal 4 743 · Québec ville 569 · 6 villes ~491.

Sortie : Données Québec/musicbrainz_artistes_qc_AAAA-MM-JJ.json

Usage :  python3 moissonneur_musicbrainz.py
Durée :  ~5-8 min (rate limit 1 req/s, ~160 pages de 100 artistes)
Reprise : si interrompu, relancer — le script reprend où il en était
          grâce au fichier .moisson_etat.json.

Licence des données : MusicBrainz publie ses données de base sous CC0.
"""

import json
import time
import datetime
import urllib.request
import urllib.parse
from pathlib import Path

BASE = "https://musicbrainz.org/ws/2"
UA = "CarnetDonneesCultureQC/1.0 (joaoroquer@gmail.com)"
DOSSIER_SORTIE = Path(__file__).parent / "Données Québec"
FICHIER_ETAT = Path(__file__).parent / ".moisson_etat.json"

# Zones validées par la sonde (MBID -> libellé)
ZONES = {
    "a510b9b1-404d-4e23-8db8-0f6585909ed8": "Québec (province)",
    "c3cc624e-b963-49cf-ad0b-e318cb341963": "Montréal",
    "e1804252-7413-4a4d-a34d-d21a8e8e752b": "Québec (ville)",
    "3e415fe3-5c32-4fdb-af8b-558452bfd26d": "Laval",
    "c621114d-73cc-4832-8afe-f13dc261e5af": "Gatineau",
    "c0e97660-cb34-4ca8-b7c5-c5dc95d608e3": "Longueuil",
    "1fcce45b-d0a6-46c8-ba07-156e75e33870": "Sherbrooke",
    "fd4d966b-6c58-4e52-82f8-bb1142979cfc": "Trois-Rivières",
    "57dc83fc-eeea-4133-855c-61f20ad6576e": "Saguenay",
}

PLATEFORMES = {
    "spotify.com": "spotify",
    "music.apple.com": "apple_music",
    "deezer.com": "deezer",
    "bandcamp.com": "bandcamp",
    "youtube.com": "youtube",
    "soundcloud.com": "soundcloud",
}


def req(path, params, retries=5):
    params["fmt"] = "json"
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    for tentative in range(retries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (503, 429) and tentative < retries - 1:
                attente = 10 * (tentative + 1)
                print(f"    ({e.code} — pause {attente} s...)")
                time.sleep(attente)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if tentative < retries - 1:
                time.sleep(10)
                continue
            raise


def normaliser_artiste(a, zone_libelle):
    """Extrait les champs utiles d'un artiste MusicBrainz."""
    liens = {}
    for rel in a.get("relations", []):
        u = rel.get("url", {}).get("resource", "")
        for domaine, cle in PLATEFORMES.items():
            if domaine in u and cle not in liens:
                liens[cle] = u
    genres = sorted(
        (g.get("name", "") for g in a.get("genres", []) if g.get("count", 0) > 0),
        key=str.lower,
    )
    vie = a.get("life-span", {})
    return {
        "mbid": a["id"],
        "nom": a.get("name", ""),
        "type": a.get("type"),          # Person / Group / ...
        "zone": zone_libelle,
        "debut": vie.get("begin"),
        "fin": vie.get("end"),
        "actif": not vie.get("ended", False),
        "genres": genres,
        "liens": liens,
        "spotify_id": (liens.get("spotify", "").rsplit("/", 1)[-1]
                       if "spotify" in liens else None),
    }


def charger_etat():
    if FICHIER_ETAT.exists():
        return json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
    return {"zones_terminees": [], "artistes": {}}


def sauver_etat(etat):
    FICHIER_ETAT.write_text(json.dumps(etat, ensure_ascii=False),
                            encoding="utf-8")


def main():
    print("=" * 70)
    print("MOISSONNEUR MUSICBRAINZ — artistes du Québec")
    print("=" * 70)

    etat = charger_etat()
    artistes = etat["artistes"]          # mbid -> dict (dédoublonnage naturel)
    if etat["zones_terminees"]:
        print(f"Reprise : {len(etat['zones_terminees'])} zone(s) déjà faite(s), "
              f"{len(artistes)} artistes en mémoire.")

    for mbid_zone, libelle in ZONES.items():
        if mbid_zone in etat["zones_terminees"]:
            continue
        print(f"\nZone : {libelle}")
        offset = 0
        total = None
        while True:
            time.sleep(1.1)
            data = req("artist", {
                "area": mbid_zone,
                "limit": 100,
                "offset": offset,
                "inc": "url-rels+genres",
            })
            if total is None:
                total = data.get("artist-count", 0)
                print(f"  {total} artistes à récolter")
            lot = data.get("artists", [])
            if not lot:
                break
            for a in lot:
                artistes[a["id"]] = normaliser_artiste(a, libelle)
            offset += len(lot)
            print(f"  {offset}/{total}", end="\r")
            if offset >= total:
                break
        print(f"  {offset}/{total} — terminé")
        etat["zones_terminees"].append(mbid_zone)
        etat["artistes"] = artistes
        sauver_etat(etat)

    # --- Statistiques et sortie finale ---
    liste = list(artistes.values())
    n = len(liste)
    n_spotify = sum(1 for a in liste if a["spotify_id"])
    n_streaming = sum(1 for a in liste if a["liens"])
    n_actifs = sum(1 for a in liste if a["actif"])

    aujourdhui = datetime.date.today().isoformat()
    sortie = {
        "source": "MusicBrainz (MetaBrainz Foundation) — données de base sous licence CC0",
        "methode": ("Browse /ws/2/artist?area=<MBID> sur 9 zones québécoises "
                    "validées par code ISO CA-QC et désambiguïsation par comptage. "
                    "Un artiste MusicBrainz n'a qu'une zone : pas de doublons inter-zones."),
        "date_recolte": aujourdhui,
        "nb_artistes": n,
        "nb_avec_spotify": n_spotify,
        "nb_avec_streaming": n_streaming,
        "nb_actifs": n_actifs,
        "zones": {lib: sum(1 for a in liste if a["zone"] == lib)
                  for lib in ZONES.values()},
        "artistes": liste,
    }

    DOSSIER_SORTIE.mkdir(exist_ok=True)
    fichier = DOSSIER_SORTIE / f"musicbrainz_artistes_qc_{aujourdhui}.json"
    fichier.write_text(json.dumps(sortie, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    print()
    print("=" * 70)
    print(f"Récolte terminée : {n} artistes uniques")
    print(f"  Avec ID Spotify   : {n_spotify} ({n_spotify/n*100:.1f} %)")
    print(f"  Avec lien streaming : {n_streaming} ({n_streaming/n*100:.1f} %)")
    print(f"  Actifs (non dissous) : {n_actifs} ({n_actifs/n*100:.1f} %)")
    print(f"Fichier : {fichier}")
    print("=" * 70)
    FICHIER_ETAT.unlink(missing_ok=True)   # nettoyage de l'état de reprise


if __name__ == "__main__":
    main()
