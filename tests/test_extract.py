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

from src import extract
from src.pipeline import find_source_file


@pytest.fixture
def raw_dir():
    return REPO_ROOT / 'data' / 'raw'


def test_part_qc_streaming(raw_dir):
    """Part QC streaming YTD février 2026 = 6,8 %."""
    f = find_source_file(raw_dir, 'Part des interprètes*.xlsx')
    assert f is not None, "Fichier Part des interprètes manquant dans data/raw/"
    data = extract.extract_part_qc(f)
    assert data['indicateurs']['streaming']['cumul_ytd_pct'] == 6.8


def test_part_qc_albums_numeriques(raw_dir):
    """Part QC albums numériques YTD = 19,6 % (plus haute des canaux numériques)."""
    f = find_source_file(raw_dir, 'Part des interprètes*.xlsx')
    data = extract.extract_part_qc(f)
    assert data['indicateurs']['albums_numeriques']['cumul_ytd_pct'] == 19.6


def test_volume_streaming(raw_dir):
    """Streaming cumulatif YTD = 4 829 409,6 milliers d'écoutes."""
    f = find_source_file(raw_dir, "Consommation d'enregistrements musicaux*.xlsx")
    data = extract.extract_volume_musique(f)
    assert data['indicateurs']['streaming']['cumul_ytd'] == 4829409.6


def test_cinema_quebec(raw_dir):
    """Part QC box-office YTD = 4,7 %, var an−1 = −12,4 %."""
    f = find_source_file(raw_dir,
                         "Résultats d'exploitation des établissements*pays d'origine*.xlsx")
    assert f is not None, "Fichier cinéma pays d'origine manquant"
    data = extract.extract_cinema_pays(f)
    qc = next(p for p in data['pays'] if p['pays'] == 'Québec')
    assert qc['pct_cumul_ytd'] == 4.7
    assert qc['var_cumul_an_prec_pct'] == -12.4


def test_palmares_quebec_count(raw_dir):
    """Un seul interprète québécois dans le top 20."""
    f = find_source_file(raw_dir, 'Palmarès des enregistrements*.xlsx')
    data = extract.extract_palmares(f)
    qc = [t for t in data if t['provenance'] == 'Québec']
    assert len(qc) == 1
    assert qc[0]['interprete'] == 'Les Cowboys Fringants'
    assert qc[0]['rang'] == 15


def test_evolution_streaming_2024(raw_dir):
    """Écoutes streaming 2024 = 31 004 652,5 (k)."""
    f = find_source_file(raw_dir, 'Évolution de statistiques clés*.xlsx')
    data = extract.extract_evolution(f)
    serie = data['indicateurs']['musique_streaming']['serie']
    val_2024 = next(p['valeur'] for p in serie if p['annee'] == 2024)
    assert val_2024 == 31004652.5


def test_emplois_5121_decline(raw_dir):
    """Emplois film et vidéo (5121) : variation 2025 ≈ −11,6 %."""
    f = find_source_file(raw_dir, 'Emplois salariés*.xlsx')
    data = extract.extract_emplois_eerh(f)
    rec = next(r for r in data if r['scian'] == '5121')
    assert rec['variation_pct'] is not None
    assert -12.0 < rec['variation_pct'] < -11.0


def test_emplois_5162_growth(raw_dir):
    """Distribution de contenu en continu (5162) : variation 2025 > +30 %."""
    f = find_source_file(raw_dir, 'Emplois salariés*.xlsx')
    data = extract.extract_emplois_eerh(f)
    rec = next(r for r in data if r['scian'] == '5162')
    assert rec['variation_pct'] > 30.0
