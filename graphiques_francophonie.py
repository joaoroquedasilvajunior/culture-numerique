#!/usr/bin/env python3
"""
Graphiques de la sonde francophonie — matériel de présentation.
Carnet de données — souveraineté culturelle numérique.

Produit quatre figures à partir de sonde_francophonie_*.json :
  1. La fracture documentaire (nombre d'artistes par territoire)
  2. L'inégalité est en amont (comptes vs taux de liens, côte à côte)
  3. Densité documentaire par million d'habitants
  4. La taxonomie Deezer (asymétrie genre / géographie)

Usage :  python3 graphiques_francophonie.py
Sortie : chroniques/graph_francophonie_*.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RACINE = Path(__file__).parent
SORTIE = RACINE / "chroniques"
SORTIE.mkdir(exist_ok=True)

# Palette alignée sur le tableau de bord du Carnet
BLEU = "#264653"
BLEU_MOY = "#2a7f9e"
BLEU_CLAIR = "#7fb3c8"
ORANGE = "#d6603c"
GRIS = "#8a9aa5"
GRIS_PALE = "#f0f4f8"

COULEUR_GROUPE = {
    "Europe": BLEU,
    "Amériques": BLEU_MOY,
    "Maghreb": BLEU_CLAIR,
    "Moyen-Orient": BLEU_CLAIR,
    "Afrique centrale": ORANGE,
    "Afrique de l'Ouest": ORANGE,
    "Océan Indien": ORANGE,
}

# Populations approximatives (millions), ordres de grandeur usuels 2024-2025.
# Utilisées uniquement pour la densité ; toute publication devrait les
# recouper avec une source démographique citée (Banque mondiale, ONU).
POPULATION_M = {
    "France": 68.0, "Belgique": 11.8, "Suisse": 8.9, "Luxembourg": 0.67,
    "Québec": 8.9, "Haïti": 11.7,
    "Sénégal": 18.4, "Côte d'Ivoire": 31.2, "Mali": 23.8, "Burkina Faso": 23.3,
    "Guinée": 14.2, "Bénin": 13.7, "Togo": 9.1, "Niger": 26.2,
    "Cameroun": 28.6, "RD Congo": 105.8, "Congo-Brazzaville": 6.1, "Gabon": 2.4,
    "Maroc": 37.8, "Tunisie": 12.3, "Algérie": 46.2,
    "Madagascar": 31.0, "Liban": 5.8,
}

NOTE = ("Source : MusicBrainz (MetaBrainz Foundation, données de base CC0), sonde du {date}. "
        "Les taux de liens sont des planchers de complétude des métadonnées ouvertes, "
        "non des taux de présence réelle sur les plateformes.\n"
        "MusicBrainz rattache les artistes par lieu de naissance ou de formation, pas par "
        "citoyenneté : le biais de diaspora gonfle les comptes européens et réduit les comptes "
        "africains.\nCarnet de données — souveraineté culturelle numérique · démarche indépendante.")


def charger():
    fichiers = sorted(RACINE.glob("Données Québec/sonde_francophonie_*.json"))
    if not fichiers:
        raise SystemExit("Aucun fichier sonde_francophonie_*.json — lancer sonde_francophonie.py.")
    d = json.loads(fichiers[-1].read_text(encoding="utf-8"))
    terr = [v for v in d["territoires"].values()
            if "erreur" not in v and v.get("artistes")]
    return d, sorted(terr, key=lambda t: -t["artistes"])


def pied(fig, date):
    fig.text(0.01, 0.012, NOTE.format(date=date), fontsize=6.5, color=GRIS,
             va="bottom", ha="left", linespacing=1.5)


# === Figure 1 — La fracture documentaire ====================================

def figure_1(terr, date):
    fig, ax = plt.subplots(figsize=(11, 8))
    noms = [t["libelle"] for t in terr][::-1]
    vals = [t["artistes"] for t in terr][::-1]
    cols = [COULEUR_GROUPE.get(t["groupe"], GRIS) for t in terr][::-1]

    ax.barh(noms, vals, color=cols, height=0.72)
    ax.set_xscale("log")
    ax.set_xlim(50, 150000)
    ax.set_xlabel("Nombre d'artistes recensés (échelle logarithmique)", fontsize=10)
    fig.text(0.012, 0.982, "La fracture documentaire de la francophonie musicale",
             fontsize=16, fontweight="bold", color=BLEU, va="top", ha="left")
    fig.text(0.012, 0.945, "Artistes recensés dans MusicBrainz, par territoire",
             fontsize=11, color=GRIS, va="top", ha="left")

    for nom, v in zip(noms, vals):
        ax.text(v * 1.12, nom, f"{v:,}".replace(",", " "),
                va="center", fontsize=8.5, color=BLEU)

    ax.grid(axis="x", color=GRIS_PALE, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9.5)

    ax.legend(handles=[Patch(color=BLEU, label="Europe"),
                       Patch(color=BLEU_MOY, label="Amériques"),
                       Patch(color=BLEU_CLAIR, label="Maghreb / Moyen-Orient"),
                       Patch(color=ORANGE, label="Afrique subsaharienne / Océan Indien")],
              loc="lower right", frameon=False, fontsize=9)

    total_af = sum(t["artistes"] for t in terr
                   if t["groupe"] in ("Afrique de l'Ouest", "Afrique centrale", "Océan Indien"))
    fr = next(t["artistes"] for t in terr if t["libelle"] == "France")
    ax.annotate(f"La France seule recense {fr/total_af:.0f} fois plus d'artistes\n"
                f"que toute l'Afrique francophone subsaharienne réunie\n"
                f"({fr:,} contre {total_af:,})".replace(",", " "),
                xy=(0.44, 0.52), xycoords="axes fraction", fontsize=10.5,
                color=ORANGE, fontweight="bold", linespacing=1.6)

    fig.tight_layout(rect=[0, 0.075, 1, 0.915])
    pied(fig, date)
    f = SORTIE / "graph_francophonie_1_fracture.png"
    fig.savefig(f, dpi=170, facecolor="white")
    plt.close(fig)
    return f


# === Figure 2 — L'inégalité est en amont ====================================

def figure_2(terr, date):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 8), sharey=True,
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    noms = [t["libelle"] for t in terr][::-1]
    vals = [t["artistes"] for t in terr][::-1]
    dz = [t["liens_pct"].get("deezer", 0) for t in terr][::-1]
    cols = [COULEUR_GROUPE.get(t["groupe"], GRIS) for t in terr][::-1]

    ax1.barh(noms, vals, color=cols, height=0.72)
    ax1.set_xscale("log")
    ax1.set_xlim(50, 150000)
    ax1.invert_xaxis()
    ax1.set_xlabel("Artistes recensés (log)", fontsize=10)
    ax1.set_title("Existence au catalogue", fontsize=12.5, fontweight="bold",
                  color=BLEU, pad=10)
    ax1.grid(axis="x", color=GRIS_PALE)
    ax1.set_axisbelow(True)

    ax2.barh(noms, dz, color=cols, height=0.72)
    ax2.set_xlim(0, 30)
    ax2.set_xlabel("Artistes avec lien Deezer documenté (%)", fontsize=10)
    ax2.set_title("Documentation vers les plateformes", fontsize=12.5,
                  fontweight="bold", color=BLEU, pad=10)
    ax2.grid(axis="x", color=GRIS_PALE)
    ax2.set_axisbelow(True)
    for nom, v in zip(noms, dz):
        ax2.text(v + 0.6, nom, f"{v:.0f} %", va="center", fontsize=8.5, color=BLEU)

    for ax in (ax1, ax2):
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0, labelsize=9.5)
    ax1.tick_params(axis="y", pad=14)

    fig.text(0.012, 0.982, "L'inégalité est en amont, pas en aval",
             fontsize=16, fontweight="bold", color=BLEU, va="top", ha="left")
    fig.text(0.012, 0.945,
             "À gauche, un rapport de 1 à 900 entre les territoires. À droite, des taux qui se tiennent tous "
             "entre 5 et 24 %.\nUne fois qu'un artiste existe au catalogue, il est documenté vers les plateformes "
             "aussi bien au Niger qu'en France.",
             fontsize=10.5, color=GRIS, linespacing=1.6, va="top", ha="left")

    fig.tight_layout(rect=[0, 0.075, 1, 0.885])
    pied(fig, date)
    f = SORTIE / "graph_francophonie_2_amont_aval.png"
    fig.savefig(f, dpi=170, facecolor="white")
    plt.close(fig)
    return f


# === Figure 3 — Densité par million d'habitants =============================

def figure_3(terr, date):
    data = [(t["libelle"], t["artistes"] / POPULATION_M[t["libelle"]],
             COULEUR_GROUPE.get(t["groupe"], GRIS))
            for t in terr if t["libelle"] in POPULATION_M]
    data.sort(key=lambda x: x[1])

    fig, ax = plt.subplots(figsize=(11, 8))
    noms = [d[0] for d in data]
    vals = [d[1] for d in data]
    cols = [d[2] for d in data]

    ax.barh(noms, vals, color=cols, height=0.72)
    ax.set_xscale("log")
    ax.set_xlim(0.8, 8000)
    ax.set_xlabel("Artistes recensés par million d'habitants (échelle logarithmique)", fontsize=10)
    fig.text(0.012, 0.982, "Densité documentaire : qui a les moyens d'être catalogué ?",
             fontsize=16, fontweight="bold", color=BLEU, va="top", ha="left")
    fig.text(0.012, 0.945,
             "Artistes MusicBrainz par million d'habitants — populations approximatives, à recouper",
             fontsize=11, color=GRIS, va="top", ha="left")

    for nom, v in zip(noms, vals):
        ax.text(v * 1.14, nom, f"{v:,.0f}".replace(",", " ") if v >= 10 else f"{v:.1f}",
                va="center", fontsize=8.5, color=BLEU)

    ax.grid(axis="x", color=GRIS_PALE)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9.5)

    haut, bas = vals[-1], vals[0]
    ax.annotate(f"Du plus dense au moins dense :\nun rapport de {haut/bas:,.0f} pour 1".replace(",", " "),
                xy=(0.42, 0.13), xycoords="axes fraction", fontsize=11,
                color=ORANGE, fontweight="bold", linespacing=1.6)

    fig.tight_layout(rect=[0, 0.075, 1, 0.915])
    pied(fig, date)
    f = SORTIE / "graph_francophonie_3_densite.png"
    fig.savefig(f, dpi=170, facecolor="white")
    plt.close(fig)
    return f


# === Figure 4 — La taxonomie Deezer =========================================

GENRES_MUSICAUX = ["Pop", "Rap/Hip Hop", "Rock", "Dance", "R&B", "Alternative",
                   "Electro", "Folk", "Reggae", "Jazz", "Country", "Classical",
                   "Films/Games", "Metal", "Soul & Funk", "Blues", "Kids"]
GENRES_GEO = ["African Music", "Asian Music", "Brazilian Music",
              "Indian Music", "Latin Music", "French Chanson"]


def figure_4(date):
    fig, ax = plt.subplots(figsize=(12.5, 8.5))
    ax.axis("off")

    ax.text(0.01, 0.985, "Ce que la taxonomie de la plateforme dit du monde",
            fontsize=16.5, fontweight="bold", color=BLEU, va="top",
            transform=ax.transAxes)
    ax.text(0.01, 0.935,
            "Les 24 catégories de l'API publique Deezer, relevées le 26 août 2026",
            fontsize=11, color=GRIS, va="top", transform=ax.transAxes)

    # Colonne de gauche — genres musicaux, sur deux sous-colonnes
    ax.text(0.03, 0.855, "Décrites par leur musique", fontsize=13.5,
            fontweight="bold", color=BLEU, va="top", transform=ax.transAxes)
    ax.text(0.03, 0.815, f"{len(GENRES_MUSICAUX)} catégories sur 24", fontsize=10,
            color=GRIS, va="top", transform=ax.transAxes)
    moitie = (len(GENRES_MUSICAUX) + 1) // 2
    for i, g in enumerate(GENRES_MUSICAUX[:moitie]):
        ax.text(0.04, 0.755 - i * 0.052, "· " + g, fontsize=11.5,
                color=BLEU, va="top", transform=ax.transAxes)
    for i, g in enumerate(GENRES_MUSICAUX[moitie:]):
        ax.text(0.25, 0.755 - i * 0.052, "· " + g, fontsize=11.5,
                color=BLEU, va="top", transform=ax.transAxes)

    ax.plot([0.46, 0.46], [0.17, 0.87], color=GRIS_PALE, lw=2,
            transform=ax.transAxes)

    # Colonne de droite — catégories géographiques
    ax.text(0.50, 0.855, "Décrites par leur géographie", fontsize=13.5,
            fontweight="bold", color=ORANGE, va="top", transform=ax.transAxes)
    ax.text(0.50, 0.815, f"{len(GENRES_GEO)} catégories sur 24", fontsize=10,
            color=GRIS, va="top", transform=ax.transAxes)
    for i, g in enumerate(GENRES_GEO):
        ax.text(0.51, 0.755 - i * 0.052, "· " + g, fontsize=11.5,
                color=ORANGE, va="top", transform=ax.transAxes)

    ax.text(0.50, 0.415,
            "Une seule catégorie pour 54 pays et des\n"
            "centaines de traditions : le mbalax sénégalais,\n"
            "la rumba congolaise, le griot malien et le raï\n"
            "algérien y sont indistincts.",
            fontsize=11, color=BLEU, va="top", linespacing=1.7,
            transform=ax.transAxes)
    ax.text(0.50, 0.245,
            "Il n'existe ni « European Music » ni « North\n"
            "American Music ». « French Chanson » est la\n"
            "seule catégorie nationale européenne : la\n"
            "francophonie musicale se trouve donc découpée\n"
            "par une ligne qui n'est pas linguistique.",
            fontsize=11, color=BLEU, va="top", linespacing=1.7,
            transform=ax.transAxes)

    ax.text(0.04, 0.26,
            "L'endpoint /genre/{id}/artists retourne la même\n"
            "liste globale quel que soit le genre demandé.\n"
            "La taxonomie est donc consultable mais non\n"
            "exploitable : elle devient objet d'étude\n"
            "plutôt qu'outil.",
            fontsize=9.5, color=GRIS, style="italic", va="top",
            linespacing=1.7, transform=ax.transAxes)

    fig.text(0.012, 0.018,
             "Source : API publique Deezer, endpoint /genre, relevé du 26 août 2026. "
             "Carnet de données — souveraineté culturelle numérique · démarche indépendante.",
             fontsize=6.5, color=GRIS)

    f = SORTIE / "graph_francophonie_4_taxonomie.png"
    fig.savefig(f, dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return f


def main():
    d, terr = charger()
    date = d.get("date_sonde", "")
    print(f"Sonde du {date} — {len(terr)} territoires mesurés\n")
    for f in (figure_1(terr, date), figure_2(terr, date),
              figure_3(terr, date), figure_4(date)):
        print("  ✓", f.name)
    print(f"\nDossier : {SORTIE}")


if __name__ == "__main__":
    main()
