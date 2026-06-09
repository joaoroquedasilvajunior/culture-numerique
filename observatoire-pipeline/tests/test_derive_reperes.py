"""
Tests d'intégrité du dériveur des cinq repères.

Mêmes conventions que test_extract.py : les valeurs attendues correspondent
aux derniers fichiers ISQ déposés dans Données Québec/. Si l'ISQ révise un
chiffre, ces tests échouent — c'est le signal voulu pour vérifier la
révision puis ajuster les attentes.

Pour R4 (matrice gelée), les attentes sont fixées par le protocole v1.1.0 ;
toute évolution de la matrice doit s'accompagner d'un bump de version et
d'une mise à jour explicite de ces attentes.
"""

from __future__ import annotations
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import yaml

from src import extract, derive
from src.pipeline import find_source_file, _resolve_raw_dir


@pytest.fixture
def raw_dir():
    """Lit le dossier configuré dans sources.yaml."""
    config = yaml.safe_load((REPO_ROOT / 'sources.yaml').read_text(encoding='utf-8'))
    return _resolve_raw_dir(REPO_ROOT, config)


@pytest.fixture
def combined(raw_dir):
    """Reconstitue le dict combiné comme le pipeline, sans réécrire les JSON."""
    f_part = find_source_file(raw_dir, 'Part des interprètes*.xlsx')
    f_vol = find_source_file(raw_dir, "Consommation d'enregistrements musicaux*.xlsx")
    f_pal = find_source_file(raw_dir, 'Palmarès des enregistrements*.xlsx')
    f_cin = find_source_file(
        raw_dir,
        "Résultats d'exploitation des établissements*pays d'origine*hebdomadaires*.xlsx"
    )
    return {
        'part_qc': extract.extract_part_qc(f_part),
        'volume_musique': extract.extract_volume_musique(f_vol),
        'palmares_top20': extract.extract_palmares(f_pal),
        'cinema_pays': extract.extract_cinema_pays(f_cin),
    }


# === R1 — Écart de découvrabilité ============================================

def test_r1_ratio_et_ecart(combined):
    """R1 — p_alb=24,5 % / p_str=6,9 % → R≈3,55 ; E=17,6 pts."""
    r1 = derive.derive_r1(combined['part_qc'])
    assert r1['part_streaming_pct'] == 6.9
    assert r1['part_albums_numeriques_pct'] == 24.5
    assert r1['ratio'] == 3.55
    assert r1['ecart_pts'] == 17.6
    assert r1['provisional'] is True
    assert r1['source'] == 'ISQ tableau 4153'


# === R2 — Profondeur du catalogue (N₂₀) ======================================

def test_r2_n20_cowboys_fringants(combined):
    """R2 — Un seul interprète québécois distinct dans le top 20."""
    r2 = derive.derive_r2(combined['palmares_top20'])
    assert r2['n20'] == 1
    assert r2['interpretes'] == ['Les Cowboys Fringants']
    assert r2['rangs_quebecois'] == [15]
    assert r2['provisional'] is True


# === R3 — Consommation québécoise absolue ===================================

def test_r3_streaming_consommation_absolue(combined):
    """R3 — C_streaming = 4 829 409,6 × 6,9 % ≈ 333 229,3 k écoutes."""
    r3 = derive.derive_r3(
        combined['volume_musique'], combined['part_qc'], combined['cinema_pays']
    )
    s = r3['canaux']['streaming_musique']
    assert s['volume_total_k_ecoutes'] == 4829409.6
    assert s['part_qc_pct'] == 6.9
    # 4 829 409,6 × 0,069 = 333 229,2624 → arrondi 1 décimale
    assert s['consommation_qc_k_ecoutes'] == pytest.approx(333229.3, abs=0.1)
    assert s['provisional'] is True


def test_r3_cinema_metadata_seulement(combined):
    """R3 cinéma — part QC livrée, mais C_film en attente des recettes annuelles."""
    r3 = derive.derive_r3(
        combined['volume_musique'], combined['part_qc'], combined['cinema_pays']
    )
    cinema = r3['canaux']['cinema']
    # ISQ a révisé la part QC entre le 22 mai et le 9 juin : 4,7 → 3,9 %
    # (même semaine de référence 24-30 avril 2026)
    assert cinema['part_qc_box_office_pct'] == 3.9
    assert cinema['status'] == 'donnees_annuelles_a_venir'
    assert cinema['consommation_absolue_recettes_qc'] is None


