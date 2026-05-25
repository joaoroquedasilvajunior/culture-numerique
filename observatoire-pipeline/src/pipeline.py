"""
Orchestrateur du pipeline.

Étapes :
1. Charger sources.yaml
2. Pour chaque source : trouver le fichier le plus récent dans data/raw/ qui matche
   le motif, puis appeler l'extracteur déclaré
3. Écrire un JSON par source dans data/processed/
4. Combiner tous les JSON en un dataset unique data/processed/dashboard_data.json
5. Rendre le tableau de bord HTML dans outputs/dashboard.html
6. Écrire le ledger dans outputs/ledger.json (et append à ledger_history.jsonl)
"""

from __future__ import annotations
import fnmatch
import json
import unicodedata
from pathlib import Path
import yaml

from . import extract
from .ledger import file_fingerprint, build_record, write_ledger
from .render import render_dashboard


class PipelineError(Exception):
    pass


def _nfc(s: str) -> str:
    """Normalise une chaîne en NFC (composée) pour comparaison robuste cross-OS.
    macOS stocke souvent les noms de fichiers en NFD (décomposé), alors que les
    motifs écrits dans sources.yaml sont en NFC. La normalisation des deux côtés
    règle le problème de matching."""
    return unicodedata.normalize('NFC', s)


def find_source_file(raw_dir: Path, pattern: str) -> Path | None:
    """Retourne le fichier le plus récent qui matche le motif glob, en tenant
    compte de la normalisation Unicode NFC/NFD."""
    pattern_nfc = _nfc(pattern)
    candidates = []
    for p in raw_dir.iterdir():
        if not p.is_file():
            continue
        if fnmatch.fnmatchcase(_nfc(p.name), pattern_nfc):
            candidates.append(p)
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _resolve_raw_dir(repo_root: Path, config: dict) -> Path:
    """Résout le dossier des données brutes selon la config.
    - Si `raw_data_dir` est défini dans sources.yaml et est un chemin absolu, on le prend tel quel.
    - Sinon (relatif), on le résout par rapport à la racine du dépôt.
    - Sinon (absent), fallback sur data/raw/.
    """
    raw = config.get('raw_data_dir', 'data/raw')
    p = Path(raw)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    return p


def run(repo_root: Path | str = '.', verbose: bool = True) -> dict:
    """Exécute le pipeline complet et retourne le record du build."""
    repo_root = Path(repo_root).resolve()
    config = yaml.safe_load((repo_root / 'sources.yaml').read_text(encoding='utf-8'))
    raw_dir = _resolve_raw_dir(repo_root, config)
    processed_dir = repo_root / 'data' / 'processed'
    outputs_dir = repo_root / 'outputs'
    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        raise PipelineError(
            f"Le dossier des données brutes est introuvable : {raw_dir}\n"
            f"Vérifier `raw_data_dir` dans sources.yaml.")
    if verbose:
        print(f"  Source des données brutes : {raw_dir}\n")

    sources_used = []
    errors = []
    combined: dict = {}

    for source_key, meta in config['sources'].items():
        pattern = meta['file_pattern']
        extractor_name = meta['extractor']
        extractor_fn = extract.EXTRACTORS.get(extractor_name)
        if not extractor_fn:
            errors.append({'source': source_key, 'error': f"Extracteur inconnu : {extractor_name}"})
            continue

        src_file = find_source_file(raw_dir, pattern)
        if src_file is None:
            errors.append({'source': source_key,
                           'error': f"Fichier introuvable pour le motif `{pattern}` dans data/raw/"})
            if verbose:
                print(f"  [!] {source_key:20s} : MANQUANT  ({pattern})")
            continue

        if verbose:
            print(f"  [+] {source_key:20s} : {src_file.name}")

        try:
            data = extractor_fn(src_file)
        except Exception as e:
            errors.append({'source': source_key, 'error': str(e)})
            if verbose:
                print(f"      ERREUR : {e}")
            continue

        # Persist per-source JSON
        per_source = {
            'source_key': source_key,
            'label': meta['label'],
            'isq_url': meta.get('isq_url'),
            'classification': meta.get('classification'),
            'axe_tdb': meta.get('axe_tdb', []),
            'data': data,
        }
        out_path = processed_dir / f"{source_key}.json"
        out_path.write_text(json.dumps(per_source, ensure_ascii=False, indent=2),
                            encoding='utf-8')

        # Add to combined dashboard payload
        combined[source_key] = data

        # Record in ledger
        sources_used.append({**file_fingerprint(src_file),
                             'source_key': source_key,
                             'label': meta['label']})

    # Write combined dashboard data
    combined_path = processed_dir / 'dashboard_data.json'
    combined_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2),
                             encoding='utf-8')

    # Render dashboard HTML
    dashboard_cfg = config.get('dashboard', {})
    template = repo_root / dashboard_cfg.get('template', 'templates/dashboard.html.tmpl')
    output_html = repo_root / dashboard_cfg.get('output', 'outputs/dashboard.html')

    rendered = None
    if template.exists():
        rendered = render_dashboard(_payload_for_dashboard(combined),
                                    template, output_html)
        if verbose:
            print(f"  [✓] dashboard rendu : {output_html.relative_to(repo_root)}")
    else:
        errors.append({'source': '__template__',
                       'error': f"Template manquant : {template.relative_to(repo_root)}"})

    outputs_produced = [str(combined_path.relative_to(repo_root))]
    if rendered:
        outputs_produced.append(str(rendered.relative_to(repo_root)))

    record = build_record(sources_used, outputs_produced, errors)
    write_ledger(record, outputs_dir)

    if verbose:
        print(f"\n  Sources OK  : {len(sources_used)}")
        print(f"  Erreurs     : {len(errors)}")
        if errors:
            for e in errors:
                print(f"    · {e.get('source','?')} → {e.get('error','?')}")

    return record


def _payload_for_dashboard(combined: dict) -> dict:
    """Adapte les clés au format attendu par le template HTML.
    Les clés JS du template sont historiquement : part_qc_musique, volume_musique,
    cinema_pays_origine, palmares_top20, historique_2002_2024, emplois_2025.
    """
    mapping = {
        'part_qc': 'part_qc_musique',
        'volume_musique': 'volume_musique',
        'cinema_pays': 'cinema_pays_origine',
        'palmares_top20': 'palmares_top20',
        'evolution_stats': 'historique_2002_2024',
        'emplois_eerh': 'emplois_2025',
    }
    payload = {}
    for k, v in combined.items():
        target = mapping.get(k, k)
        payload[target] = v
    return payload
