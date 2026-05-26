"""
Dériveur des cinq repères de l'Observatoire de la souveraineté culturelle numérique.

Conformément au Protocole v1.1.0 (gel initial 2026-05-25, révision mineure
2026-05-26 — matrice R4 figée en annexe, conventions externes R5) :

  R1 — Écart de découvrabilité          (ratio + écart absolu)
  R2 — Profondeur du catalogue          (N₂₀)
  R3 — Consommation québécoise absolue  (canal par canal)
  R4 — Indice d'angle mort              (matrice 4×3 UNESCO 2025, gelée — 8/12)
  R5 — Volume d'œuvres                  (placeholder ; sources à identifier)

Marquage `"provisional": true` pour les repères lus en YTD vivant (R1, R2, R3) tant
que la baseline annuelle ISQ n'a pas été figée au 1ᵉʳ mars de l'année suivante
(tâche #26). R4 n'est pas provisional : sa matrice est gelée par le protocole.
R5 est un placeholder (`provisional: null`) tant que les sources ne sont pas branchées.

Les fonctions consomment directement les dictionnaires produits par
`src/extract.py`. Elles ne dépendent pas de Path ni du système de fichiers et
peuvent être appelées hors pipeline (notamment depuis les tests).
"""

from __future__ import annotations
import datetime as dt
from typing import Any

# === Version du protocole ====================================================
# Toute modification de la matrice R4, de la définition opérationnelle d'un
# repère, ou de la règle de comptage exige un bump de version ET la mise à jour
# du journal des révisions dans Protocole_reperes_observatoire.md.

PROTOCOLE_VERSION = "1.1.0"
DATE_GEL_MATRICE = "2026-05-25"

# === Matrice R4 — gelée 2026-05-25, annexée 2026-05-26 (protocole v1.1.0) ===
# 4 capitaux UNESCO 2025 × 3 étapes de la chaîne culturelle.
#
# États documentés :
#   "plein"   (✓)  — un indicateur statistique au sens strict couvre la cellule
#   "partiel" (⚠) — couverture par indicateur partiel, par sous-ensemble, ou
#                    par proxy explicitement identifié
#   "absent"  (✗)  — aucune mesure publique connue dans le périmètre ISQ/OCCQ/MCC/CRTC
#
# RÈGLE DE COMPTAGE : binaire. `plein` OU `partiel` ⇒ couverte (+1 au numérateur).
# La qualité de la couverture (✓ vs ⚠) est documentée mais n'influe pas sur A.
# Cette règle est inscrite dans la définition opérationnelle du protocole :
# « qualité non incluse » — une cellule couverte par un indicateur faible compte
# autant qu'une cellule bien instrumentée.

MATRICE_R4: dict[str, dict[str, dict[str, Any]]] = {
    "economique": {
        "creation_production": {
            "etat": "partiel",
            "source": ("Indicateurs des résultats d'exploitation des établissements "
                       "cinématographiques (ISQ 2736) — composante production")
        },
        "diffusion_consommation": {
            "etat": "plein",
            "source": ("Triade Loi 109 art. 33 — ISQ 4153 / 2620 / 2140 / 3059 "
                       "/ 2342 / 3171")
        },
        "preservation_transmission": {
            "etat": "partiel",
            "source": ("Nombre d'établissements culturels (ISQ 929) — "
                       "sous-ensemble institutions muséales")
        }
    },
    "naturel": {
        "creation_production": {"etat": "absent", "source": None},
        "diffusion_consommation": {"etat": "absent", "source": None},
        "preservation_transmission": {
            "etat": "partiel",
            "source": ("Registre du patrimoine culturel (MCC) — couverture "
                       "indirecte par inventaire patrimonial")
        }
    },
    "humain": {
        "creation_production": {
            "etat": "partiel",
            "source": ("Emplois salariés EERH (ISQ 2576) — salariés seulement, "
                       "autonomes invisibles à la statistique")
        },
        "diffusion_consommation": {
            "etat": "partiel",
            "source": ("Emplois salariés EERH (ISQ 2576) — même limite que "
                       "création-production")
        },
        "preservation_transmission": {
            "etat": "partiel",
            "source": ("Statistiques des bibliothèques publiques du Québec "
                       "(MCC / BAnQ) — proxy de transmission culturelle")
        }
    },
    "social": {
        "creation_production": {"etat": "absent", "source": None},
        "diffusion_consommation": {
            "etat": "partiel",
            "source": ("Principaux indicateurs en culture par région (ISQ 4850) "
                       "— proxy faible, ne couvre pas le capital social au sens strict")
        },
        "preservation_transmission": {"etat": "absent", "source": None}
    }
}


