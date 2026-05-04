"""
Journal d'audit (« ledger ») : trace chaque exécution du pipeline.

Pour chaque source utilisée, on consigne :
- chemin et nom de fichier
- empreinte SHA-256 (preuve d'intégrité)
- taille en octets
- date de modification du fichier (mtime)
- date de l'exécution

Le ledger est écrit dans outputs/ledger.json après chaque build, et historisé dans
outputs/ledger_history.jsonl (une ligne par build, append-only) pour permettre
de reconstituer l'historique des chiffres publiés.
"""

from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def file_fingerprint(path: Path) -> dict:
    """Calcule l'empreinte intégrale d'un fichier source."""
    p = Path(path)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    stat = p.stat()
    return {
        'path': str(p),
        'name': p.name,
        'sha256': h.hexdigest(),
        'size_bytes': stat.st_size,
        'mtime_iso': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def build_record(sources_used: list[dict], outputs_produced: list[str],
                 errors: list[dict] | None = None) -> dict:
    """Compose un enregistrement de build complet."""
    return {
        'build_iso': datetime.now(tz=timezone.utc).isoformat(),
        'pipeline_version': '1.0.0',
        'sources_used': sources_used,
        'outputs_produced': outputs_produced,
        'errors': errors or [],
    }


def write_ledger(record: dict, outputs_dir: Path) -> Path:
    """Écrit le ledger courant et l'append à l'historique."""
    outputs_dir = Path(outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    current = outputs_dir / 'ledger.json'
    history = outputs_dir / 'ledger_history.jsonl'

    with current.open('w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    with history.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

    return current
