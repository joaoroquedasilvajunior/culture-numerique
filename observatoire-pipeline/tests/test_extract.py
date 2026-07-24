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
    # Maj 22 juillet 2026 : pct 3,9 → 3,7 % ; var cumul -38,7 → -48,7 %.
    # La part QC du box-office continue de glisser ; le recul sur un an
    # se creuse. Signalé au chroniqueur (donnée d'actualité).
    assert qc['pct_cumul_ytd'] == 3.7
    assert qc['var_cumul_an_prec_pct'] == -48.7


def test_palmares_quebec_count(raw_dir):
    """Un seul interprète québécois dans le top 20 — Les Cowboys Fringants au rang 14.

    Trajectoire du rang : 15 (avril) → 17 (mai) → 14 (maj du 23 juillet 2026).
    La remontée peut refléter la saison estivale (festivals, Saint-Jean).
    La diversité reste à 1 dans tous les cas.
    """
    f = find_source_file(raw_dir, 'Palmarès des enregistrements*.xlsx')
    data = extract.extract_palmares(f)
    qc = [t for t in data if t['provenance'] == 'Québec']
    assert len(qc) == 1
    assert qc[0]['interprete'] == 'Les Cowboys Fringants'
    assert qc[0]['rang'] == 14


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
    # Maj 22 juillet 2026 : avril ajouté (3 → 4 mois disponibles)
    assert rec['mois_disponibles'] == 4
    assert rec['mois_dernier'] == 'Avril'
    # Variation Jan → Avril 2026 ≈ +4,0 % — la reprise 5121 se confirme
    assert rec['variation_pct'] is not None
    assert 3.0 < rec['variation_pct'] < 5.0


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


# === Dériveur croisé livre papier vs numérique ===

def test_livre_papier_vs_numerique_perimetre(raw_dir):
    """Vérifie que le dériveur produit une série 2014-2025 avec papier et
    numérique alignés, et la synthèse comparative.
    """
    from src import extract
    from src.derive import derive_livre_papier_vs_numerique
    fp_ev = find_source_file(raw_dir, "Évolution de statistiques clés*.xlsx")
    fp_num = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    assert fp_ev is not None and fp_num is not None
    ev = extract.extract_evolution(fp_ev)
    num = extract.extract_ventes_livres_numeriques(fp_num)
    out = derive_livre_papier_vs_numerique(ev, num)
    # Série
    assert 'serie' in out
    assert out['serie'][0]['annee'] == 2014
    assert out['serie'][-1]['annee'] == 2025
    assert len(out['serie']) == 12
    # Synthèse
    assert out['synthese']['periode_complete'] == '2014-2024'
    assert out['synthese']['lecture'] == 'addition'


def test_livre_papier_vs_numerique_pic_2020(raw_dir):
    """En 2020, le numérique bondit (+69,3 %) pendant que le papier
    décroche (-2,7 %). C'est le seul point de substitution observable
    dans la série, et il est conjoncturel (COVID).
    """
    from src import extract
    from src.derive import derive_livre_papier_vs_numerique
    fp_ev = find_source_file(raw_dir, "Évolution de statistiques clés*.xlsx")
    fp_num = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    ev = extract.extract_evolution(fp_ev)
    num = extract.extract_ventes_livres_numeriques(fp_num)
    out = derive_livre_papier_vs_numerique(ev, num)
    pt_2020 = next(s for s in out['serie'] if s['annee'] == 2020)
    assert pt_2020['var_papier_pct'] is not None and pt_2020['var_papier_pct'] < 0
    assert pt_2020['var_numerique_pct'] is not None and pt_2020['var_numerique_pct'] > 50


def test_livre_papier_vs_numerique_part_marginale(raw_dir):
    """La part du numérique dans le marché total reste sous 2 % en valeur
    sur toute la période. C'est la limite à signaler en interprétation :
    la part est sensible aux fluctuations relatives mais le numérique
    n'a pas fondamentalement déplacé le marché en $.
    """
    from src import extract
    from src.derive import derive_livre_papier_vs_numerique
    fp_ev = find_source_file(raw_dir, "Évolution de statistiques clés*.xlsx")
    fp_num = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    ev = extract.extract_evolution(fp_ev)
    num = extract.extract_ventes_livres_numeriques(fp_num)
    out = derive_livre_papier_vs_numerique(ev, num)
    parts = [s['part_numerique_pct'] for s in out['serie'] if s['part_numerique_pct'] is not None]
    assert max(parts) < 2.0  # jamais au-dessus de 2 %
    assert min(parts) > 0.5  # jamais sous 0,5 %