def _est_couverte(etat: str) -> bool:
    """Règle de comptage R4 : plein OU partiel = couverte."""
    return etat in ("plein", "partiel")


# === Dériveurs unitaires =====================================================

def derive_r1(part_qc: dict) -> dict:
    """R1 — Écart de découvrabilité.

    Ratio R = p_alb / p_str ; écart absolu E = p_alb − p_str (points de %).
    """
    p_str = part_qc['indicateurs']['streaming']['cumul_ytd_pct']
    p_alb = part_qc['indicateurs']['albums_numeriques']['cumul_ytd_pct']
    ratio = round(p_alb / p_str, 2) if p_str else None
    ecart = round(p_alb - p_str, 1)
    return {
        "ratio": ratio,
        "ecart_pts": ecart,
        "part_albums_numeriques_pct": p_alb,
        "part_streaming_pct": p_str,
        "source": "ISQ tableau 4153",
        "periode": part_qc.get('periode'),
        "provisional": True,
        "note": ("Lecture YTD courante. Valeur 2025 à figer au 1ᵉʳ mars sur "
                 "l'archive ISQ annuelle (tâche #26).")
    }


def derive_r2(palmares: list) -> dict:
    """R2 — Profondeur du catalogue (N₂₀).

    Nombre d'interprètes québécois distincts dans le top 20 cumulatif annuel.
    """
    qc = [t for t in palmares if t.get('provenance') == 'Québec']
    interpretes = sorted(set(t['interprete'] for t in qc))
    rangs_qc = sorted(t['rang'] for t in qc)
    return {
        "n20": len(interpretes),
        "interpretes": interpretes,
        "rangs_quebecois": rangs_qc,
        "source": "ISQ — Palmarès des enregistrements musicaux (cumulatif annuel)",
        "provisional": True
    }


def derive_r3(volume_musique: dict, part_qc: dict,
              cinema_pays: dict | None = None) -> dict:
    """R3 — Consommation québécoise absolue, canal par canal.

    Pondération multiplicative : C_c = volume_total × (part_QC / 100).
    Lecture canal par canal — la somme inter-canaux n'a pas de sens (unités
    hétérogènes : écoutes, unités, recettes).
    """
    canaux: dict[str, dict] = {}

    # Streaming musical (k écoutes)
    try:
        v_str = volume_musique['indicateurs']['streaming']['cumul_ytd']
        p_str = part_qc['indicateurs']['streaming']['cumul_ytd_pct']
        canaux['streaming_musique'] = {
            "volume_total_k_ecoutes": v_str,
            "part_qc_pct": p_str,
            "consommation_qc_k_ecoutes": round(v_str * p_str / 100, 1),
            "provisional": True
        }
    except (KeyError, TypeError):
        canaux['streaming_musique'] = {"status": "donnees_indisponibles"}

    # Albums numériques téléchargés (unités)
    try:
        v_alb = volume_musique['indicateurs']['albums_numeriques']['cumul_ytd']
        p_alb = part_qc['indicateurs']['albums_numeriques']['cumul_ytd_pct']
        canaux['albums_numeriques'] = {
            "volume_total_unites": v_alb,
            "part_qc_pct": p_alb,
            "consommation_qc_unites": round(v_alb * p_alb / 100, 0),
            "provisional": True
        }
    except (KeyError, TypeError):
        canaux['albums_numeriques'] = {
            "status": "donnees_indisponibles",
            "note": ("Structure volume_musique['indicateurs']['albums_numeriques']"
                     " absente de l'extraction courante.")
        }

    # Cinéma — part QC disponible en YTD ; recettes annuelles requises pour C_film
    if cinema_pays:
        try:
            qc = next(p for p in cinema_pays['pays'] if p['pays'] == 'Québec')
            canaux['cinema'] = {
                "part_qc_box_office_pct": qc.get('pct_cumul_ytd'),
                "consommation_absolue_recettes_qc": None,
                "status": "donnees_annuelles_a_venir",
                "note": ("Recettes totales annuelles requises pour C_film ; "
                         "indicateurs_cinema est annuel mais cinema_pays est YTD — "
                         "consolidation au 1ᵉʳ mars année+1.")
            }
        except (StopIteration, KeyError, TypeError):
            canaux['cinema'] = {"status": "donnees_indisponibles"}

    return {
        "canaux": canaux,
        "definition_operationnelle": "C_c = volume_total × part_QC (par canal)"
    }


