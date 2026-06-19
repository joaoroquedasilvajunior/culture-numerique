# Culture Québec en donnée — instructions de projet

Analyses traçables des données culturelles de l'Institut de la statistique du Québec
(statistique.quebec.ca, thème culture-et-médias), au regard de la **Loi 109** sur la
découvrabilité. Cadre : **Carnet de données — souveraineté culturelle numérique**
(anciennement « Observatoire de la souveraineté culturelle numérique » jusqu'au
2026-06-12 ; renommé pour éviter la confusion avec l'OCCQ et d'autres
observatoires institutionnels).

## Conventions

- Répondre en **français (Québec)**.
- **Traçabilité** : toujours citer la source, la version de classification (SCIAN 2022),
  la période et la date de mise à jour.
- **Ne pas produire de .docx / .pdf** sauf demande explicite ("seulement quand c'est nécessaire").
- Livrables réutilisables ; notes méthodologiques systématiques.
- Rester économe : ne pas ré-explorer le dépôt ni relire les gros fichiers (HTML, PDF)
  quand la routine ci-dessous suffit.

## Mettre à jour le tableau de bord — routine économe

Le tableau de bord est généré par un pipeline reproductible. Pour le mettre à jour,
**ne pas relire le HTML ni ré-explorer le dépôt**. Faire seulement :

1. Vérifier que les .xlsx ISQ à jour sont dans `Données Québec/` — le pipeline retient,
   pour chaque motif de `sources.yaml`, le fichier le plus récent par date de modification.
2. `cd observatoire-pipeline && python build.py`
3. `python -m pytest tests/` — si un test échoue parce que l'ISQ a révisé un chiffre,
   c'est le signal voulu : confirmer la révision auprès du fichier source, puis mettre à
   jour la valeur attendue dans `tests/test_extract.py`.

Sorties : `observatoire-pipeline/outputs/dashboard.html`, JSON dans `data/processed/`,
journal d'audit dans `outputs/ledger.json`. Détails (sources, extracteurs, cadre
tripartite Loi 109) : voir `observatoire-pipeline/README.md`.

## Repères du dépôt

- `observatoire-pipeline/` — pipeline ISQ → JSON → tableau de bord HTML.
- `chroniques/` — chroniques du Carnet de données (`01_`, `02_`…) et items de veille
  (`veille_AAAA-MM_*`). Méthode éditoriale : pluralisme méthodologique + Cadre UNESCO 2025
  (écosystème culturel et créatif, lentille praxéologique, 4 capitaux, 3 étapes).
- `Données Québec/` — fichiers .xlsx téléchargés de l'ISQ (sources du pipeline).
- `Manifeste_observatoire_souverainete_culturelle.*` — posture éditoriale du Carnet de données
  (le nom de fichier conserve « observatoire » par stabilité git).
- `Protocole_reperes_observatoire.md` — protocole gelé des 5 repères suivis (v1.0, 2026-05-25) ; définitions, sources, baseline 2025
  (le nom de fichier conserve « observatoire » par stabilité git).

## Veille

Suivre de près le **ministère de la Culture et des Communications du Québec** et le
**CRTC** (publications, communiqués, décisions, consultations). Périmètre, cadence et
format à confirmer — voir les tâches du projet.
