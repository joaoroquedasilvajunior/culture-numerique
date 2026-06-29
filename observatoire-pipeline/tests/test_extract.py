"""
Tests d'intégrité sur les extracteurs.

Ces tests vérifient que les fichiers ISQ déposés dans data/raw/ produisent les
valeurs-clés attendues. Si l'ISQ révise ses chiffres ou si la structure du
tableau change, les tests échouent — c'est le signal pour mettre à jour
l'extracteur correspondant.
"""

from __future__ import annotations
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import yaml

from src import extract
from src.pipeline import find_source_file, _resolve_raw_dir


@pytest.fixture
def raw_dir():
    """Lit le dossier configuré dans sources.yaml — s'aligne sur la config réelle."""
    config = yaml.safe_load((REPO_ROOT / 'sources.yaml').read_text(encoding='utf-8'))
    return _resolve_raw_dir(REPO_ROOT, config)


def test_part_qc_streaming(raw_dir):
    """Part QC streaming YTD — semaine du 24 au 30 avril 2026 = 6,9 %."""
    f = find_source_file(raw_dir, 'Part des interprètes*.xlsx')
    assert f is not None, "Fichier Part des interprètes manquant dans data/raw/"
    data = extract.extract_part_qc(f)
    assert data['indicateurs']['streaming']['cumul_ytd_pct'] == 6.9


def test_part_qc_albums_numeriques(raw_dir):
    """Part QC albums numériques YTD — semaine du 22 au 28 mai 2026 = 24,1 %.

    Source : ISQ tableau 4153, mise à jour 12 juin 2026.
    La part QC a légèrement reculé sur 4 semaines (24,5 → 24,1 %) mais reste
    la plus élevée des canaux numériques.
    """
    f = find_source_file(raw_dir, 'Part des interprètes*.xlsx')
    data = extract.extract_part_qc(f)
    assert data['indicateurs']['albums_numeriques']['cumul_ytd_pct'] == 24.1


def test_volume_streaming(raw_dir):
    """Streaming cumulatif YTD = 13 027 963,2 milliers d'écoutes (semaine du 22-28 mai 2026).

    Source : ISQ tableau 2140, mise à jour 12 juin 2026.
    Volume YTD passé de 4,83 G (cumul à fin avril) à 13,03 G (cumul à fin mai) —
    avance temporelle attendue du cumul, pas une révision rétroactive.
    """
    f = find_source_file(raw_dir, "Consommation d'enregistrements musicaux*.xlsx")
    data = extract.extract_volume_musique(f)
    assert data['indicateurs']['streaming']['cumul_ytd'] == 13027963.2


def test_cinema_quebec(raw_dir):
    """Part QC box-office YTD = 3,9 %, var an−1 = −38,7 % (semaine 24-30 avril 2026).

    Source : ISQ, fichier hebdomadaire mis à jour le 9 juin 2026.
    Le pattern inclut « hebdomadaires » pour ne pas matcher le nouveau
    fichier annuel publié simultanément (cinema_pays_annuel).

    ⚠ Révision ISQ entre les versions du 22 mai et du 9 juin (même semaine
    de référence) : pct_cumul_ytd 4,7 → 3,9 % ; var_cumul 12,4 → 38,7 %.
    À documenter dans le ledger / la chronique.
    """
    f = find_source_file(
        raw_dir,
        "Résultats d'exploitation des établissements*pays d'origine*hebdomadaires*.xlsx"
    )
    assert f is not None, "Fichier cinéma pays d'origine (hebdomadaire) manquant"
    data = extract.extract_cinema_pays(f)
    qc = next(p for p in data['pays'] if p['pays'] == 'Québec')
    assert qc['pct_cumul_ytd'] == 3.9
    assert qc['var_cumul_an_prec_pct'] == -38.7


def test_palmares_quebec_count(raw_dir):
    """Un seul interprète québécois dans le top 20 — Les Cowboys Fringants au rang 17.

    Source : ISQ Palmarès cumulatif annuel, mise à jour 12 juin 2026.
    L'unique entrée québécoise est descendue du rang 15 au rang 17 entre la
    semaine du 24-30 avril et celle du 22-28 mai 2026. La diversité reste à 1.
    """
    f = find_source_file(raw_dir, 'Palmarès des enregistrements*.xlsx')
    data = extract.extract_palmares(f)
    qc = [t for t in data if t['provenance'] == 'Québec']
    assert len(qc) == 1
    assert qc[0]['interprete'] == 'Les Cowboys Fringants'
    assert qc[0]['rang'] == 17


