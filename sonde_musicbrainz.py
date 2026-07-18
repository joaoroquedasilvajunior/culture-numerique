#!/usr/bin/env python3
"""
Sonde de faisabilité MusicBrainz v3 — échantillon Spotify uniquement.

Les comptages sont acquis (v2) : province 9 731, Montréal 4 743, Québec ville 569.
Ne reste qu'à mesurer le taux de liens Spotify sur un échantillon d'artistes
montréalais. 50 artistes en 1 seule requête (limit=50, inc=url-rels).

Usage :  python3 sonde_musicbrainz.py
Durée :  ~10 s
"""

import json
import time
import urllib.request
import urllib.parse

BASE = "https://musicbrainz.org/ws/2"
UA = "CarnetDonneesCultureQC/0.3 (joaoroquer@gmail.com)"
MBID_MONTREAL = "c3cc624e-b963-49cf-ad0b-e318cb341963"   # validé en v2


def req(path, params, retries=4):
    params["fmt"] = "json"
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    for tentative in range(retries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 503 and tentative < retries - 1:
                attente = 5 * (tentative + 1)
                print(f"  (503 — nouvelle tentative dans {attente} s...)")
                time.sleep(attente)
                continue
            raise


def main():
    print("=" * 70)
    print("SONDE MUSICBRAINZ v3 — taux de liens Spotify (échantillon Montréal)")
    print("=" * 70)

    data = req("artist", {"area": MBID_MONTREAL, "limit": 50, "inc": "url-rels"})
    artistes = data.get("artists", [])
    if not artistes:
        print("  Aucun artiste retourné — réessayer dans quelques minutes.")
        return

    avec_spotify = 0
    avec_streaming = 0   # spotify OU apple music OU deezer OU bandcamp
    exemples = []
    for a in artistes:
        urls = [rel.get("url", {}).get("resource", "")
                for rel in a.get("relations", [])]
        spotify = next((u for u in urls if "spotify.com" in u), None)
        streaming = next((u for u in urls if any(s in u for s in
                          ("spotify.com", "music.apple.com", "deezer.com",
                           "bandcamp.com"))), None)
        if spotify:
            avec_spotify += 1
        if streaming:
            avec_streaming += 1
        exemples.append((a.get("name", "?"), spotify or "—"))

    n = len(artistes)
    print(f"  Échantillon : {n} artistes (zone Montréal)")
    print(f"  Avec lien Spotify           : {avec_spotify:>3} ({avec_spotify/n*100:.0f} %)")
    print(f"  Avec lien streaming (élargi) : {avec_streaming:>3} ({avec_streaming/n*100:.0f} %)")
    print()
    print("  Aperçu (12 premiers) :")
    for nom_a, sp in exemples[:12]:
        print(f"    {nom_a:<34} | {sp[:58]}")

    print()
    print("=" * 70)
    print("Rappel des comptages v2 : province 9 731 · Montréal 4 743 · Québec 569")
    print("+ petites villes ~491 → univers total ≈ 15 500 artistes QC.")
    print("=" * 70)


if __name__ == "__main__":
    main()
