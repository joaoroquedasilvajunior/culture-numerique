"""
Fonctions d'extraction des tableaux ISQ vers des structures Python normalisées.

Conventions
-----------
Chaque extracteur prend un chemin de fichier .xlsx et retourne un dict.
Les valeurs textuelles spéciales de l'ISQ sont systématiquement traduites :
    '..'   -> None  (donnée non disponible)
    '...'  -> None  (sans objet — typiquement séries terminées)
    '--'   -> 0.0   (donnée infime, pour les TCM)
    '-'    -> 0.0   (néant ou zéro)
    'F'    -> None  (donnée peu fiable, ne peut être diffusée)

Les libellés contiennent souvent des espaces insécables \\xa0 (hiérarchie SCIAN)
et des préfixes en points (ex. '..Albums physiques'). On normalise en supprimant
ces marqueurs après en avoir extrait le niveau hiérarchique.
"""

from __future__ import annotations
import re
from pathlib import Path
from openpyxl import load_workbook


# ---------- Helpers ----------

def _clean_label(s):
    if s is None:
        return ''
    s = str(s).replace('\xa0', '').replace('\n', ' ').strip()
    s = re.sub(r'^\.+\s*', '', s)  # remove leading sub-level markers
    return s


def _to_num(x):
    if x is None:
        return None
    if isinstance(x, str):
        s = x.strip()
        if s in ('', '..', '...', 'F'):
            return None
        if s in ('--', '-'):
            return 0.0
        try:
            return float(s.replace(',', '.'))
        except (ValueError, TypeError):
            return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _hierarchy_level(s):
    """Return indentation level inferred from leading non-breaking spaces or dots."""
    if s is None:
        return 0
    raw = str(s)
    # 6 \xa0 per level (ISQ convention)
    nbsp = len(raw) - len(raw.lstrip('\xa0'))
    if nbsp > 0:
        return nbsp // 6
    # ".." per level (some files use this convention instead)
    dots = len(raw) - len(raw.lstrip('.'))
    return dots // 2


def _is_terminated(s):
    return '(Terminé)' in str(s or '')


# ---------- Extractors ----------

def extract_part_qc(path: Path) -> dict:
    """
    Tableau « Part des interprètes du Québec dans la consommation d'enregistrements musicaux »
    Layout : col A = libellé, col B = % cette semaine, col D = % cumulatif YTD.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    periode = ws.cell(row=4, column=1).value or ''

    cibles = {
        'streaming': "Écoutes sur les services de diffusion de musique en continu",
        'albums_total': 'Ensemble des albums',
        'albums_physiques': 'Albums sur support physique',
        'albums_numeriques': 'Albums en fichier numérique',
        'pistes_numeriques': 'Pistes en fichier numérique',
    }
    indicateurs = {}
    for row in ws.iter_rows(min_row=8, max_row=20, values_only=True):
        label = _clean_label(row[0])
        for k, target in cibles.items():
            if label.startswith(target):
                indicateurs[k] = {
                    'libelle': target,
                    'semaine_pct': _to_num(row[1]),
                    'cumul_ytd_pct': _to_num(row[3]),
                }
    return {'periode': str(periode).strip(), 'indicateurs': indicateurs}


def extract_volume_musique(path: Path) -> dict:
    """
    Tableau « Consommation d'enregistrements musicaux selon le type de produit »
    Layout : A=libellé, B=cette sem (k), D=var sem-1 (%), F=var an-1 sem (%),
             H=cumul YTD (k), J=var cumul an-1 (%).
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    periode = ws.cell(row=4, column=1).value or ''

    cibles = {
        'streaming': "Écoutes sur les services de diffusion de musique en continu",
        'albums_total': 'Ensemble des albums',
        'albums_physiques': 'Albums sur support physique',
        'cd': 'Disques compacts',
        'vinyle': 'Disques vinyle',
        'albums_numeriques': 'Albums en fichier numérique',
        'pistes_numeriques': 'Pistes en fichier numérique',
    }
    indicateurs = {}
    for row in ws.iter_rows(min_row=8, max_row=22, values_only=True):
        label = _clean_label(row[0])
        for k, target in cibles.items():
            if label.startswith(target):
                indicateurs[k] = {
                    'libelle': target,
                    'semaine': _to_num(row[1]),
                    'var_sem_prec_pct': _to_num(row[3]),
                    'var_an_prec_sem_pct': _to_num(row[5]),
                    'cumul_ytd': _to_num(row[7]),
                    'var_cumul_an_prec_pct': _to_num(row[9]),
                }
    return {'periode': str(periode).strip(), 'indicateurs': indicateurs}