def test_evolution_streaming_2024(raw_dir):
    """Écoutes streaming 2024 = 31 004 652,5 (k)."""
    f = find_source_file(raw_dir, 'Évolution de statistiques clés*.xlsx')
    data = extract.extract_evolution(f)
    serie = data['indicateurs']['musique_streaming']['serie']
    val_2024 = next(p['valeur'] for p in serie if p['annee'] == 2024)
    assert val_2024 == 31004652.5


def test_emplois_eerh_mensuel_ytd_2026(raw_dir):
    """Fichier mensuel EERH — l'ISQ a basculé en 2026 (le 10 juin 2026).

    Vérifie la tolérance à l'année partielle : annee_reference=2026,
    mois_disponibles=3 (Jan, Fev, Mar), variation_pct calculée Jan→Mars
    plutôt que Jan→Déc.
    """
    f = find_source_file(raw_dir, 'Emplois salariés*données mensuelles*.xlsx')
    assert f is not None, "Fichier EERH mensuel manquant"
    data = extract.extract_emplois_eerh(f)
    rec = next(r for r in data if r['scian'] == '5121')
    assert rec['annee_reference'] == 2026
    assert rec['mois_disponibles'] == 3
    assert rec['mois_dernier'] == 'Mars'
    # Variation Jan → Mars 2026 ≈ +1,7 % — légère reprise après la chute 2025
    assert rec['variation_pct'] is not None
    assert 1.0 < rec['variation_pct'] < 3.0


def test_emplois_eerh_annuel_5121_baseline_2025(raw_dir):
    """Baseline figée — film et vidéo (5121) : n_2025 = 14 299, TCA 2025 = −8,6 %.

    Source : ISQ EERH série annuelle 2001-2025 (Québec), mise à jour 10 juin 2026.
    Cette baseline annuelle est moins volatile que la variation Jan→Déc
    mensuelle (qui valait −11,6 % sur la même industrie en 2025). Les deux
    mesures sont distinctes mais cohérentes — l'année 2025 a effectivement
    décliné davantage en fin qu'en moyenne annuelle.
    """
    f = find_source_file(raw_dir, 'Emplois salariés*données annuelles*.xlsx')
    assert f is not None, "Fichier EERH annuel manquant"
    data = extract.extract_emplois_eerh_annuel(f)
    rec = next(r for r in data if r['scian'] == '5121')
    assert rec['n_2024'] == 15636.0
    assert rec['n_2025'] == 14299.0
    assert rec['tca_2025'] == -8.6
    # Plage de la série
    assert rec['annees'][0] == 2001
    assert rec['annees'][-1] == 2025


def test_remunerations_eerh_statcan_secteur_51_consolidation(raw_dir):
    """Lentille 3 améliorée — Secteur [51] Information et culture, Québec :
    effectifs reculent (−5,4 %) ET rémunération hebdo moyenne monte (+4,3 %)
    entre 2024 et 2025. Pattern de consolidation cohérent avec une capture
    de valeur côté survivants, à interpréter avec prudence (effet de composition
    interne possible vu la granularité SCIAN 2 chiffres seulement).

    Source : Statistique Canada CANSIM 14-10-0223, dump complet 2026-05-28.
    """
    f = find_source_file(raw_dir, '14100223*.zip')
    assert f is not None, "Dump CANSIM 14-10-0223 manquant"
    data = extract.extract_remunerations_eerh_statcan(f)
    assert data['tableau'] == '14-10-0223'
    sect_51 = next(s for s in data['secteurs'] if s['code_scian'] == '51')
    # Effectifs : moyenne annuelle 2024 et 2025
    eff = {m['annee']: m for m in sect_51['mesures']['effectifs']['moyennes_annuelles']}
    assert eff[2024]['valeur'] == 74287.58
    assert eff[2024]['n_mois'] == 12
    assert eff[2025]['valeur'] == 70294.33
    assert eff[2025]['n_mois'] == 12
    # Rémunération hebdo : moyennes annuelles
    rem = {m['annee']: m for m in sect_51['mesures']['remuneration_hebdo']['moyennes_annuelles']}
    assert rem[2024]['valeur'] == 1673.04
    assert rem[2025]['valeur'] == 1744.35
    # Pattern de consolidation : effectifs ↓, rémunération ↑
    assert eff[2025]['valeur'] < eff[2024]['valeur']
    assert rem[2025]['valeur'] > rem[2024]['valeur']


