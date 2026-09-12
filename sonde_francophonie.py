#!/usr/bin/env python3
"""
Sonde de faisabilité — la francophonie musicale dans les métadonnées ouvertes.
Carnet de données — souveraineté culturelle numérique.

Question de recherche (rencontre Tchéhouali, août 2026) : peut-on construire
une lecture comparée de la présence et de la popularité des artistes
francophones, pays par pays, à partir de sources ouvertes ?

Ce que la sonde mesure, pour ~23 territoires de la francophonie :
  1. le nombre d'artistes recensés dans MusicBrainz (CC0) ;
  2. le taux de liens Deezer documentés (sur un échantillon de 100 artistes) ;
  3. le taux de liens Spotify et le taux de liens streaming toutes plateformes.

Ce que la sonde NE mesure PAS, et pourquoi :
  - la popularité (nb_fan) : mesurable ensuite via enrichir_deezer.py, mais
    hors périmètre d'une sonde de faisabilité ;
  - la nationalité déclarée : MusicBrainz rattache par lieu de naissance ou de
    formation, pas par citoyenneté. Le biais pèse plus lourd pour les
    diasporas — à porter explicitement dans toute lecture ;
  - la langue de création : un artiste rattaché au Maroc peut créer en arabe,
    en amazigh ou en français. « Francophonie » désigne ici l'espace
    institutionnel, pas un corpus linguistique.

Les taux de liens sont des PLANCHERS DE COMPLÉTUDE des métadonnées ouvertes,
jamais des taux de présence réelle sur les plateformes. C'est précisément
l'objet : l'inégalité d'infrastructure documentaire entre territoires.

Usage :  python3 sonde_francophonie.py
Durée :  ~3-6 min (rate limit MusicBrainz 1 req/s + retries sur 503)
Reprise : relancer en cas d'interruption, l'état est conservé.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://musicbrainz.org/ws/2"
UA = "CarnetDonneesCultureQC/1.0 (joaoroquer@gmail.com)"
DOSSIER = Path(__file__).parent / "Données Québec"
ETAT = Path(__file__).parent / ".sonde_francophonie_etat.json"
TAILLE_ECHANTILLON = 100

# Territoires de la francophonie, groupés pour la lecture comparée.
# Le Québec est une subregion (MBID validé le 2026-07-18), les autres sont
# des pays résolus par code ISO 3166-1 alpha-2.
TERRITOIRES = [
    # (clé, libellé, groupe, code ISO ou MBID direct)
    ("QC", "Québec",            "Amériques", "MBID:a510b9b1-404d-4e23-8db8-0f6585909ed8"),
    ("HT", "Haïti",             "Amériques", "ISO:HT"),
    ("FR", "France",            "Europe",    "ISO:FR"),
    ("BE", "Belgique",          "Europe",    "ISO:BE"),
    ("CH", "Suisse",            "Europe",    "ISO:CH"),
    ("LU", "Luxembourg",        "Europe",    "ISO:LU"),
    ("SN", "Sénégal",           "Afrique de l'Ouest", "ISO:SN"),
    ("CI", "Côte d'Ivoire",     "Afrique de l'Ouest", "ISO:CI"),
    ("ML", "Mali",              "Afrique de l'Ouest", "ISO:ML"),
    ("BF", "Burkina Faso",      "Afrique de l'Ouest", "ISO:BF"),
    ("GN", "Guinée",            "Afrique de l'Ouest", "ISO:GN"),
    ("BJ", "Bénin",             "Afrique de l'Ouest", "ISO:BJ"),
    ("TG", "Togo",              "Afrique de l'Ouest", "ISO:TG"),
    ("NE", "Niger",             "Afrique de l'Ouest", "ISO:NE"),
    ("CM", "Cameroun",          "Afrique centrale",   "ISO:CM"),
    ("CD", "RD Congo",          "Afrique centrale",   "ISO:CD"),
    ("CG", "Congo-Brazzaville", "Afrique centrale",   "ISO:CG"),
    ("GA", "Gabon",             "Afrique centrale",   "ISO:GA"),
    ("MA", "Maroc",             "Maghreb",            "ISO:MA"),
    ("TN", "Tunisie",           "Maghreb",            "ISO:TN"),
    ("DZ", "Algérie",           "Maghreb",            "ISO:DZ"),
    ("MG", "Madagascar",        "Océan Indien",       "ISO:MG"),
    ("LB", "Liban",             "Moyen-Orient",       "ISO:LB"),
]

PLATEFORMES = {
    "deezer": "deezer.com",
    "spotify": "spotify.com",
    "apple_music": "music.apple.com",
    "bandcamp": "bandcamp.com",
    "youtube": "youtube.com",
    "soundcloud": "soundcloud.com",
}


def req(path, params, retries=5):
    """GET MusicBrainz avec backoff sur 503 (fréquents, documentés)."""
    params["fmt"] = "json"
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    for tentative in range(retries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=45) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (503, 429) and tentative < retries - 1:
                attente = 5 * (tentative + 1)
                print(f"      ({e.code} — pause {attente} s)")
                time.sleep(attente)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if tentative < retries - 1:
                time.sleep(5)
                continue
            raise
    return None


def resoudre_zone(ref):
    """Retourne le MBID de la zone, par MBID direct ou par code ISO."""
    if ref.startswith("MBID:"):
        return ref.split(":", 1)[1]
    iso = ref.split(":", 1)[1]
    time.sleep(1.1)
    data = req("area", {"query": f"iso:{iso}", "limit": 3})
    for a in data.get("areas", []):
        codes = a.get("iso-3166-1-codes") or []
        if iso in codes:
            return a["id"]
    aires = data.get("areas", [])
    return aires[0]["id"] if aires else None


def mesurer(mbid):
    """Compte les artistes et mesure les taux de liens sur un échantillon."""
    time.sleep(1.1)
    total = req("artist", {"area": mbid, "limit": 1}).get("artist-count", 0)
    if total == 0:
        return {"artistes": 0, "echantillon": 0, "liens": {}}

    time.sleep(1.1)
    data = req("artist", {"area": mbid, "limit": TAILLE_ECHANTILLON,
                          "inc": "url-rels"})
    artistes = data.get("artists", [])
    compte = {k: 0 for k in PLATEFORMES}
    au_moins_une = 0
    for a in artistes:
        urls = [rel.get("url", {}).get("resource", "")
                for rel in a.get("relations", [])]
        trouve = False
        for cle, domaine in PLATEFORMES.items():
            if any(domaine in u for u in urls):
                compte[cle] += 1
                trouve = True
        if trouve:
            au_moins_une += 1

    n = len(artistes)
    taux = {k: round(v / n * 100, 1) for k, v in compte.items()} if n else {}
    return {
        "artistes": total,
        "echantillon": n,
        "liens_n": compte,
        "liens_pct": taux,
        "streaming_toutes_plateformes_pct": round(au_moins_une / n * 100, 1) if n else None,
    }


def main():
    print("=" * 78)
    print("SONDE — la francophonie musicale dans les métadonnées ouvertes")
    print("=" * 78)

    resultats = {}
    if ETAT.exists():
        resultats = json.loads(ETAT.read_text(encoding="utf-8"))
        print(f"Reprise : {len(resultats)} territoire(s) déjà mesuré(s).\n")

    for cle, libelle, groupe, ref in TERRITOIRES:
        if cle in resultats:
            continue
        print(f"  {libelle} ({groupe})…")
        try:
            mbid = resoudre_zone(ref)
            if not mbid:
                print("      zone introuvable")
                resultats[cle] = {"libelle": libelle, "groupe": groupe,
                                  "erreur": "zone introuvable"}
                continue
            mes = mesurer(mbid)
            resultats[cle] = {"libelle": libelle, "groupe": groupe,
                              "mbid": mbid, **mes}
            print(f"      {mes['artistes']:>6} artistes | "
                  f"Deezer {mes['liens_pct'].get('deezer', 0):>5} % | "
                  f"Spotify {mes['liens_pct'].get('spotify', 0):>5} % | "
                  f"streaming {mes['streaming_toutes_plateformes_pct']:>5} %")
        except Exception as e:
            print(f"      ERREUR : {e}")
            resultats[cle] = {"libelle": libelle, "groupe": groupe,
                              "erreur": str(e)}
        ETAT.write_text(json.dumps(resultats, ensure_ascii=False), encoding="utf-8")

    # === Tableau de synthèse ===
    print()
    print("=" * 78)
    print(f"{'Territoire':<20} {'Groupe':<20} {'Artistes':>9} {'Deezer':>8} {'Spotify':>8} {'Strm':>7}")
    print("-" * 78)
    ok = [(k, v) for k, v in resultats.items() if "erreur" not in v and v.get("artistes")]
    for _, v in sorted(ok, key=lambda kv: -kv[1]["artistes"]):
        lp = v.get("liens_pct", {})
        print(f"{v['libelle']:<20} {v['groupe']:<20} {v['artistes']:>9,} "
              f"{lp.get('deezer', 0):>7.1f}% {lp.get('spotify', 0):>7.1f}% "
              f"{v.get('streaming_toutes_plateformes_pct', 0):>6.1f}%".replace(",", " "))

    # Agrégats par groupe — l'inégalité d'infrastructure documentaire
    print("-" * 78)
    groupes = {}
    for _, v in ok:
        g = groupes.setdefault(v["groupe"], {"artistes": 0, "dz": [], "strm": []})
        g["artistes"] += v["artistes"]
        g["dz"].append(v.get("liens_pct", {}).get("deezer", 0))
        g["strm"].append(v.get("streaming_toutes_plateformes_pct", 0))
    for nom, g in sorted(groupes.items(), key=lambda kv: -kv[1]["artistes"]):
        moy_dz = sum(g["dz"]) / len(g["dz"])
        moy_st = sum(g["strm"]) / len(g["strm"])
        print(f"{nom:<41} {g['artistes']:>9,} {moy_dz:>7.1f}% {'':>8} {moy_st:>6.1f}%".replace(",", " "))

    erreurs = [v["libelle"] for v in resultats.values() if "erreur" in v]
    if erreurs:
        print(f"\nNon mesurés : {', '.join(erreurs)}")

    aujourdhui = time.strftime("%Y-%m-%d")
    sortie = {
        "source": "MusicBrainz (MetaBrainz Foundation) — données de base CC0",
        "date_sonde": aujourdhui,
        "taille_echantillon": TAILLE_ECHANTILLON,
        "note_methodo": (
            "Les taux de liens sont des planchers de complétude des métadonnées "
            "ouvertes, pas des taux de présence réelle sur les plateformes. "
            "MusicBrainz rattache par lieu de naissance ou de formation, pas par "
            "citoyenneté — biais accru pour les diasporas. Échantillon de "
            f"{TAILLE_ECHANTILLON} artistes par territoire, ordonné par identifiant "
            "MusicBrainz (ordre non corrélé à la popularité)."),
        "territoires": resultats,
    }
    DOSSIER.mkdir(exist_ok=True)
    fichier = DOSSIER / f"sonde_francophonie_{aujourdhui}.json"
    fichier.write_text(json.dumps(sortie, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    print(f"\nFichier : {fichier}")
    print("=" * 78)
    if not erreurs:
        ETAT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