def extract_cinema_pays(path: Path) -> dict:
    """
    Tableau « Résultats d'exploitation cinéma selon pays d'origine »
    Layout : A=pays, B=assistance sem (n), D=% sem, F=var sem-1 %, H=var an-1 sem %,
             J=cumul YTD (n), L=% cumul, N=var cumul an-1 %.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    periode = ws.cell(row=4, column=1).value or ''

    pays_cibles = ['États-Unis', 'France', 'Grande-Bretagne', 'Québec',
                   'Canada', 'Autres pays', 'Total']
    pays_data = []
    for row in ws.iter_rows(min_row=10, max_row=22, values_only=True):
        label = _clean_label(row[0])
        if label in pays_cibles:
            pays_data.append({
                'pays': label,
                'assistance_semaine': _to_num(row[1]),
                'pct_semaine': _to_num(row[3]),
                'var_sem_prec_pct': _to_num(row[5]),
                'var_an_prec_sem_pct': _to_num(row[7]),
                'assistance_cumul_ytd': _to_num(row[9]),
                'pct_cumul_ytd': _to_num(row[11]),
                'var_cumul_an_prec_pct': _to_num(row[13]),
            })
    return {'periode': str(periode).strip(), 'pays': pays_data}


def extract_palmares(path: Path) -> list[dict]:
    """
    Tableau « Palmarès des enregistrements musicaux »
    Layout : A=rang (entier), B=interprète, C=provenance.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    top = []
    for row in ws.iter_rows(values_only=True):
        if row[0] is None:
            continue
        try:
            rang = int(row[0])
        except (TypeError, ValueError):
            continue
        top.append({
            'rang': rang,
            'interprete': str(row[1]).strip() if row[1] else '',
            'provenance': str(row[2]).strip() if row[2] else '',
        })
    return top