def test_remunerations_eerh_statcan_secteur_71_stable(raw_dir):
    """Lentille 3 améliorée — Secteur [71] Arts, spectacles, loisirs, Québec :
    effectifs en légère hausse, rémunération hebdo quasi stable. Pattern
    distinct du secteur 51 — moins de pression structurelle.

    Source : Statistique Canada CANSIM 14-10-0223.
    """
    f = find_source_file(raw_dir, '14100223*.zip')
    data = extract.extract_remunerations_eerh_statcan(f)
    sect_71 = next(s for s in data['secteurs'] if s['code_scian'] == '71')
    eff = {m['annee']: m for m in sect_71['mesures']['effectifs']['moyennes_annuelles']}
    rem = {m['annee']: m for m in sect_71['mesures']['remuneration_hebdo']['moyennes_annuelles']}
    assert eff[2024]['valeur'] == 67866.75
    assert eff[2025]['valeur'] == 69045.58
    assert rem[2024]['valeur'] == 782.46
    assert rem[2025]['valeur'] == 787.95
    # Pattern stable : effectifs en très légère hausse, rémunération quasi stable
    assert eff[2025]['valeur'] > eff[2024]['valeur']
    assert abs(rem[2025]['valeur'] - rem[2024]['valeur']) < 10  # variation < 10 $


def test_ai_exposure_culture_perimetre(raw_dir):
    """Sous-lentille 1a « demande experte » — indice C-AIOE pour les
    industries culturelles canadiennes.

    Source : Statistique Canada, Mehdi, Allen, Lesica & Watt (mars 2026).
    Cinq industries culturelles + une catégorie de référence (autres).
    Pattern attendu : video game publishers/design est le plus exposé
    (substitution potentielle ≈ 75 %), motion picture le moins du groupe
    culturel (≈ 54 %), autres industries en référence (≈ 34 %).
    """
    f = find_source_file(raw_dir, 'ai_exposure_culture*.csv')
    assert f is not None, "Fichier ai_exposure_culture manquant"
    data = extract.extract_ai_exposure_culture(f)
    assert data['pays'] == 'Canada (national)'
    assert 'C-AIOE' in data['methode']
    # 5 industries culturelles + 1 catégorie de référence
    codes = [ind['code'] for ind in data['industries']]
    assert '513212+541515' in codes  # video game
    assert '513_hors_513212' in codes  # publishing
    assert '5122+71113' in codes  # sound recording + musical
    assert '5121' in codes  # motion picture
    assert 'autres' in codes  # référence
    # Le tri doit placer video game en tête (HE_LC le plus élevé)
    assert data['industries'][0]['code'] == '513212+541515'
    # Et "autres" en dernier (référence)
    assert data['industries'][-1]['code'] == 'autres'


def test_ai_exposure_culture_video_game(raw_dir):
    """Video game publishers + design : 75,2 % moyenne hommes/femmes de
    substitution potentielle (78,8 % H, 71,6 % F) — le plus exposé du périmètre.
    """
    f = find_source_file(raw_dir, 'ai_exposure_culture*.csv')
    data = extract.extract_ai_exposure_culture(f)
    vg = next(i for i in data['industries'] if i['code'] == '513212+541515')
    assert vg['men+']['he_lc_pct'] == 78.8
    assert vg['women+']['he_lc_pct'] == 71.6
    assert vg['moyenne_sexes']['he_lc_pct'] == 75.2


def test_ai_exposure_culture_motion_picture(raw_dir):
    """Motion picture : 54 % moyenne de substitution potentielle, mais
    14,4 % en faible exposition (le plus de "low exposure" du groupe culturel).
    """
    f = find_source_file(raw_dir, 'ai_exposure_culture*.csv')
    data = extract.extract_ai_exposure_culture(f)
    mp = next(i for i in data['industries'] if i['code'] == '5121')
    assert mp['moyenne_sexes']['he_lc_pct'] == 54.0
    assert mp['moyenne_sexes']['le_pct'] == 14.4


