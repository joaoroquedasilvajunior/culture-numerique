#!/usr/bin/env python3
"""
Phase 2 — Enrichissement Spotify des artistes québécois (v2 diagnostique).
Carnet de données — souveraineté culturelle numérique.

v2 : les nouvelles apps Spotify en mode développement reçoivent des 403 sur
certains endpoints (restrictions post-nov. 2024). Ce script :
  1. affiche le corps des erreurs 403 (la vraie raison s'y trouve),
  2. sonde l'endpoint unitaire /v1/artists/{id} PUIS le batch /v1/artists?ids=,
  3. choisit automatiquement le mode qui fonctionne,
  4. sauvegarde sa progression (.spotify_etat.json) et reprend si interrompu.

PRÉREQUIS :
  export SPOTIFY_CLIENT_ID="ton_client_id"
  export SPOTIFY_CLIENT_SECRET="ton_client_secret"

Usage :  python3 enrichir_spotify.py
Durée :  ~3 min en mode batch · ~15-20 min en mode unitaire (1940 appels)
"""

import base64
import datetime
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

DOSSIER = Path(__file__).parent / "Données Québec"
FICHIER_ETAT = Path(__file__).parent / ".spotify_etat.json"


def trouver_recolte():
    fichiers = sorted(DOSSIER.glob("musicbrainz_artistes_qc_*.json"))
    if not fichiers:
        sys.exit("Aucun musicbrainz_artistes_qc_*.json — lancer le moissonneur d'abord.")
    return fichiers[-1]


def obtenir_token(client_id, client_secret):
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)["access_token"]


def get_json(url, token, retries=5):
    """GET avec Bearer token. Retourne (donnees, None) ou (None, (code, corps))."""
    for tentative in range(retries):
        r = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                return json.load(resp), None
        except urllib.error.HTTPError as e:
            corps = ""
            try:
                corps = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            if e.code == 429 and tentative < retries - 1:
                attente = int(e.headers.get("Retry-After", 5)) + 1
                print(f"    (429 — pause {attente} s)")
                time.sleep(attente)
                continue
            return None, (e.code, corps)
    return None, (0, "épuisement des tentatives")