def test_livre_papier_vs_numerique_2025_papier_manquant(raw_dir):
    """L'ISQ n'a pas encore publié les ventes papier 2025 dans Évolution.
    Le dériveur doit gérer ce trou en mettant valeur_papier et part_numerique
    à None pour 2025, sans planter.
    """
    from src import extract
    from src.derive import derive_livre_papier_vs_numerique
    fp_ev = find_source_file(raw_dir, "Évolution de statistiques clés*.xlsx")
    fp_num = find_source_file(raw_dir, "Ventes de livres numériques*.xlsx")
    ev = extract.extract_evolution(fp_ev)
    num = extract.extract_ventes_livres_numeriques(fp_num)
    out = derive_livre_papier_vs_numerique(ev, num)
    pt_2025 = next(s for s in out['serie'] if s['annee'] == 2025)
    assert pt_2025['valeur_papier'] is None
    assert pt_2025['valeur_numerique'] is not None
    assert pt_2025['valeur_totale'] is None
    assert pt_2025['part_numerique_pct'] is None


# === Extracteurs CALQ (écosystème subventionné) ===

def test_calq_theatre_cirque_serie_longue(raw_dir):
    """CALQ théâtre/cirque : série longue 1994-1995 à 2023-2024 (30 ans).
    Le fichier global doit contenir le bloc Activités avec au minimum
    Nombre de productions, Représentations, Spectateurs (total + QC + hors-QC).
    """
    from src import extract
    f = find_source_file(
        raw_dir,
        "Statistiques principales des organismes de production en théâtre et arts du cirque soutenus par le Conseil des arts et des lettres du Québec, Québec.xlsx"
    )
    assert f is not None
    d = extract.extract_calq_theatre_cirque(f)
    # Période 30 ans
    assert d['annees'][0] == '1994-1995'
    assert d['annees'][-1] == '2023-2024'
    assert len(d['annees']) == 30
    # Discipline
    assert d['discipline'] == 'theatre_cirque'
    # Groupes présents : meta + revenus + depenses + activites
    groupes = {ind['groupe'] for ind in d['indicateurs']}
    assert {'meta', 'revenus', 'depenses', 'activites'}.issubset(groupes)
    # Nb organismes 2023-2024 : ordre de grandeur (60-90 orgs typique)
    nb_2324 = d['organismes_par_annee']['2023-2024']
    assert 60 <= nb_2324 <= 90
    # Activités attendues : au moins Représentations + Spectateurs
    libelles_act = {ind['libelle'] for ind in d['indicateurs'] if ind['groupe'] == 'activites'}
    assert 'Représentations' in libelles_act
    assert 'Spectateurs' in libelles_act


def test_calq_diffuseurs_pluridiscip_perimetre(raw_dir):
    """CALQ diffuseurs pluridisciplinaires : série 2016-2017 à 2023-2024.
    Ce sont des diffuseurs, donc pas de « Nombre de productions »,
    seulement Représentations + Spectateurs.
    """
    from src import extract
    f = find_source_file(
        raw_dir,
        "Statistiques principales des diffuseurs pluridisciplinaires soutenus par le Conseil des arts et des lettres du Québec, Québec.xlsx"
    )
    assert f is not None
    d = extract.extract_calq_diffuseurs_pluridiscip(f)
    assert d['annees'][0] == '2016-2017'
    assert d['annees'][-1] == '2023-2024'
    assert d['discipline'] == 'diffuseurs_pluridiscip'
    # Activités : Représentations + Spectateurs, mais pas de « Nombre de productions »
    libelles_act = {ind['libelle'] for ind in d['indicateurs'] if ind['groupe'] == 'activites'}
    assert 'Représentations' in libelles_act
    assert 'Spectateurs' in libelles_act
    assert 'Nombre de productions' not in libelles_act


def test_calq_arts_visuels_pas_dactivite_chiffree(raw_dir):
    """CALQ arts visuels : série 2017-2018 à 2023-2024. Ce tableau ne
    publie pas d'indicateurs d'activité en n dans le fichier global —
    le nombre d'organismes joue seul le rôle de proxy volume.
    Cette absence est structurelle et doit être respectée par
    l'extracteur (pas d'invention de zéros).
    """
    from src import extract
    f = find_source_file(
        raw_dir,
        "Statistiques principales des organismes de diffusion et de production en arts visuels, arts numériques, cinéma et vidéo soutenus à la mission par le Conseil des arts et des lettres du Québec, Québec.xlsx"
    )
    assert f is not None
    d = extract.extract_calq_arts_visuels(f)
    assert d['annees'][0] == '2017-2018'
    assert d['annees'][-1] == '2023-2024'
    assert d['discipline'] == 'arts_visuels_numeriques'
    # Aucun indicateur d'activité chiffré n'est attendu
    activites = [ind for ind in d['indicateurs'] if ind['groupe'] == 'activites']
    assert activites == []
    # Mais Nombre d'organismes doit être présent
    assert d['organismes_par_annee']['2023-2024'] is not None