def test_job_vacancy_quebec_perimetre(raw_dir):
    """Sous-lentille 1b « demande marché » — JVWS Québec, 5 derniers trimestres.

    Source : Statistique Canada CANSIM 14-10-0442 (diffusion 16 juin 2026).
    Six SCIAN couverts (512, 513, 516, 519, 711, 712) ; SCIAN 515 archivé.
    Pattern saillant : taux de postes vacants élevé sur [519] (5,0 %) vs faible
    sur [516] (0,9 %). Salaire horaire offert le plus bas sur [712] patrimoine.
    """
    f = find_source_file(raw_dir, '14100442*.zip')
    assert f is not None, "Dump CANSIM 14-10-0442 manquant"
    data = extract.extract_job_vacancy_quebec(f)
    assert data['tableau'] == '14-10-0442-01'
    assert data['periode_max'] == '2026-01'
    # Six SCIAN couverts + un non couvert
    codes = {s['code_scian'] for s in data['secteurs']}
    assert {'512', '513', '516', '519', '711', '712'}.issubset(codes)
    # 515 doit apparaître marqué non couvert
    s_515 = next(s for s in data['secteurs'] if s['code_scian'] == '515')
    assert s_515.get('statut') == 'non_couvert'


def test_job_vacancy_quebec_secteur_512_film(raw_dir):
    """SCIAN 512 (Film et enregistrement sonore) — demande marché modérée,
    salaire offert élevé. Moyenne 5 derniers trimestres : taux ≈ 1,3 %, salaire
    horaire ≈ 41 $/h."""
    f = find_source_file(raw_dir, '14100442*.zip')
    data = extract.extract_job_vacancy_quebec(f)
    s_512 = next(s for s in data['secteurs'] if s['code_scian'] == '512')
    m = s_512['moyennes_5_derniers_trimestres']
    assert m['n_trimestres'] == 5
    # Note : round(1.325, 2) renvoie 1.32 en Python (banker's rounding)
    assert m['taux_postes_vacants'] == 1.32
    assert m['salaire_horaire_offert'] == 41.42
    # La série trimestrielle doit couvrir 2015-01 → 2026-01
    serie = s_512['serie_trimestrielle']
    assert serie[0]['periode'] == '2015-01'
    assert serie[-1]['periode'] == '2026-01'


def test_aei_canada_collaboration_globale(raw_dir):
    """Lentille 2 « usage révélé » — collaboration Canada (semaine du 5-12 fév. 2026).

    Source : Anthropic Economic Index 5e édition, release 2026-03-24.
    Les utilisateurs canadiens de Claude.ai utilisent l'IA majoritairement en
    mode productif (substitution potentielle) plutôt qu'en mode apprentissage.
    Productif (directive + task iteration + feedback loop) = 65,79 %.
    Apprentissage (learning + validation) = 31,40 %. Ratio 2,1×.
    """
    f = find_source_file(raw_dir, 'aei_raw_claude_ai_*.csv')
    assert f is not None, "Fichier AEI Canada manquant"
    data = extract.extract_aei_canada(f)
    assert data['pays'] == 'CA'
    assert data['release_anthropic'] == '2026-03-24'
    assert data['periode_start'] == '2026-02-05'
    assert data['periode_end'] == '2026-02-12'
    # Agrégats collaboration
    ag = data['agregats_collaboration']
    assert ag['productif_pct'] == 65.79
    assert ag['apprentissage_pct'] == 31.40
    assert ag['ratio_productif_apprentissage'] == 2.10
    # Les 6 modes principaux sont tous présents
    collab = data['collaboration_canada']
    for mode in ('directive', 'task iteration', 'learning', 'feedback loop', 'validation', 'none'):
        assert collab[mode] is not None, f"Mode {mode} manquant"


def test_aei_canada_perimetre_creatif(raw_dir):
    """Périmètre créatif du Carnet sur l'AEI Canada : 13 tâches O*NET retenues
    (7 cœur culturel + 6 contenu écrit), pour 4,91 % du total des conversations
    canadiennes. Signal modeste mais visible."""
    f = find_source_file(raw_dir, 'aei_raw_claude_ai_*.csv')
    data = extract.extract_aei_canada(f)
    creatif = data['taches_creatives']
    meta = data['meta']
    assert meta['n_taches_onet_canada_total'] == 271
    assert meta['n_taches_coeur_culturel'] == 7
    assert meta['n_taches_contenu_ecrit'] == 6
    assert creatif['pct_total_coeur_culturel'] == 0.69
    assert creatif['pct_total_contenu_ecrit'] == 4.22
    assert creatif['pct_total_creatif'] == 4.91
    # Vérifie que les tâches cœur culturel sont triées par % décroissant
    coeur_pcts = [t['pct_total_canada'] for t in creatif['coeur_culturel']]
    assert coeur_pcts == sorted(coeur_pcts, reverse=True)
    # La tâche en tête du cœur culturel est la critique d'œuvres
    assert 'write reviews of literary' in creatif['coeur_culturel'][0]['tache_onet']