def extract_evolution(path: Path) -> dict:
    """
    Tableau « Évolution de statistiques clés de la culture et des communications »
    Layout : A=domaine (header rows), B=indicateur, C=unité, puis pairs (year, blank).
    Header année en row 4 sous la forme '2020(ou 2020-2021)'.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']

    # Find year columns from row 4
    annees = []
    year_cols = []
    for c in ws[4]:
        v = c.value
        if v and 'ou' in str(v):
            try:
                yr = int(str(v).split('(')[0].strip())
                annees.append(yr)
                year_cols.append(c.column)
            except (ValueError, IndexError):
                pass

    # Whitelist of indicators to extract (clé -> début du libellé)
    cibles = {
        "scene_representations": "Représentations payantes",
        "scene_assistance": "Assistance totale des représentations payantes",
        "scene_revenus": "Revenus de billetterie excluant les taxes",
        "cine_projections": "Projections dans les cinémas et ciné-parcs",
        "cine_assistance": "Assistance dans les cinémas et ciné-parcs",
        "cine_recettes": "Recettes de billetterie dans les cinémas",
        "musique_streaming": "Nombre d'écoutes sur les services de diffusion",
        "musique_ventes": "Nombre d'enregistrements vendus",
        "livre_ventes": "Ventes finales de livres neufs",
        "biblio_usagers": "Usagers inscrits dans les bibliothèques",
        "musees_freq": "Fréquentation totale dans les institutions",
        "depenses_pub": "Dépenses en culture de l'administration",
        "depenses_menages": "Ensemble des dépenses pour la culture",
    }

    indicateurs = {}
    for row in ws.iter_rows(min_row=6, max_row=40, values_only=True):
        label_b = row[1] if len(row) > 1 else None
        if not label_b:
            continue
        label = str(label_b).replace('\xa0', '').strip()
        for key, target in cibles.items():
            if label.startswith(target):
                serie = []
                for yr, col in zip(annees, year_cols):
                    val = _to_num(row[col - 1]) if (col - 1) < len(row) else None
                    serie.append({'annee': yr, 'valeur': val})
                indicateurs[key] = {
                    'libelle': label[:80],
                    'unite': str(row[2]).strip() if row[2] else '',
                    'serie': serie,
                }
                break
    return {'annees': annees, 'indicateurs': indicateurs}


def extract_emplois_eerh(path: Path) -> list[dict]:
    """
    Tableau ISQ 2576 « Emplois salariés EERH ».
    Pour chaque industrie, on calcule la variation annuelle (Jan -> Déc) et le TCM cumulé.
    Retourne une liste de dicts : un par industrie active.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']

    MOIS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_cols = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]  # 1-indexed

    rows_iter = list(ws.iter_rows(values_only=True))
    out = []
    i = 7  # data rows start at row 8 (0-indexed = 7)
    while i < len(rows_iter):
        r = rows_iter[i]
        col0, col1 = r[0], r[1]
        if (col0 and isinstance(col0, str) and col0.strip()
                and col1 == 'n'):
            industry_raw = col0
            niveau = _hierarchy_level(industry_raw)
            terminee = _is_terminated(industry_raw)

            scian_match = re.search(r'\(([\d,\s]+)\)\s*(?:\(Terminé\))?\s*$',
                                    industry_raw.replace('\xa0', '').strip())
            scian = scian_match.group(1).replace(' ', '') if scian_match else ''
            label_clean = re.sub(r'\s*\([\d,\s]+\)\s*(?:\(Terminé\))?\s*$', '',
                                 industry_raw.replace('\xa0', '').strip()).strip()

            # n values
            n_series = [_to_num(r[c - 1]) for c in month_cols]
            # TCM row (next)
            tcm_row = rows_iter[i + 1] if i + 1 < len(rows_iter) else (None,) * 26
            tcm_series = [_to_num(tcm_row[c - 1]) for c in month_cols]

            n_jan = n_series[0]
            n_dec = n_series[-1]
            if n_jan is not None and n_dec is not None and n_jan != 0:
                variation_pct = (n_dec - n_jan) / n_jan * 100
            else:
                variation_pct = None

            out.append({
                'scian': scian,
                'industrie': label_clean,
                'niveau': niveau,
                'serie_terminee': terminee,
                'mois': MOIS,
                'n_serie': n_series,
                'tcm_serie': tcm_series,
                'n_janvier': n_jan,
                'n_decembre': n_dec,
                'variation_pct': variation_pct,
            })
            i += 2
        else:
            i += 1

    return out