def test_calq_theatre_cirque_croissance_30_ans(raw_dir):
    """Test de bon sens sur la trajectoire longue : les revenus totaux du
    secteur théâtre/cirque soutenu doivent avoir crû nominalement entre
    1994-1995 et 2023-2024. Le test est délibérément lâche (juste > x2)
    pour éviter d'échouer sur des révisions ISQ mineures.
    """
    from src import extract
    f = find_source_file(
        raw_dir,
        "Statistiques principales des organismes de production en théâtre et arts du cirque soutenus par le Conseil des arts et des lettres du Québec, Québec.xlsx"
    )
    d = extract.extract_calq_theatre_cirque(f)
    revenus_totaux = next(
        ind for ind in d['indicateurs'] if ind['libelle'] == 'Revenus totaux'
    )
    v_debut = revenus_totaux['valeurs'][0]     # 1994-1995
    v_fin = revenus_totaux['valeurs'][-1]      # 2023-2024
    assert v_debut is not None and v_fin is not None
    # Croissance nominale sur 30 ans : le secteur passe de ~35 M$ à ~120 M$
    # (x3.4 avant inflation). Test lâche : au moins x2.
    assert v_fin > 2 * v_debut


# === MusicBrainz — présence catalogue des artistes QC ===

def test_musicbrainz_artistes_qc_perimetre(raw_dir):
    """Récolte MusicBrainz du 2026-07-18 : 9 731 artistes uniques rattachés
    aux 9 zones québécoises. Première source non gouvernementale du pipeline
    (licence CC0).
    """
    from src import extract
    f = find_source_file(raw_dir, "musicbrainz_artistes_qc_*.json")
    assert f is not None, "Fichier musicbrainz_artistes_qc manquant"
    d = extract.extract_musicbrainz_artistes_qc(f)
    assert d['nb_artistes'] == 9731
    assert d['date_recolte'] == '2026-07-18'
    # 9 zones attendues
    assert len(d['zones']) == 9
    assert 'Montréal' in d['zones']
    assert 'Québec (province)' in d['zones']
    # Montréal est la zone la plus peuplée en libellé affiné
    assert d['zones']['Montréal']['artistes'] > 4000


def test_musicbrainz_artistes_qc_taux_plancher(raw_dir):
    """Les taux de couverture streaming sont des planchers de complétude
    des métadonnées ouvertes. Récolte 2026-07-18 : Spotify ~20 %,
    streaming élargi ~40 %, actifs ~87 %.
    """
    from src import extract
    f = find_source_file(raw_dir, "musicbrainz_artistes_qc_*.json")
    d = extract.extract_musicbrainz_artistes_qc(f)
    assert 15 <= d['taux_spotify_pct'] <= 30
    assert 30 <= d['taux_streaming_pct'] <= 50
    assert d['taux_actifs_pct'] > 80
    # Cohérence interne
    assert d['nb_avec_spotify'] <= d['nb_avec_streaming'] <= d['nb_artistes']


def test_musicbrainz_artistes_qc_agregats(raw_dir):
    """Agrégats calculés : types, top genres, échantillon documenté.
    Le hip hop est le premier genre du catalogue QC (récolte 2026-07-18).
    """
    from src import extract
    f = find_source_file(raw_dir, "musicbrainz_artistes_qc_*.json")
    d = extract.extract_musicbrainz_artistes_qc(f)
    # Types : Person + Group dominent
    assert d['types'].get('Person', 0) > 5000
    assert d['types'].get('Group', 0) > 3000
    # Top genres : le premier est hip hop
    assert d['top_genres'][0][0] == 'hip hop'
    # Échantillon de 30 artistes documentés
    assert len(d['echantillon_documentes']) == 30
    # L'échantillon est trié par documentation décroissante
    assert d['echantillon_documentes'][0]['nb_liens'] >= d['echantillon_documentes'][-1]['nb_liens']


# === Deezer — popularité des artistes QC ===