def test_remunerations_eerh_statcan_periode_couverte(raw_dir):
    """La table CANSIM démarre en janvier 2001 et la diffusion 2026-05-28 va
    jusqu'à mars 2026 (3 mois d'année partielle 2026)."""
    f = find_source_file(raw_dir, '14100223*.zip')
    data = extract.extract_remunerations_eerh_statcan(f)
    assert data['periode_min'] == '2001-01'
    assert data['periode_max'] == '2026-03'
    sect_51 = next(s for s in data['secteurs'] if s['code_scian'] == '51')
    moy_2026 = {m['annee']: m for m in
                sect_51['mesures']['effectifs']['moyennes_annuelles']}.get(2026)
    assert moy_2026 is not None
    assert moy_2026['n_mois'] == 3  # Jan + Fév + Mars 2026


def test_emplois_eerh_annuel_5162_baseline_2025(raw_dir):
    """Baseline figée — distribution contenu en continu (5162) : TCA 2025 = +5,2 %.

    Source : ISQ EERH série annuelle 2001-2025, mise à jour 10 juin 2026.
    Le TCA annuel +5,2 % est nettement inférieur à la variation Jan→Déc 2025
    mensuelle (+30 %) : 2025 a connu une trajectoire fortement ascendante au
    cours de l'année, ce que la moyenne annuelle 2025 ne capture qu'en partie.
    """
    f = find_source_file(raw_dir, 'Emplois salariés*données annuelles*.xlsx')
    assert f is not None, "Fichier EERH annuel manquant"
    data = extract.extract_emplois_eerh_annuel(f)
    rec = next(r for r in data if r['scian'] == '5162')
    assert rec['n_2024'] == 1657.0
    assert rec['n_2025'] == 1743.0
    assert rec['tca_2025'] == 5.2


def test_ventes_livres_total(raw_dir):
    """Ventes totales de livres en septembre 2025 = 73 314 799 $ ; cumul YTD ≈ 543 M $.
    Source : ISQ, tableau 2342, mise à jour 25 mai 2026 (révision : période juin → septembre 2025)."""
    f = find_source_file(raw_dir, 'Variations mensuelles*ventes de livres*.xlsx')
    assert f is not None, "Fichier ventes de livres manquant dans Données Québec/"
    data = extract.extract_ventes_livres(f)
    total = next(L for L in data['lignes'] if L['libelle'] == 'Ventes totales')
    assert total['mois_courant'] == 73314799.0
    assert total['cumul_ytd'] == 542612980.0
    assert 'Septembre' in data['periode']


def test_ventes_categorie(raw_dir):
    """Ventes de livres par catégorie de points de vente — cumul 2025 = 542 612 980 $.
    Source : ISQ, tableau 2341, mise à jour 25 mai 2026."""
    f = find_source_file(raw_dir, 'Ventes de livres neufs*points de vente*.xlsx')
    assert f is not None, "Fichier ventes par catégorie de points de vente manquant"
    data = extract.extract_ventes_categorie(f)
    total = next(L for L in data['lignes'] if L['libelle'] == 'Ventes totales')
    assert total['cumul'] == 542612980.0
    assert total['valeurs'][7] == 112351737.0  # Août — pic de la rentrée scolaire
    assert len(data['mois']) == 9
    assert data['mois'][0] == 'Janvier' and data['mois'][-1] == 'Septembre'
    agreees = next(L for L in data['lignes'] if L['libelle'] == 'Librairies agréées (A)')
    assert agreees['cumul'] == 258349841.0


def test_etablissements_count(raw_dir):
    """Le tableau couvre 2004-2024 (21 années) et liste >= 15 indicateurs."""
    f = find_source_file(raw_dir, 'Nombre d*établissements culturels*.xlsx')
    assert f is not None, "Fichier établissements culturels manquant"
    data = extract.extract_etablissements(f)
    assert data['annees'][0] == 2004
    assert data['annees'][-1] >= 2023
    assert len(data['indicateurs']) >= 15
    # Salles de spectacles : indicateur clé qui doit avoir des valeurs
    salles = next((i for i in data['indicateurs'] if i['libelle'].startswith('Salles')), None)
    assert salles is not None
    assert any(p['valeur'] for p in salles['serie'])


