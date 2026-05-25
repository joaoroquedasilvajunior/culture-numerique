# Observatoire de la souveraineté culturelle numérique

**Analyses traçables des données culturelles publiques du Québec, au regard de la
Loi 109 sur la découvrabilité.**

Ce dépôt rassemble un pipeline de données reproductible, un tableau de bord et des
chroniques d'analyse portant sur les industries de la culture et des communications
au Québec, à partir des données ouvertes de l'Institut de la statistique du Québec
(ISQ, thème « culture et médias »).

## Démarche indépendante — avertissement

L'Observatoire de la souveraineté culturelle numérique est une **initiative
indépendante de recherche et d'analyse citoyenne**. Il n'est **ni affilié, ni
mandaté, ni endossé** par l'Institut de la statistique du Québec, le ministère de la
Culture et des Communications, le Conseil de la radiodiffusion et des
télécommunications canadiennes (CRTC) ou le gouvernement du Québec.

Le projet **réutilise des données publiques** diffusées par l'ISQ. Les analyses,
interprétations et opinions présentées n'engagent que leurs auteurs. Aucune des
organisations citées n'est responsable du contenu de ce dépôt ni des conclusions qui
en sont tirées.

## Tableau de bord

Le tableau de bord est publié via GitHub Pages :

**https://joaoroquedasilvajunior.github.io/culture-num-rique/**

Activation : dans le dépôt GitHub, *Settings → Pages → Source : Deploy from a branch*,
puis branche `main` et dossier `/docs`.

## Contenu du dépôt

- `observatoire-pipeline/` — pipeline reproductible : fichiers ISQ (.xlsx) → JSON →
  tableau de bord HTML. Détails dans `observatoire-pipeline/README.md`.
- `docs/` — tableau de bord publié (`index.html`) et journal d'audit (`ledger.json`,
  `ledger_history.jsonl`).
- `chroniques/` — chroniques de l'Observatoire et items de veille.
- `Manifeste_observatoire_souverainete_culturelle.*` — posture éditoriale de
  l'Observatoire.

## Sources et traçabilité

- **Données** : Institut de la statistique du Québec — Observatoire de la culture et
  des communications du Québec. Thème « culture et médias » :
  <https://statistique.quebec.ca/fr/statistiques/par-themes/culture-et-medias>
- **Classification** : Système de classification des industries de l'Amérique du Nord
  (SCIAN) 2022.
- **Cadre politique** : Loi 109 (chapitre 38 des lois de 2025) — Loi affirmant la
  souveraineté culturelle du Québec, sanctionnée le 12 décembre 2025.
- **Journal d'audit** : `docs/ledger.json` consigne, pour chaque fichier ISQ utilisé,
  le nom, la taille, l'empreinte SHA-256 et la date de modification, ainsi que la date
  de génération du tableau de bord.

Les **fichiers .xlsx bruts de l'ISQ ne sont pas versionnés** dans ce dépôt (conditions
de réutilisation et poids du dépôt) ; le journal d'audit fige la version exacte
utilisée. Ils se téléchargent depuis le site de l'ISQ.

## Reproduire le tableau de bord

```bash
cd observatoire-pipeline
pip install -r requirements.txt
python build.py
python -m pytest tests/
```

Le pipeline lit les fichiers ISQ depuis le dossier `Données Québec/` (non versionné)
et produit `observatoire-pipeline/outputs/dashboard.html`. La version publiée dans
`docs/` est une copie figée de cette sortie.

## Licence

Aucune licence n'est encore attachée à ce dépôt. En l'absence de licence explicite, le
code et les textes demeurent « tous droits réservés » par leurs auteurs. Les données
proviennent de l'ISQ et demeurent soumises aux conditions de réutilisation de
l'Institut de la statistique du Québec.
