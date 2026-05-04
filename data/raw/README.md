# Dossier `data/raw/`

Déposer ici les fichiers .xlsx téléchargés depuis l'Institut de la statistique du Québec (ISQ) et l'Observatoire de la culture et des communications du Québec (OCCQ).

**Conserver le nom de fichier d'origine** — le pipeline retrouve chaque fichier via un motif glob défini dans `sources.yaml`. Si plusieurs fichiers correspondent au même motif (par exemple deux versions successives), le plus récent (selon `mtime`) est retenu et le ledger trace lequel a été utilisé.

## Liste des fichiers attendus (état actuel)

| Source ISQ | Motif (sources.yaml) |
|---|---|
| Part des interprètes du Québec — consommation musicale | `Part des interprètes*.xlsx` |
| Consommation d'enregistrements musicaux — type de produit | `Consommation d'enregistrements musicaux*.xlsx` |
| Résultats d'exploitation cinéma — pays d'origine | `Résultats d'exploitation des établissements*pays d'origine*.xlsx` |
| Palmarès des enregistrements musicaux | `Palmarès des enregistrements*.xlsx` |
| Évolution de statistiques clés — culture et communications | `Évolution de statistiques clés*.xlsx` |
| Emplois salariés EERH (tableau 2576) | `Emplois salariés*.xlsx` |

Les fichiers listés ne sont pas exhaustifs : on peut en déposer d'autres pour les explorations à venir, ils seront ignorés tant qu'une nouvelle source n'a pas été déclarée dans `sources.yaml`.

## Source officielle

Les tableaux ISQ se téléchargent depuis https://statistique.quebec.ca/fr/recherche?sujet=culture-et-medias

Pour chaque fichier déposé ici :
- noter la **date du téléchargement** (le `mtime` y suffit)
- ne pas modifier le contenu (toute transformation doit passer par le pipeline pour rester traçable)
- conserver les fichiers .xlsx d'origine plutôt que des conversions (CSV, etc.)