# === R4 — Indice d'angle mort ===============================================

def test_r4_matrice_8_sur_12():
    """R4 — matrice gelée 2026-05-25 : 8 cellules couvertes sur 12."""
    r4 = derive.derive_r4()
    assert r4['total'] == 12
    assert r4['cellules_couvertes'] == 8
    assert r4['a'] == round(8 / 12, 3)
    assert r4['provisional'] is False
    assert r4['version_protocole'] == '1.1.0'
    assert r4['date_gel'] == '2026-05-25'


def test_r4_cellules_absentes_explicites():
    """R4 — les 4 ✗ nommés par le protocole : Naturel (CP/DC), Social (CP/PT)."""
    r4 = derive.derive_r4()
    m = r4['matrice']
    assert m['naturel']['creation_production']['etat'] == 'absent'
    assert m['naturel']['diffusion_consommation']['etat'] == 'absent'
    assert m['social']['creation_production']['etat'] == 'absent'
    assert m['social']['preservation_transmission']['etat'] == 'absent'


def test_r4_cellule_pleine_unique():
    """R4 — une seule cellule ✓ : Économique × Diffusion-Consommation (Loi 109 art. 33)."""
    r4 = derive.derive_r4()
    pleins = [
        (cap, etape)
        for cap, etapes in r4['matrice'].items()
        for etape, info in etapes.items()
        if info['etat'] == 'plein'
    ]
    assert pleins == [('economique', 'diffusion_consommation')]


# === R5 — placeholder ========================================================

def test_r5_en_chantier():
    """R5 — placeholder explicite, status en_chantier."""
    r5 = derive.derive_r5()
    assert r5['status'] == 'en_chantier'
    assert r5['provisional'] is None


# === Orchestration ==========================================================

def test_derive_all_structure(combined):
    """derive_all — structure complète, version protocole portée."""
    result = derive.derive_all(combined, annee=2025)
    assert result['annee'] == 2025
    assert result['protocole_version'] == '1.1.0'
    assert set(result['reperes'].keys()) == {
        'r1_ecart_decouvrabilite',
        'r2_profondeur_catalogue',
        'r3_consommation_absolue',
        'r4_angle_mort',
        'r5_volume_oeuvres'
    }


def test_derive_all_tolerant_aux_sources_manquantes():
    """derive_all — si une source manque, le repère est marqué donnees_indisponibles."""
    result = derive.derive_all({}, annee=2025)
    assert result['reperes']['r1_ecart_decouvrabilite']['status'] == 'donnees_indisponibles'
    assert result['reperes']['r2_profondeur_catalogue']['status'] == 'donnees_indisponibles'
    assert result['reperes']['r3_consommation_absolue']['status'] == 'donnees_indisponibles'
    # R4 et R5 restent calculables, indépendants des sources extraites
    assert result['reperes']['r4_angle_mort']['cellules_couvertes'] == 8
    assert result['reperes']['r5_volume_oeuvres']['status'] == 'en_chantier'


# === Intégration dériveur → payload du dashboard ============================

def test_payload_for_dashboard_inclut_reperes(combined):
    """_payload_for_dashboard porte les repères sous la clé `reperes`.

    Vérifie que la section « Repères suivis » du dashboard reçoit bien les
    valeurs calculées, et qu'elle peut être consommée par le JS du template.
    """
    from src.pipeline import _payload_for_dashboard
    reperes = derive.derive_all(combined, annee=2025)
    payload = _payload_for_dashboard(combined, reperes=reperes)

    assert 'reperes' in payload
    assert payload['reperes']['protocole_version'] == '1.1.0'
    # R4 — la matrice gelée doit voyager intacte jusqu'au template
    r4 = payload['reperes']['reperes']['r4_angle_mort']
    assert r4['cellules_couvertes'] == 8
    assert r4['total'] == 12
    # R1 — les valeurs YTD doivent être disponibles
    r1 = payload['reperes']['reperes']['r1_ecart_decouvrabilite']
    assert r1['ratio'] == 3.55
    assert r1['provisional'] is True


def test_payload_for_dashboard_sans_reperes(combined):
    """Si reperes=None, le payload reste compatible avec l'ancien template."""
    from src.pipeline import _payload_for_dashboard
    payload = _payload_for_dashboard(combined)
    assert 'reperes' not in payload
    # Les clés existantes doivent rester intactes
    assert 'part_qc_musique' in payload