def test_deezer_artistes_qc_perimetre(raw_dir):
    """Extraction Deezer 2026-07-19 : 1 203 artistes enrichis sur les
    9 731 du catalogue MusicBrainz (périmètre = liens Deezer documentés).
    """
    from src import extract
    f = find_source_file(raw_dir, "deezer_artistes_qc_*.json")
    assert f is not None, "Fichier deezer_artistes_qc manquant"
    d = extract.extract_deezer_artistes_qc(f)
    assert d['nb_artistes'] == 1203
    assert d['date_extraction'] == '2026-07-19'
    # Distribution en 5 paliers dont les parts somment à ~100
    assert len(d['distribution_longue_traine']) == 5
    total_pct = sum(p['part_pct'] for p in d['distribution_longue_traine'])
    assert 99.0 <= total_pct <= 101.0


def test_deezer_artistes_qc_tete_et_traine(raw_dir):
    """Céline Dion est en tête (~3,6 M fans) ; la distribution est une
    longue traîne fortement concentrée (le top 1 % capte une part
    majoritaire des fans).
    """
    from src import extract
    f = find_source_file(raw_dir, "deezer_artistes_qc_*.json")
    d = extract.extract_deezer_artistes_qc(f)
    assert d['top_20'][0]['nom'] == 'Céline Dion'
    assert d['top_20'][0]['nb_fan'] > 3_000_000
    # Concentration : top 1 % > 40 % des fans
    assert d['part_fans_top_1pct_pct'] > 40
    # Médiane très basse (longue traîne)
    assert d['mediane_fans'] < 1000


# === Palmarès évolutif des films ===

def test_palmares_films_perimetre(raw_dir):
    """Top 20 cumulatif annuel des films par assistance, ensemble du Québec.
    Structure : 20 entrées avec rang, titre, année, pays, assistance.
    """
    from src import extract
    f = find_source_file(raw_dir, "Palmarès évolutif des films*.xlsx")
    assert f is not None, "Fichier palmarès films manquant"
    d = extract.extract_palmares_films(f)
    assert len(d['entrees']) == 20
    assert d['entrees'][0]['rang'] == 1
    assert d['entrees'][-1]['rang'] == 20
    # Le rang 1 a la plus forte assistance
    assert d['entrees'][0]['assistance_cumul'] == max(
        e['assistance_cumul'] for e in d['entrees'])
    assert 'Cumulatif' in d['periode']


def test_palmares_films_absence_quebec(raw_dir):
    """Constat structurant à l'intégration (juillet 2026) : aucun film
    québécois dans le top 20 d'assistance. Le pendant cinéma du R2
    musical (1 seul interprète QC au top 20 musique).

    Si ce test casse un jour parce qu'un film QC entre au top 20,
    c'est une bonne nouvelle : mettre à jour le test ET le signaler
    comme fait d'actualité au chroniqueur.
    """
    from src import extract
    f = find_source_file(raw_dir, "Palmarès évolutif des films*.xlsx")
    d = extract.extract_palmares_films(f)
    assert d['n_quebec'] == 0
    assert d['films_quebec'] == []
    # Domination américaine
    assert d['repartition_pays'].get('États-Unis', 0) >= 15


# === AEI Cadences (juin 2026) — lentille 2 au niveau Québec ===

def test_aei_cadences_perimetre(raw_dir):
    """Release Cadences : CA-QC + CAN, deux mois (avril-mai 2026),
    Brésil exclu par décision éditoriale.
    """
    from src import extract
    f = find_source_file(raw_dir, "aei_claude_ai_2026-*.csv")
    assert f is not None, "Fichier AEI Cadences manquant"
    d = extract.extract_aei_cadences(f)
    assert d['geos'] == ['CA-QC', 'CAN']
    assert d['periodes'] == ['2026-04-01', '2026-05-01']
    assert d['periode_reference'] == '2026-05-01'
    # Les deux géos ont des métriques overall pour le mois de référence
    assert 'usage_pct' in d['overall']['CA-QC']['2026-05-01']
    assert 'usage_pct' in d['overall']['CAN']['2026-05-01']


def test_aei_cadences_quebec_mai_2026(raw_dir):
    """Valeurs-clés CA-QC de mai 2026 : partage automation/augmentation
    46,97/53,03 ; le Québec pèse 20,81 % de l'usage canadien de Claude.ai.
    """
    from src import extract
    f = find_source_file(raw_dir, "aei_claude_ai_2026-*.csv")
    d = extract.extract_aei_cadences(f)
    qc_mai = d['overall']['CA-QC']['2026-05-01']
    assert qc_mai['collaboration_bucket_automation_pct'] == 46.97
    assert qc_mai['collaboration_bucket_augmentation_pct'] == 53.03
    assert qc_mai['usage_pct'] == 20.81
    # Somme automation + augmentation = 100
    assert abs(qc_mai['collaboration_bucket_automation_pct']
               + qc_mai['collaboration_bucket_augmentation_pct'] - 100) < 0.1