def extract_ventes_livres(path: Path) -> dict:
    """
    Tableau « Variations mensuelles et annuelles des ventes de livres neufs »
    Layout : A=libellé (hiérarchique avec \\xa0), B=mois courant ($), D=var mois-1 %,
             F=var an-1 mois %, H=cumul YTD ($), J=var cumul an-1 %.
    Le mois et l'année du dépôt sont en R3 et R4.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    annee = ws.cell(row=3, column=1).value or ''
    mois = ws.cell(row=4, column=1).value or ''
    periode = f"{mois} {annee}".strip()

    lignes = []
    for row in ws.iter_rows(min_row=8, max_row=40, values_only=True):
        label_raw = row[0]
        if not label_raw or not str(label_raw).strip():
            continue
        niveau = _hierarchy_level(label_raw)
        label = _clean_label(label_raw)
        # Sauter les lignes purement structurelles (sans valeur)
        if all(_to_num(row[c]) is None for c in (1, 3, 5, 7, 9)):
            # Ligne de section (parent sans données propres) — la garder comme groupe
            lignes.append({
                'libelle': label,
                'niveau': niveau,
                'is_groupe': True,
                'mois_courant': None,
                'var_mois_prec_pct': None,
                'var_an_prec_mois_pct': None,
                'cumul_ytd': None,
                'var_cumul_an_prec_pct': None,
            })
            continue
        lignes.append({
            'libelle': label,
            'niveau': niveau,
            'is_groupe': False,
            'mois_courant': _to_num(row[1]),
            'var_mois_prec_pct': _to_num(row[3]),
            'var_an_prec_mois_pct': _to_num(row[5]),
            'cumul_ytd': _to_num(row[7]),
            'var_cumul_an_prec_pct': _to_num(row[9]),
        })
    return {'periode': periode, 'unite_monetaire': '$ courants', 'lignes': lignes}


def extract_ventes_categorie(path: Path) -> dict:
    """
    Tableau « Ventes de livres neufs selon la catégorie de points de vente,
    données mensuelles » (ISQ tableau 2341).
    Layout : A=libellé hiérarchique ; colonnes B.. = mois ($), dernière = Cumulatif.
    R3 = année, R4 = portée géographique, R6 = en-têtes de colonnes.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']
    annee = ws.cell(row=3, column=1).value or ''
    portee = ws.cell(row=4, column=1).value or ''

    # En-têtes de colonnes (R6) : Janvier, Février, ..., Cumulatif
    headers = []
    for c in range(2, (ws.max_column or 2) + 1):
        v = ws.cell(row=6, column=c).value
        if v is None or str(v).strip() == '':
            break
        headers.append(str(v).strip())
    has_cumul = bool(headers) and headers[-1].lower().startswith('cumul')
    mois = headers[:-1] if has_cumul else headers
    n_mois = len(mois)

    lignes = []
    for row in ws.iter_rows(min_row=8, max_row=60, values_only=True):
        label_raw = row[0]
        if label_raw is None or not str(label_raw).strip():
            if lignes:            # ligne vide après les données -> fin du tableau
                break
            continue
        if str(label_raw).startswith('\n') or str(label_raw).lstrip().startswith('Notes'):
            break                 # bloc de notes -> fin du tableau
        valeurs = [_to_num(row[1 + i]) for i in range(n_mois)]
        cumul = _to_num(row[1 + n_mois]) if has_cumul else None
        lignes.append({
            'libelle': _clean_label(label_raw),
            'niveau': _hierarchy_level(label_raw),
            'is_groupe': all(v is None for v in valeurs) and cumul is None,
            'valeurs': valeurs,
            'cumul': cumul,
        })

    periode = f"Janvier à {mois[-1]} {annee}".strip() if mois else str(annee).strip()
    return {
        'periode': periode,
        'annee': annee,
        'portee': str(portee).strip(),
        'mois': mois,
        'unite_monetaire': '$ courants',
        'lignes': lignes,
    }


