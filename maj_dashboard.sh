#!/usr/bin/env bash
#
# maj_dashboard.sh — Mise à jour du tableau de bord du Carnet de données
# — souveraineté culturelle numérique.
#
# Enchaîne la routine de mise à jour :
#   1. Archivage horodaté des fichiers sources ISQ (.xlsx)
#   2. Build du pipeline           (python build.py)
#   3. Tests                       (pytest)
#   4. Copie du tableau de bord vers docs/  (pour GitHub Pages)
#   5. git add + git commit
#
# Le « git push » reste manuel, à faire après vérification :  git push
#
# Usage :
#   ./maj_dashboard.sh              routine complète (jusqu'au commit)
#   ./maj_dashboard.sh --no-commit  s'arrête après la copie vers docs/
#
# Prérequis : déposer au préalable les .xlsx ISQ à jour dans « Données Québec/ ».
# Les archives (Données Québec/_archives/) ne sont pas versionnées : elles
# servent de trace locale des versions successives des tableaux de l'ISQ.

set -uo pipefail

# --- Repérage des chemins (le script est à la racine du projet) -------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PIPELINE_DIR="$SCRIPT_DIR/observatoire-pipeline"
DOCS_DIR="$SCRIPT_DIR/docs"
OUT_DIR="$PIPELINE_DIR/outputs"
DATE="$(date +%F)"

# Dossier des sources ISQ — repli tolérant à la normalisation Unicode du nom.
RAW_DIR="$SCRIPT_DIR/Données Québec"
if [ ! -d "$RAW_DIR" ]; then
  alt="$(cd "$SCRIPT_DIR" 2>/dev/null && echo Donn*Qu*bec)"
  [ -d "$SCRIPT_DIR/$alt" ] && RAW_DIR="$SCRIPT_DIR/$alt"
fi
ARCHIVE_DIR="$RAW_DIR/_archives/$DATE"

# --- Options ----------------------------------------------------------------
DO_COMMIT=1
if [ "${1:-}" = "--no-commit" ]; then
  DO_COMMIT=0
elif [ -n "${1:-}" ]; then
  echo "Option inconnue : $1" >&2
  echo "Usage : ./maj_dashboard.sh [--no-commit]" >&2
  exit 2
fi

# --- Interpréteur Python ----------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERREUR : Python introuvable dans le PATH." >&2
  exit 1
fi

echo "=================================================================="
echo " Carnet de données — souveraineté culturelle numérique"
echo " Mise à jour du tableau de bord — $DATE"
echo "=================================================================="

# --- Étape 1/5 : archivage des sources ISQ ----------------------------------
echo
echo "[1/5] Archivage des sources ISQ"
if [ ! -d "$RAW_DIR" ]; then
  echo "  ERREUR : dossier des sources introuvable : $RAW_DIR" >&2
  exit 1
fi
mkdir -p "$ARCHIVE_DIR"
n_arch=0
while IFS= read -r -d '' f; do
  cp -p "$f" "$ARCHIVE_DIR/"
  n_arch=$((n_arch + 1))
done < <(find "$RAW_DIR" -maxdepth 1 -type f -name '*.xlsx' -print0)
if [ "$n_arch" -eq 0 ]; then
  echo "  AVERTISSEMENT : aucun fichier .xlsx trouvé dans $RAW_DIR" >&2
else
  echo "  $n_arch fichier(s) .xlsx archivé(s) dans Données Québec/_archives/$DATE/"
fi

# --- Étape 2/5 : build du pipeline ------------------------------------------
echo
echo "[2/5] Build du pipeline"
cd "$PIPELINE_DIR"
if ! "$PYTHON" build.py; then
  echo >&2
  echo "  ERREUR : le build a échoué. Mise à jour interrompue." >&2
  exit 1
fi

# --- Étape 3/5 : tests ------------------------------------------------------
echo
echo "[3/5] Tests (pytest)"
if ! "$PYTHON" -m pytest --version >/dev/null 2>&1; then
  echo "  ERREUR : pytest n'est pas installé." >&2
  echo "  Installe-le puis relance :  $PYTHON -m pip install pytest" >&2
  exit 1
fi
if ! "$PYTHON" -m pytest tests/ -q; then
  echo >&2
  echo "  ÉCHEC DES TESTS — interruption avant publication." >&2
  echo "  Un test qui échoue signale en général une révision d'un tableau ISQ." >&2
  echo "  Marche à suivre :" >&2
  echo "    1. Confirmer le nouveau chiffre dans le fichier .xlsx source ;" >&2
  echo "    2. mettre à jour la valeur attendue dans" >&2
  echo "       observatoire-pipeline/tests/test_extract.py ;" >&2
  echo "    3. relancer ./maj_dashboard.sh" >&2
  exit 1
fi

# --- Étape 4/5 : copie du tableau de bord vers docs/ ------------------------
echo
echo "[4/5] Copie du tableau de bord vers docs/"
cd "$SCRIPT_DIR"
if [ ! -f "$OUT_DIR/dashboard.html" ]; then
  echo "  ERREUR : tableau de bord introuvable : $OUT_DIR/dashboard.html" >&2
  exit 1
fi
mkdir -p "$DOCS_DIR"
cp "$OUT_DIR/dashboard.html" "$DOCS_DIR/index.html"
[ -f "$OUT_DIR/ledger.json" ]         && cp "$OUT_DIR/ledger.json"         "$DOCS_DIR/ledger.json"
[ -f "$OUT_DIR/ledger_history.jsonl" ] && cp "$OUT_DIR/ledger_history.jsonl" "$DOCS_DIR/ledger_history.jsonl"
[ -f "$OUT_DIR/reperes_2025.json" ]   && cp "$OUT_DIR/reperes_2025.json"   "$DOCS_DIR/reperes_2025.json"
echo "  docs/index.html mis à jour (+ journal d'audit + repères dérivés)."

# --- Étape 5/5 : commit git -------------------------------------------------
echo
if [ "$DO_COMMIT" -eq 0 ]; then
  echo "[5/5] Commit ignoré (--no-commit)."
  echo
  echo "Terminé. Vérifie docs/, puis versionne quand tu es prêt :"
  echo "  git add -A && git commit -m \"maj: tableau de bord — $DATE\" && git push"
  exit 0
fi

echo "[5/5] Commit git"
if ! command -v git >/dev/null 2>&1; then
  echo "  ERREUR : git introuvable dans le PATH." >&2
  exit 1
fi
git add -A
if git diff --cached --quiet; then
  echo "  Aucun changement à versionner — le tableau de bord est déjà à jour."
else
  git commit -m "maj: tableau de bord — $DATE"
  echo "  Commit créé."
fi

echo
echo "=================================================================="
echo " Terminé."
echo " Pour publier en ligne :  git push"
echo " GitHub Pages se régénère automatiquement après le push."
echo "=================================================================="