def normaliser(sp, mb):
    return {
        "mbid": mb["mbid"],
        "nom_mb": mb["nom"],
        "zone": mb["zone"],
        "spotify_id": sp["id"],
        "nom_spotify": sp.get("name"),
        "popularite": sp.get("popularity"),
        "followers": sp.get("followers", {}).get("total"),
        "genres_spotify": sp.get("genres", []),
        "url": sp.get("external_urls", {}).get("spotify"),
    }


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET absents de l'environnement.")

    fichier_recolte = trouver_recolte()
    print(f"Récolte source : {fichier_recolte.name}")
    donnees = json.loads(fichier_recolte.read_text(encoding="utf-8"))

    cibles = []
    for a in donnees["artistes"]:
        sid = a.get("spotify_id")
        if not sid:
            continue
        sid = sid.split("?")[0]
        if len(sid) == 22:
            a = dict(a)
            a["spotify_id"] = sid
            cibles.append(a)
    print(f"Artistes avec ID Spotify valide : {len(cibles)}")

    token = obtenir_token(client_id, client_secret)
    print("Token Spotify obtenu.")

    # --- DIAGNOSTIC : unitaire puis batch ---
    test_id = cibles[0]["spotify_id"]
    print("\n--- Diagnostic des endpoints ---")
    _, err_unit = get_json(f"https://api.spotify.com/v1/artists/{test_id}", token)
    print(f"  Unitaire /v1/artists/{{id}}       : {'OK' if err_unit is None else f'ERREUR {err_unit[0]} — {err_unit[1]}'}")
    ids2 = ",".join(c["spotify_id"] for c in cibles[:2])
    _, err_batch = get_json(f"https://api.spotify.com/v1/artists?ids={ids2}", token)
    print(f"  Batch    /v1/artists?ids=...     : {'OK' if err_batch is None else f'ERREUR {err_batch[0]} — {err_batch[1]}'}")

    if err_unit is not None and err_batch is not None:
        sys.exit("\nLes deux endpoints échouent. Le corps d'erreur ci-dessus indique la "
                 "raison exacte. Causes probables : app en mode développement avec "
                 "restrictions renforcées → demander une 'quota extension' dans le "
                 "dashboard Spotify, ou vérifier que l'app a bien coché « Web API ».")

    mode = "batch" if err_batch is None else "unitaire"
    print(f"\nMode retenu : {mode}")

    # --- État de reprise ---
    enrichis = {}
    if FICHIER_ETAT.exists():
        enrichis = json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
        print(f"Reprise : {len(enrichis)} artistes déjà enrichis.")
    restants = [c for c in cibles if c["spotify_id"] not in enrichis]

    debut = time.time()
    if mode == "batch":
        lots = [restants[i:i + 50] for i in range(0, len(restants), 50)]
        for i, lot in enumerate(lots, 1):
            ids = ",".join(c["spotify_id"] for c in lot)
            data, err = get_json(f"https://api.spotify.com/v1/artists?ids={ids}", token)
            if err:
                print(f"\n  Lot {i} : erreur {err[0]} — {err[1]}")
                break
            for mb, sp in zip(lot, data.get("artists", [])):
                if sp:
                    enrichis[sp["id"]] = normaliser(sp, mb)
            FICHIER_ETAT.write_text(json.dumps(enrichis, ensure_ascii=False), encoding="utf-8")
            print(f"  Lot {i}/{len(lots)} — {len(enrichis)} enrichis", end="\r")
            time.sleep(0.5)
    else:
        for i, mb in enumerate(restants, 1):
            data, err = get_json(f"https://api.spotify.com/v1/artists/{mb['spotify_id']}", token)
            if err:
                if err[0] in (400, 404):   # ID retiré / invalide : sauter
                    continue
                print(f"\n  Artiste {i} : erreur {err[0]} — {err[1]}")
                break
            enrichis[data["id"]] = normaliser(data, mb)
            if i % 25 == 0:
                FICHIER_ETAT.write_text(json.dumps(enrichis, ensure_ascii=False), encoding="utf-8")
                ecoule = time.time() - debut
                reste = ecoule / i * (len(restants) - i)
                print(f"  {i}/{len(restants)} — ETA {reste/60:.0f} min", end="\r")
            time.sleep(0.35)   # ~3 req/s, prudent

    print()
    liste = sorted(enrichis.values(), key=lambda a: -(a["popularite"] or 0))
    aujourdhui = datetime.date.today().isoformat()
    sortie = {
        "source": "Spotify Web API (metadata artistes) — attribution Spotify requise",
        "source_identification": f"MusicBrainz ({fichier_recolte.name})",
        "date_extraction": aujourdhui,
        "validite_cache": "30 jours (Spotify Developer Terms)",
        "mode_extraction": mode,
        "nb_artistes": len(liste),
        "artistes": liste,
    }
    fichier = DOSSIER / f"spotify_artistes_qc_{aujourdhui}.json"
    fichier.write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")

    print("=" * 70)
    print(f"Enrichissement : {len(liste)} artistes ({mode})")
    print("\nTop 10 par popularité Spotify :")
    for a in liste[:10]:
        f_str = f"{a['followers']:,}".replace(",", " ") if a["followers"] is not None else "?"
        print(f"  {(a['nom_spotify'] or '?'):<32} pop={a['popularite']!s:>3} followers={f_str:>11}")
    print(f"\nFichier : {fichier}")
    print("=" * 70)
    if len(liste) >= len(cibles) * 0.95:
        FICHIER_ETAT.unlink(missing_ok=True)
    else:
        print("(État de reprise conservé — relancer pour compléter.)")


if __name__ == "__main__":
    main()