def extract_etablissements(path: Path) -> dict:
    """
    Tableau « Nombre d'établissements culturels de certains types »
    Layout : A=libellé hiérarchique, B/D/F/... = années (2004-2024).
    Header année en R4 sous la forme '2004 (ou 2004-2005)'.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']

    # Trouver les colonnes-années (R4)
    annees, year_cols = [], []
    for c in ws[4]:
        v = c.value
        if v and re.match(r'\s*\d{4}', str(v)):
            try:
                yr = int(str(v).strip().split()[0])
                annees.append(yr)
                year_cols.append(c.column)
            except (ValueError, IndexError):
                pass

    indicateurs = []
    for row in ws.iter_rows(min_row=6, max_row=42, values_only=True):
        label_raw = row[0]
        if not label_raw or not str(label_raw).strip():
            continue
        niveau = _hierarchy_level(label_raw)
        label = _clean_label(label_raw)
        serie = []
        for yr, col in zip(annees, year_cols):
            val = _to_num(row[col - 1]) if (col - 1) < len(row) else None
            serie.append({'annee': yr, 'valeur': val})
        indicateurs.append({
            'libelle': label,
            'niveau': niveau,
            'serie': serie,
        })
    return {'annees': annees, 'indicateurs': indicateurs}


def extract_indicateurs_cinema(path: Path) -> dict:
    """
    Tableau « Indicateurs des résultats d'exploitation cinémas, données annuelles » (depuis 1975)
    Layout : A=indicateur, B=unité, C/E/G/... = années à partir de 1975.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']

    # Header R4 : C=1975, E=1976, ...
    annees, year_cols = [], []
    for c in ws[4]:
        v = c.value
        if v and isinstance(v, (int, float)) and 1900 < v < 2100:
            annees.append(int(v))
            year_cols.append(c.column)
        elif v and re.match(r'^\d{4}$', str(v).strip()):
            annees.append(int(str(v).strip()))
            year_cols.append(c.column)

    indicateurs = []
    for row in ws.iter_rows(min_row=6, max_row=42, values_only=True):
        label_raw = row[0]
        if not label_raw or not str(label_raw).strip():
            continue
        label = _clean_label(label_raw)
        unite = str(row[1]).strip() if row[1] else ''
        serie = []
        for yr, col in zip(annees, year_cols):
            val = _to_num(row[col - 1]) if (col - 1) < len(row) else None
            serie.append({'annee': yr, 'valeur': val})
        # Filtrer les lignes purement vides
        if all(p['valeur'] is None for p in serie):
            continue
        indicateurs.append({
            'libelle': label,
            'unite': unite,
            'serie': serie,
        })
    return {'annees': annees, 'indicateurs': indicateurs}


# ---------- Helpers spécifiques aux séries cinéma 1985- ----------
#
# Ces trois fichiers (langue, classement, pays annuel) partagent une mise en
# page commune : ligne d'années en colonne paire (B, D, F, ...), libellés en
# colonne A, indentation par NBSP triples (3 NBSP = sous-niveau). C'est une
# convention distincte du tableau « Indicateurs cinéma » (qui démarre en 1975
# et colle ses années en C, E, G, ...).

def _find_year_row_paired(ws, max_scan_row: int = 12) -> int | None:
    """Retourne le numéro de ligne où la colonne B contient une année (1900-2100).
    Pour les tableaux ISQ dont les années sont en colonnes paires B/D/F/...
    """
    for r in range(1, max_scan_row + 1):
        v = ws.cell(row=r, column=2).value
        if v is None:
            continue
        try:
            n = int(str(v).rstrip('¹²³⁴⁵⁶⁷⁸⁹⁰').strip())
            if 1900 < n < 2100:
                return r
        except (ValueError, TypeError):
            continue
    return None


def _read_paired_years(ws, annee_row: int) -> tuple[list[int], list[int]]:
    """Lit la ligne d'années sur colonnes paires (B, D, F, ...).
    Retourne (annees, colonnes_paires) — exclut les colonnes vides en tête/queue.
    """
    annees, cols = [], []
    c = 2
    while c <= (ws.max_column or 2):
        v = ws.cell(row=annee_row, column=c).value
        if v is not None and str(v).strip():
            try:
                annees.append(int(str(v).rstrip('¹²³⁴⁵⁶⁷⁸⁹⁰').strip()))
                cols.append(c)
            except (ValueError, TypeError):
                pass
        c += 2
    return annees, cols


def _indent_level_nbsp3(s) -> int:
    """Niveau hiérarchique pour les fichiers cinéma 1985- (3 NBSP par niveau)."""
    if s is None:
        return 0
    raw = str(s)
    nbsp = len(raw) - len(raw.lstrip('\xa0'))
    return nbsp // 3


