#!/usr/bin/env python3
"""
Point d'entrée du pipeline de l'Observatoire de la souveraineté culturelle numérique.

Usage :
    python build.py                # build complet, verbeux
    python build.py --quiet        # silencieux

Le script présume que les fichiers ISQ téléchargés sont déposés dans data/raw/.
Voir data/raw/README.md pour la convention de dépôt.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Permet d'exécuter `python build.py` depuis la racine du dépôt sans installation
sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline import run  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quiet', '-q', action='store_true', help='Réduit la sortie')
    args = parser.parse_args()

    print('Observatoire de la souveraineté culturelle numérique — Pipeline\n')
    record = run(repo_root=Path(__file__).parent, verbose=not args.quiet)
    if record['errors']:
        sys.exit(1)
    print('\nBuild terminé avec succès.')


if __name__ == '__main__':
    main()