def test_indicateurs_cinema_serie_longue(raw_dir):
    """Les indicateurs cinéma remontent à 1975 ; 13 indicateurs au moins."""
    f = find_source_file(raw_dir, "Indicateurs des résultats d'exploitation*.xlsx")
    assert f is not None, "Fichier indicateurs cinéma manquant"
    data = extract.extract_indicateurs_cinema(f)
    assert data['annees'][0] == 1975
    assert data['annees'][-1] >= 2023
    assert len(data['indicateurs']) >= 10
    # Assistance 1975 : référence absolue, ~20 M
    assistance = next(i for i in data['indicateurs'] if i['libelle'] == 'Assistance')
    val_1975 = next(p['valeur'] for p in assistance['serie'] if p['annee'] == 1975)
    assert val_1975 == 20107000.0


# === Nouvelles sources cinéma (publiées juin 2026, série annuelle 1985-2025) =

def test_cinema_langue_part_francophone_2025(raw_dir):
    """Langue de projection — part francophone 2025 ≈ 67 % (464 365 / 691 261).

    Source : ISQ, mise à jour 9 juin 2026 (résultats annuels 2025).
    Indicateur direct du marché francophone — central pour la Loi 109.
    """
    f = find_source_file(
        raw_dir,
        "Résultats d'exploitation des établissements*langue de projection*.xlsx"
    )
    assert f is not None, "Fichier langue de projection manquant"
    data = extract.extract_cinema_langue(f)
    assert data['annees'][0] == 1985
    assert data['annees'][-1] == 2025
    # Projections totales 2025
    projections = next(i for i in data['indicateurs'] if i['libelle'] == 'Projections')
    val_total = next(p['valeur'] for p in projections['serie'] if p['annee'] == 2025)
    assert val_total == 691261.0
    # Langue française 2025 (niveau 0, distinct des « Cinémas » au niveau 1)
    fr = next(i for i in data['indicateurs']
              if i['libelle'] == 'Langue française' and i['niveau'] == 0)
    val_fr = next(p['valeur'] for p in fr['serie'] if p['annee'] == 2025)
    assert val_fr == 464365.0
    # Part francophone des projections 2025 : ≈ 67,2 %
    assert 0.66 < val_fr / val_total < 0.68
    # Hiérarchie : Cinémas et Ciné-parcs présents comme sous-niveaux
    assert any(i['libelle'] == 'Cinémas' and i['niveau'] == 1
               for i in data['indicateurs'])
    assert any(i['libelle'] == 'Ciné-parcs' and i['niveau'] == 1
               for i in data['indicateurs'])


def test_cinema_classement_visa_general_2025(raw_dir):
    """Catégorie de classement — Visa général domine en 2025 (≈ 68 % du total).

    Source : ISQ, mise à jour 9 juin 2026.
    """
    f = find_source_file(
        raw_dir,
        "Résultats d'exploitation des établissements*catégorie de classement*.xlsx"
    )
    assert f is not None, "Fichier catégorie de classement manquant"
    data = extract.extract_cinema_classement(f)
    assert data['annees'][0] == 1985
    assert data['annees'][-1] == 2025
    visa = next(i for i in data['indicateurs']
                if i['libelle'] == 'Visa général' and i['niveau'] == 0)
    val_visa = next(p['valeur'] for p in visa['serie'] if p['annee'] == 2025)
    assert val_visa == 473627.0
    # Les quatre classes principales sont toutes présentes au niveau 0
    classes_niveau0 = [i['libelle'] for i in data['indicateurs'] if i['niveau'] == 0]
    for c in ('Visa général', '13 ans et plus', '16 ans et plus', '18 ans et plus'):
        assert c in classes_niveau0, f"Classe « {c} » manquante au niveau 0"