def test_aei_cadences_soc_arts_2e_groupe(raw_dir):
    """Constat d'intégration : les occupations Arts, Design, Entertainment,
    Sports, and Media sont le 2e groupe SOC d'usage de Claude au Québec
    (13,18 % en mai 2026), derrière Computer and Mathematical.
    La lentille 2 devient directement culturelle.
    """
    from src import extract
    f = find_source_file(raw_dir, "aei_claude_ai_2026-*.csv")
    d = extract.extract_aei_cadences(f)
    soc = d['soc_top_dernier_mois']
    assert soc[0]['groupe'] == 'Computer and Mathematical'
    assert soc[1]['groupe'] == 'Arts, Design, Entertainment, Sports, and Media'
    assert soc[1]['creatif'] is True
    assert soc[1]['pct_qc'] == 13.18
    # Comparaison CAN disponible pour le groupe créatif
    assert soc[1]['pct_can'] is not None


# === Top 100 Apple Music Canada ===

def test_apple_top100_perimetre(raw_dir):
    """Flux marketing public Apple, storefront Canada, 100 entrées,
    artistes QC marqués par croisement MusicBrainz.
    """
    from src import extract
    f = find_source_file(raw_dir, "apple_top100_ca_*.json")
    assert f is not None, "Fichier apple_top100_ca manquant"
    d = extract.extract_apple_top100(f)
    assert d['n_entrees'] == 100
    assert len(d['top_10']) == 10
    assert d['top_10'][0]['rang'] == 1


def test_apple_top100_zero_quebec(raw_dir):
    """Constat d'intégration (récolte 2026-07-23) : AUCUN artiste québécois
    dans le top 100 des chansons les plus écoutées sur Apple Music Canada.
    Zéro vérifié : matcher validé sur noms connus (Cowboys Fringants,
    Céline Dion, Cœur de pirate) + inspection visuelle des 48 artistes
    uniques du palmarès.

    Le motif R2 tient maintenant sur trois lectures : 1/20 au palmarès
    musical ISQ (toutes plateformes), 0/20 au palmarès films, 0/100 sur
    Apple Music Canada. Si ce test casse parce qu'un artiste QC entre au
    top 100 : bonne nouvelle, mettre à jour et signaler au chroniqueur.
    """
    from src import extract
    f = find_source_file(raw_dir, "apple_top100_ca_*.json")
    d = extract.extract_apple_top100(f)
    assert d['n_quebec'] == 0
    assert d['entrees_quebec'] == []


# === Part QC top 200 ventes (série terminée 2021) ===

def test_part_top200_ventes_perimetre(raw_dir):
    """Tableau ISQ 2142 — série terminée (dernière maj 24 févr. 2022).
    Capsule de l'ère des ventes : 4 dimensions définitionnelles,
    dernière semaine du 24-30 décembre 2021.
    """
    from src import extract
    f = find_source_file(raw_dir, "Part des enregistrements audio québécois*.xlsx")
    assert f is not None, "Fichier part top 200 ventes manquant"
    d = extract.extract_part_top200_ventes(f)
    assert d['statut_serie'] == 'terminee'
    assert d['annee'] == '2021'
    assert '24 au 30 décembre 2021' in d['derniere_semaine']
    assert len(d['dimensions']) == 4
    assert 'Dimension artistique' in d['dimensions']


def test_part_top200_ventes_bascule_ere(raw_dir):
    """Le contraste central : en cumulatif 2021, 58,9 % des ventes du
    top 200 étaient québécoises (dimension artistique, ensemble albums) ;
    en 2026, la part QC du streaming est de 6,9 % (tableau 4153).
    Métriques non comparables terme à terme (ventes vs flux, top 200 vs
    total) mais l'ordre de grandeur de la bascule d'ère est le constat.
    """
    from src import extract
    f = find_source_file(raw_dir, "Part des enregistrements audio québécois*.xlsx")
    d = extract.extract_part_top200_ventes(f)
    s = d['synthese_2021']
    assert s['part_qc_albums_dimension_artistique_pct'] == 58.9
    assert s['part_qc_albums_numeriques_dimension_artistique_pct'] == 55.4
    assert s['part_qc_pistes_dimension_artistique_pct'] == 18.4
