# Observatoire de la souveraineté culturelle numérique — pipeline

Pipeline reproductible qui transforme les tableaux statistiques de l'**Institut de la statistique du Québec** (ISQ) et de l'**Observatoire de la culture et des communications du Québec** (OCCQ) en un tableau de bord HTML interactif structuré au regard de la **Loi 109** (chapitre 38, 2025) sur la souveraineté culturelle et la découvrabilité des contenus francophones.

> Ce dépôt accompagne le *[Manifeste de l'Observatoire de la souveraineté culturelle numérique](../Manifeste_observatoire_souverainete_culturelle.pdf)*. Il est l'incarnation technique de la traçabilité que ce manifeste promet.

## Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Déposer les fichiers .xlsx ISQ dans le dossier configuré (par défaut : ../Données Québec/).
#    Voir sources.yaml pour les motifs de fichiers attendus, et la section « Organisation des
#    données » ci-dessous pour le choix du dossier source.

# 3. Lancer le pipeline
python build.py
```

## Organisation des données

Par défaut, le pipeline lit les fichiers ISQ depuis `../Données Québec/` — un dossier qui se trouve
au-dessus du dépôt. C'est le mode recommandé : tu télécharges les .xlsx ISQ dans ce dossier
(qui sert aussi pour d'autres usages de ton projet), et le pipeline les y trouve. Pas de duplication,
pas de divergence, pas de fichier ISQ versionné dans le dépôt.

Pour basculer en mode self-contained (toutes les sources dans le dépôt), édite `sources.yaml` :

```yaml
raw_data_dir: "data/raw"
```

et dépose tes .xlsx dans `data/raw/`. Le `.gitignore` continue à exclure les .xlsx pour éviter
de redistribuer les données ISQ par mégarde — à toi de décider si tu veux les versionner ou pas.

Le tableau de bord est généré dans `outputs/dashboard.html` ; le journal d'audit dans `outputs/ledger.json` ; les JSON intermédiaires dans `data/processed/`.

## Architecture

```
observatoire-pipeline/
├── sources.yaml              ← Manifeste des sources ISQ (extensible)
├── build.py                  ← Point d'entrée
├── requirements.txt
├── README.md
├── data/
│   ├── raw/                  ← .xlsx téléchargés depuis l'ISQ
│   └── processed/            ← JSON normalisés (un par source + combiné)
├── src/
│   ├── extract.py            ← Une fonction par tableau ISQ
│   ├── render.py             ← HTML rendering depuis le template
│   ├── ledger.py             ← Audit trail (SHA-256, mtime, build_iso)
│   └── pipeline.py           ← Orchestrateur
├── templates/
│   └── dashboard.html.tmpl   ← Template HTML avec placeholder __DASHBOARD_DATA__
├── outputs/
│   ├── dashboard.html        ← Tableau de bord rendu
│   ├── ledger.json           ← Journal du dernier build
│   └── ledger_history.jsonl  ← Historique de tous les builds (append-only)
└── tests/
    └── test_extract.py
```

## Principes de conception

**Reproductibilité.** Tout fichier produit par ce pipeline peut être régénéré à partir des fichiers .xlsx d'origine. Aucune valeur n'est saisie à la main dans le code ; toutes les transformations sont documentées.

**Traçabilité.** Chaque exécution écrit un *ledger* JSON qui consigne, pour chaque source utilisée : empreinte SHA-256, taille, date de modification, libellé. L'historique est appendé à `ledger_history.jsonl`. Cela permet de reconstituer, des mois plus tard, sur quels fichiers exacts un chiffre publié reposait.

**Modularité.** Pour ajouter un nouveau tableau ISQ : (1) déposer le .xlsx dans `data/raw/`, (2) écrire une fonction d'extraction dans `src/extract.py` qui retourne un dict, (3) la déclarer dans le registre `EXTRACTORS`, (4) ajouter une entrée dans `sources.yaml`. Aucun code orchestrateur à toucher.

**Robustesse Unicode.** Les noms de fichiers ISQ contiennent des caractères accentués (Évolution, Résultats, Palmarès…). Le pipeline normalise systématiquement en NFC pour matcher les motifs `sources.yaml` quel que soit le système (macOS stocke en NFD, Linux en NFC).

**Marqueurs ISQ traités explicitement.** Les valeurs textuelles spéciales (`..`, `...`, `--`, `-`, `F`) sont traduites de manière documentée (voir le docstring de `src/extract.py`) plutôt que silencieusement converties.

## Sources couvertes (état actuel)

| Clé | Tableau ISQ | Axes du tableau de bord |
|---|---|---|
| `part_qc` | Part des interprètes du Québec dans la consommation musicale | Consommation |
| `volume_musique` | Consommation d'enregistrements musicaux selon le type de produit | Consommation, Présence |
| `cinema_pays` | Résultats d'exploitation cinéma selon le pays d'origine | Consommation |
| `palmares_top20` | Palmarès des enregistrements musicaux | Découvrabilité |
| `evolution_stats` | Évolution de statistiques clés culture et communications | Présence, Écosystème |
| `emplois_eerh` | Emplois salariés EERH (tableau 2576) | Écosystème |

Voir `sources.yaml` pour les URL ISQ permanentes et la classification de chaque source.

## Cadre tripartite (Loi 109, art. 33)

Le tableau de bord organise les indicateurs selon les trois concepts inscrits à l'article 33 de la *Loi sur la découvrabilité des contenus culturels francophones dans l'environnement numérique* :

- **Présence** — quels contenus québécois francophones existent et sont accessibles dans l'environnement numérique ?
- **Découvrabilité** — sont-ils repérables, en particulier par une personne qui n'en fait pas la recherche ?
- **Consommation** — sont-ils effectivement écoutés, visionnés, lus ?

S'y ajoutent **Écosystème de production** (capacité productive, EERH) et **Angles morts** (ce que la statistique publique ne mesure pas encore).

## Tests

```bash
python -m pytest tests/
```

Les tests couvrent les valeurs-clés attendues sur les fichiers ISQ de référence (par exemple : part QC streaming = 6,8 % YTD février 2026). Si l'ISQ révise ses chiffres, les tests échoueront — c'est précisément l'effet recherché : le pipeline signale les changements plutôt que les masquer.

## Limites connues

- **EERH exclut les travailleurs autonomes** (T4 obligatoire). À signaler dans toute publication mobilisant `emplois_eerh`.
- **Données désaisonnalisées révisées** à chaque mise à jour ISQ. Le ledger fige la version utilisée.
- **Découvrabilité algorithmique non mesurable** depuis l'extérieur des plateformes. Les palmarès sont un proxy imparfait. Recommandations 25-26 du Comité-conseil 2024 et règlement à venir de la Loi 109 sont les leviers attendus.

## Cadence de mise à jour suggérée

Trimestrielle, calée sur les rythmes de mise à jour ISQ. À chaque mise à jour : retélécharger les .xlsx pertinents, les remettre dans `data/raw/` (les anciens fichiers peuvent être archivés dans `data/raw/_archives/`, ils sont ignorés par le pipeline), relancer `python build.py`. Le ledger trace ce qui a changé.

## Licence

À déterminer (recommandation : MIT pour le code, CC BY 4.0 pour la documentation et les données dérivées). Les données primaires demeurent la propriété de l'ISQ et des organismes producteurs cités ; ce dépôt n'en redistribue pas les fichiers .xlsx d'origine.

## Contact et contributions

Voir le manifeste pour la posture éditoriale. Les contributions externes (corrections, ajouts d'extracteurs, suggestions d'indicateurs) sont bienvenues et tracées.

---

*Pipeline v1.0.0 — mai 2026 — Joao Roquer*