def test_cinema_pays_annuel_quebec_2025(raw_dir):
    """Pays d'origine annuel — assistance QC 2025 = 1 036 590 (≈ 9 % du total).

    Source : ISQ, mise à jour 9 juin 2026.

    À noter : la part annuelle (9,04 %) est nettement supérieure à la part
    YTD hebdomadaire courante (4,7 % au cumul YTD). L'écart vient en partie
    du fait que l'assistance QC se concentre certains mois — le YTD précoce
    sous-représente le poids annuel réel.
    """
    f = find_source_file(
        raw_dir,
        "Résultats d'exploitation des établissements*pays d'origine*annuelles*.xlsx"
    )
    assert f is not None, "Fichier pays d'origine annuel manquant"
    data = extract.extract_cinema_pays_annuel(f)
    assert data['annees'][0] == 1985
    assert data['annees'][-1] == 2025
    # Index par pays disponible et couvrant les pays attendus
    assert 'assistance_par_pays' in data
    assert {'États-Unis', 'France', 'Grande-Bretagne', 'Québec', 'Total'}.issubset(
        set(data['assistance_par_pays'].keys())
    )
    # Assistance QC 2025
    qc_serie = data['assistance_par_pays']['Québec']
    val_qc = next(p['valeur'] for p in qc_serie if p['annee'] == 2025)
    assert val_qc == 1036590.0
    # Assistance totale 2025
    total_serie = data['assistance_par_pays']['Total']
    val_total = next(p['valeur'] for p in total_serie if p['annee'] == 2025)
    assert val_total == 11470431.0
    # Part annuelle QC ≈ 9,04 %
    part_qc = val_qc / val_total
    assert 0.090 < part_qc < 0.091


def test_ventes_livres_numeriques_perimetre(raw_dir):
    """Source ISQ « Ventes de livres numériques, données annuelles, Québec »
    (tableau 3408). Série 2014-2025, 3 métriques.

    Méthodologie : Optique culture no 41. Inclut les ventes gratuites et
    les autoédités. Valeur exprimée au prix payé par le consommateur avant
    taxes.
    """
    f = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    assert f is not None, "Fichier livres numériques annuel manquant"
    data = extract.extract_ventes_livres_numeriques(f)
    # Périmètre temporel : 12 années 2014-2025
    assert data['annees'][0] == 2014
    assert data['annees'][-1] == 2025
    assert len(data['annees']) == 12
    # Trois séries
    assert set(data['series'].keys()) == {'exemplaires', 'valeur_ventes', 'prix_moyen'}
    # Métadonnées éditoriales
    assert '3408' in data['lien_permanent']
    assert data['mise_a_jour'] == '29 juin 2026'


def test_ventes_livres_numeriques_pic_2020(raw_dir):
    """Le pic d'exemplaires 2020 (confinement + livres gratuits)
    est le marqueur historique de cette série.

    En 2020 : 894 531 exemplaires (vs ~400 k en 2019), prix moyen
    qui chute à 11,74 $ (vs 15,48 $ en 2019).
    """
    f = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    data = extract.extract_ventes_livres_numeriques(f)
    idx_2020 = data['annees'].index(2020)
    idx_2019 = data['annees'].index(2019)
    # Pic d'exemplaires
    ex_2020 = data['series']['exemplaires']['valeurs'][idx_2020]
    ex_2019 = data['series']['exemplaires']['valeurs'][idx_2019]
    assert ex_2020 == 894531.0
    assert ex_2020 > 2 * ex_2019  # pic > x2 vs l'année précédente
    # Chute du prix moyen
    pm_2020 = data['series']['prix_moyen']['valeurs'][idx_2020]
    pm_2019 = data['series']['prix_moyen']['valeurs'][idx_2019]
    assert pm_2020 == 11.74
    assert pm_2020 < pm_2019


def test_ventes_livres_numeriques_palier_post_covid(raw_dir):
    """Lecture interprétative : la valeur des ventes reste sur un palier
    autour de 10 M$ après 2020, alors que le nombre d'exemplaires retombe.
    C'est le prix moyen qui porte la valeur (de 11,74 $ en 2020 à
    19,42 $ en 2025).
    """
    f = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    data = extract.extract_ventes_livres_numeriques(f)
    valeurs = data['series']['valeur_ventes']['valeurs']
    annees = data['annees']
    # Toutes les années 2020-2025 au-dessus de 9,5 M$
    for an in [2020, 2021, 2022, 2023, 2024, 2025]:
        v = valeurs[annees.index(an)]
        assert v > 9_500_000, f"Valeur {an} = {v}, attendue > 9,5 M$"
    # Prix moyen 2025
    pm_2025 = data['series']['prix_moyen']['valeurs'][annees.index(2025)]
    assert pm_2025 == 19.42