def _extract_serie_longue_cinema(path: Path, *,
                                  labels_stop_prefixes: tuple = ('Notes', 'Source', '.. :', '- :'),
                                  ) -> dict:
    """Extracteur commun aux trois nouveaux tableaux cinéma 1985-.

    Logique : trouver la ligne d'années, puis lire chaque ligne suivante comme
    un indicateur (libellé col A, valeurs aux colonnes paires). On s'arrête
    quand on rencontre une ligne de notes/sources ou une ligne vide après
    avoir commencé à accumuler des indicateurs.
    """
    wb = load_workbook(path, data_only=True)
    ws = wb['Tableau']

    annee_row = _find_year_row_paired(ws)
    if annee_row is None:
        raise ValueError(f"Ligne d'années introuvable dans {path.name}")
    annees, year_cols = _read_paired_years(ws, annee_row)

    indicateurs = []
    for r in range(annee_row + 1, (ws.max_row or annee_row + 1) + 1):
        label_raw = ws.cell(row=r, column=1).value
        if label_raw is None or not str(label_raw).strip():
            # Ligne vide : si on a déjà accumulé des indicateurs, c'est la fin
            if indicateurs:
                break
            continue
        label_str = str(label_raw).lstrip(' \xa0').rstrip()
        if any(label_str.startswith(p) for p in labels_stop_prefixes):
            break
        niveau = _indent_level_nbsp3(label_raw)
        serie = [{'annee': yr, 'valeur': _to_num(ws.cell(row=r, column=col).value)}
                 for yr, col in zip(annees, year_cols)]
        # Filtrer les lignes sans aucune valeur (sépareurs visuels)
        if all(p['valeur'] is None for p in serie):
            continue
        indicateurs.append({
            'libelle': _clean_label(label_raw),
            'niveau': niveau,
            'serie': serie,
        })
    return {'annees': annees, 'indicateurs': indicateurs}


# ---------- Nouveaux extracteurs cinéma (publiés juin 2026) ----------

def extract_cinema_langue(path: Path) -> dict:
    """Tableau « Résultats d'exploitation cinéma — langue de projection » (1985-).

    Hiérarchie attendue :
      Projections
      Langue française
        Cinémas
        Ciné-parcs
      Autres que le français
        Cinémas
        Ciné-parcs

    Indicateur direct du marché francophone — pertinent pour la Loi 109.
    """
    return _extract_serie_longue_cinema(path)


def extract_cinema_classement(path: Path) -> dict:
    """Tableau « Résultats d'exploitation cinéma — catégorie de classement » (1985-).

    Hiérarchie attendue : Projections / Visa général / 13 ans et plus /
    16 ans et plus / 18 ans et plus, chacune subdivisée Cinémas / Ciné-parcs
    (sauf 18+).
    """
    return _extract_serie_longue_cinema(path)


def extract_cinema_pays_annuel(path: Path) -> dict:
    """Tableau « Résultats d'exploitation cinéma — pays d'origine, données annuelles » (1985-).

    Liste plate de pays, indicateur = assistance (spectateurs) ventilée par
    pays d'origine du film. Permet de calculer directement C_cinema dans R3
    sans recourir à une multiplication recettes × part hebdomadaire.

    Retourne en plus du format standard une clé `assistance_par_pays` qui
    indexe les indicateurs par libellé de pays pour usage rapide en aval.
    """
    base = _extract_serie_longue_cinema(path)
    # Index complémentaire par pays
    base['assistance_par_pays'] = {
        ind['libelle']: ind['serie']
        for ind in base['indicateurs']
    }
    return base


# ---------- Registry ----------

EXTRACTORS = {
    'extract_part_qc': extract_part_qc,
    'extract_volume_musique': extract_volume_musique,
    'extract_cinema_pays': extract_cinema_pays,
    'extract_palmares': extract_palmares,
    'extract_evolution': extract_evolution,
    'extract_emplois_eerh': extract_emplois_eerh,
    'extract_ventes_livres': extract_ventes_livres,
    'extract_ventes_categorie': extract_ventes_categorie,
    'extract_etablissements': extract_etablissements,
    'extract_indicateurs_cinema': extract_indicateurs_cinema,
    'extract_cinema_langue': extract_cinema_langue,
    'extract_cinema_classement': extract_cinema_classement,
    'extract_cinema_pays_annuel': extract_cinema_pays_annuel,
}