def derive_r4() -> dict:
    """R4 — Indice d'angle mort. Matrice statique gelée par le protocole."""
    cellules_couvertes = 0
    total = 0
    for capital, etapes in MATRICE_R4.items():
        for etape, info in etapes.items():
            total += 1
            if _est_couverte(info['etat']):
                cellules_couvertes += 1
    return {
        "a": round(cellules_couvertes / total, 3),
        "cellules_couvertes": cellules_couvertes,
        "total": total,
        "matrice": MATRICE_R4,
        "regle_comptage": ("Binaire : `plein` OU `partiel` ⇒ couverte. La "
                           "qualité de la couverture (✓ vs ⚠) est documentée "
                           "dans la matrice mais n'influe pas sur le numérateur. "
                           "Conformément à la limite déjà reconnue par le "
                           "protocole : « qualité non incluse »."),
        "provisional": False,
        "version_protocole": PROTOCOLE_VERSION,
        "date_gel": DATE_GEL_MATRICE
    }


def derive_r5() -> dict:
    """R5 — Volume d'œuvres québécoises rendues publiques. Chantier ouvert."""
    return {
        "status": "en_chantier",
        "note": ("Sources à identifier avant première mesure : ADISQ (musique), "
                 "SODEC / Téléfilm Canada (cinéma), OCCQ / dépôt légal BAnQ "
                 "(livre). La définition de « œuvre québécoise » sera alignée sur "
                 "les conventions institutionnelles existantes (critères ADISQ ; "
                 "grille SODEC de qualification du film québécois ; convention "
                 "OCCQ de l'édition) plutôt qu'inventée pour le protocole."),
        "provisional": None
    }


# === Orchestration ===========================================================

def derive_all(combined: dict, annee: int = 2025) -> dict:
    """Calcule les cinq repères à partir du dict combiné produit par le pipeline.

    Tolère l'absence d'une source : le repère concerné est alors marqué
    `status: donnees_indisponibles`, le reste du calcul continue.
    """
    reperes: dict[str, dict] = {}

    if 'part_qc' in combined:
        reperes['r1_ecart_decouvrabilite'] = derive_r1(combined['part_qc'])
    else:
        reperes['r1_ecart_decouvrabilite'] = {
            "status": "donnees_indisponibles",
            "raison": "source part_qc absente du dataset"
        }

    if 'palmares_top20' in combined:
        reperes['r2_profondeur_catalogue'] = derive_r2(combined['palmares_top20'])
    else:
        reperes['r2_profondeur_catalogue'] = {
            "status": "donnees_indisponibles",
            "raison": "source palmares_top20 absente du dataset"
        }

    if 'volume_musique' in combined and 'part_qc' in combined:
        reperes['r3_consommation_absolue'] = derive_r3(
            combined['volume_musique'],
            combined['part_qc'],
            combined.get('cinema_pays')
        )
    else:
        reperes['r3_consommation_absolue'] = {
            "status": "donnees_indisponibles",
            "raison": "sources volume_musique et part_qc requises"
        }

    reperes['r4_angle_mort'] = derive_r4()
    reperes['r5_volume_oeuvres'] = derive_r5()

    return {
        "annee": annee,
        "date_calcul": dt.datetime.now().isoformat(timespec='seconds'),
        "protocole_version": PROTOCOLE_VERSION,
        "reperes": reperes
    }
