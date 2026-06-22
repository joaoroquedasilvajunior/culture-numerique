"""
Dériveur des cinq repères du Carnet de données — souveraineté culturelle numérique.

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


# === Lentille 3 améliorée — dérivation auxiliaire hors protocole =============
#
# Cette dérivation croise les effectifs (ISQ EERH série annuelle, niveau SCIAN
# 4 chiffres) avec la rémunération hebdomadaire moyenne (StatCan CANSIM
# 14-10-0223, niveau SCIAN 2 chiffres) pour classer chaque secteur en
# consolidation / contraction nette / expansion saine / précarisation.
#
# Elle s'inscrit dans le cadre de la grille AI-exposure (méthodologie à trois
# lentilles : demande experte, usage révélé, sortie matérielle wages). Notre
# dépôt n'instrumente que la lentille 3 actuellement ; cette dérivation enrichit
# cette lentille en combinant deux mesures matérielles complémentaires.
#
# Statut : **auxiliaire provisoire**. Pas gelée par le protocole v1.1.0, pas un
# repère au sens du Protocole. Présente dans le payload pour exposition, à
# considérer comme un signal analytique à raffiner.
#
# Limite assumée : la rémunération n'existe qu'au niveau SCIAN 2 chiffres pour
# les coupes provinciales. Les effectifs ISQ niveau 4 chiffres sont exposés en
# contexte, mais la classification est faite au niveau 2 chiffres où les deux
# mesures coexistent.

SEUIL_VARIATION_PCT = 2.0  # ±2 % en deçà = stable (sous le bruit + IPC)

# Mapping de nos SCIAN 4 chiffres ISQ vers leur secteur SCIAN 2 chiffres parent.
# Sert à exposer le contexte « composantes ISQ » sous chaque secteur classifié.
SCIAN_4_TO_2 = {
    '5121': '51', '5122': '51', '5131': '51', '5132': '51',
    '5151': '51', '5152': '51', '5161': '51', '5162': '51',
    '517': '51', '5191': '51',
    '7111': '71', '7112': '71', '7113': '71', '7115': '71',
    '712': '71', '7121': '71', '713': '71',
    '4592': '459',  # Hors [51] et [71], mais on l'expose en contexte si présent
}


def _classifier(var_eff_pct: float | None, var_rem_pct: float | None,
                seuil: float = SEUIL_VARIATION_PCT) -> dict:
    """Quatre quadrants standard de la lentille 3."""
    if var_eff_pct is None or var_rem_pct is None:
        return {"classification": "indeterminee",
                "raison": "donnée manquante sur une des deux mesures"}
    eff_baisse = var_eff_pct <= -seuil
    eff_hausse = var_eff_pct >= seuil
    rem_baisse = var_rem_pct <= -seuil
    rem_hausse = var_rem_pct >= seuil

    if eff_baisse and rem_hausse:
        return {"classification": "consolidation",
                "lecture": ("La valeur se concentre chez les survivants. "
                            "Les emplois supprimés étaient en moyenne moins "
                            "bien rémunérés que ceux qui restent, OU les "
                            "survivants ont obtenu des hausses, OU effet de "
                            "composition interne du secteur.")}
    if eff_baisse and rem_baisse:
        return {"classification": "contraction_nette",
                "lecture": ("Perte de valeur globale. Moins d'emplois, et les "
                            "emplois restants sont moins bien payés. Signal "
                            "fort de désinvestissement sectoriel.")}
    if eff_hausse and rem_hausse:
        return {"classification": "expansion_saine",
                "lecture": ("Capture de valeur et croissance simultanées. Le "
                            "secteur attire des emplois et les rémunère mieux.")}
    if eff_hausse and rem_baisse:
        return {"classification": "precarisation",
                "lecture": ("Plus d'emplois mais moins bien payés. Le secteur "
                            "grossit en absorbant des emplois moins qualifiés "
                            "ou moins rémunérés.")}
    # Stable sur au moins une des deux dimensions
    return {"classification": "stable",
            "lecture": (f"Variation sous le seuil de {seuil} % sur au moins "
                        f"une des deux mesures. Pas de mouvement structurel "
                        f"détecté entre les deux années comparées.")}


def _var_pct(v_initial: float | None, v_final: float | None) -> float | None:
    if v_initial is None or v_final is None or v_initial == 0:
        return None
    return round((v_final - v_initial) / v_initial * 100, 2)


def derive_lentille_3_amelioree(emplois_eerh_annuel: list,
                                  remunerations_statcan: dict,
                                  annee_initiale: int = 2024,
                                  annee_finale: int = 2025) -> dict:
    """Croise effectifs (ISQ niveau 4 chiffres) et rémunération hebdomadaire
    moyenne (StatCan niveau 2 chiffres) pour classifier chaque secteur SCIAN
    2 chiffres sur la grille consolidation / contraction nette / expansion
    saine / précarisation.

    Retourne un bloc analytique à inscrire dans le payload sous une clé
    distincte du bloc `reperes` (ce n'est PAS un repère du protocole).
    """
    # Index des effectifs annuels par SCIAN 4 chiffres
    index_eff_4 = {ind['scian']: ind for ind in emplois_eerh_annuel if ind.get('scian')}

    secteurs_out = []
    for sect in remunerations_statcan.get('secteurs', []):
        code_2 = sect['code_scian']
        libelle = sect['libelle']

        # Récupérer les moyennes annuelles 2024 et 2025 (effectifs + rémunération)
        eff_par_an = {m['annee']: m['valeur'] for m in
                      sect['mesures'].get('effectifs', {}).get('moyennes_annuelles', [])}
        rem_par_an = {m['annee']: m['valeur'] for m in
                      sect['mesures'].get('remuneration_hebdo', {}).get('moyennes_annuelles', [])}

        var_eff = _var_pct(eff_par_an.get(annee_initiale), eff_par_an.get(annee_finale))
        var_rem = _var_pct(rem_par_an.get(annee_initiale), rem_par_an.get(annee_finale))

        verdict = _classifier(var_eff, var_rem)

        # Composantes ISQ niveau 4 chiffres rattachées à ce secteur 2 chiffres
        composantes = []
        for scian_4, sect_parent in SCIAN_4_TO_2.items():
            if sect_parent != code_2:
                continue
            ind = index_eff_4.get(scian_4)
            if ind is None:
                continue
            composantes.append({
                'scian': ind['scian'],
                'industrie': ind['industrie'],
                'n_2024': ind.get('n_2024'),
                'n_2025': ind.get('n_2025'),
                'tca_2025': ind.get('tca_2025'),
            })

        secteurs_out.append({
            'code_scian': code_2,
            'libelle': libelle,
            'effectifs': {
                f'moyenne_{annee_initiale}': eff_par_an.get(annee_initiale),
                f'moyenne_{annee_finale}': eff_par_an.get(annee_finale),
                'variation_pct': var_eff,
            },
            'remuneration_hebdo': {
                f'moyenne_{annee_initiale}': rem_par_an.get(annee_initiale),
                f'moyenne_{annee_finale}': rem_par_an.get(annee_finale),
                'variation_pct': var_rem,
            },
            **verdict,
            'composantes_ISQ_niveau_4': composantes,
        })

    return {
        'methode': ('Croisement effectifs ISQ EERH (niveau SCIAN 4 chiffres, '
                    'série annuelle) × rémunération hebdomadaire moyenne StatCan '
                    'CANSIM 14-10-0223 (niveau SCIAN 2 chiffres, agrégée annuel). '
                    'Classification en quatre quadrants standard de la lentille 3 '
                    'AI-exposure : consolidation, contraction nette, expansion '
                    'saine, précarisation. Seuil de stabilité : ±%s %%.' %
                    SEUIL_VARIATION_PCT),
        'note_limites': ('Classification opérée au niveau SCIAN 2 chiffres parce '
                         'que la rémunération n\'est diffusée qu\'à ce niveau pour '
                         'les coupes provinciales. Les composantes ISQ niveau 4 '
                         'chiffres sont exposées en contexte ; leur lecture '
                         'individuelle reste limitée à la dimension effectifs.'),
        'annees_comparees': [annee_initiale, annee_finale],
        'seuil_stabilite_pct': SEUIL_VARIATION_PCT,
        'statut': 'auxiliaire_provisoire',
        'note_statut': ('Dérivation analytique hors protocole v1.1.0. Pas un '
                        'repère gelé. Présente dans le payload pour exposition, '
                        'à raffiner avec les futures itérations de la méthode '
                        'AI-exposure.'),
        'secteurs': secteurs_out,
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

    # Bloc auxiliaire — lentille 3 améliorée (hors protocole)
    lentille_3 = None
    if ('emplois_eerh_annuel' in combined
            and 'remunerations_eerh_statcan' in combined):
        lentille_3 = derive_lentille_3_amelioree(
            combined['emplois_eerh_annuel'],
            combined['remunerations_eerh_statcan']
        )

    # Bloc auxiliaire — lentille 2 « usage révélé » (hors protocole)
    # Lecture directe de l'extraction AEI Canada, pas de transformation
    # supplémentaire à ce stade. L'extracteur a déjà calculé les agrégats
    # productif/apprentissage et identifié le périmètre créatif.
    lentille_2 = combined.get('aei_canada')

    # Bloc auxiliaire — lentille 1b « demande marché » (hors protocole)
    # Lecture directe de l'extraction JVWS Québec. L'extracteur expose les
    # 6 sous-secteurs SCIAN culture avec leur série trimestrielle + moyennes
    # sur les 5 derniers trimestres.
    lentille_1b = combined.get('job_vacancy_quebec')

    payload = {
        "annee": annee,
        "date_calcul": dt.datetime.now().isoformat(timespec='seconds'),
        "protocole_version": PROTOCOLE_VERSION,
        "reperes": reperes
    }
    if lentille_3 is not None:
        payload["lentille_3_ameliorée"] = lentille_3
    if lentille_2 is not None:
        payload["lentille_2_usage_revele"] = {
            'statut': 'auxiliaire_provisoire',
            'note_statut': ('Dérivation analytique hors protocole v1.1.0. Pas un '
                            'repère gelé. Sert la lentille 2 « usage révélé » de '
                            'la méthode AI-exposure : ce que les utilisateurs '
                            'canadiens de Claude.ai font réellement, par tâche '
                            'O*NET et par mode de collaboration.'),
            **lentille_2,
        }
    if lentille_1b is not None:
        payload["lentille_1b_demande_marche"] = {
            'statut': 'auxiliaire_provisoire',
            'note_statut': ('Dérivation analytique hors protocole v1.1.0. Pas un '
                            'repère gelé. Sert la sous-lentille 1b « demande '
                            'marché » de l\'analyse AI-exposure : ce que les '
                            'employeurs québécois cherchent réellement à '
                            'embaucher dans les industries culturelles, à quel '
                            'salaire, à quel taux de vacance.'),
            **lentille_1b,
        }
    return payload
