# Carnet de données — souveraineté culturelle numérique

Instructions de projet pour Claude. Ce fichier est canonique et remplace
`INSTRUCTIONS_PROJET.md` (conservé pour l'historique). Mis à jour le 2026-08-17.

## Identité et posture

Projet indépendant d'analyse des données culturelles québécoises au regard de la
Loi 109 (souveraineté culturelle et découvrabilité, chapitre 38 de 2025).
Anciennement « Observatoire de la souveraineté culturelle numérique » jusqu'au
2026-06-12 ; les noms de fichiers et dossiers conservent « observatoire » par
stabilité git.

**Avis d'indépendance obligatoire sur tout livrable public** : le Carnet n'est
ni affilié, ni mandaté, ni endossé par l'ISQ, le MCC, le CRTC ou tout
gouvernement. Les analyses n'engagent que leurs auteurs.

## Conventions de travail

- Répondre en **français (Québec)**. Pas de tirets cadratins dans la prose
  destinée à publication (chroniques, cartes du tableau de bord).
- **Traçabilité systématique** : source, tableau, classification (SCIAN 2022),
  période, date de mise à jour — pour chaque chiffre.
- Ne pas produire de .docx/.pdf sauf demande explicite.
- Utiliser AskUserQuestion avant tout choix structurant (périmètre, trajectoire
  d'intégration, place dans le protocole).
- **Rester économe** : ne pas ré-explorer le dépôt ni relire les gros fichiers
  quand la routine suffit. Les conventions ci-dessous existent pour ça.
- Les mesures se vérifient avant de s'affirmer : valider un zéro avant de le
  publier (le matcher ET l'inspection visuelle), tester une hypothèse d'API
  avant de la déclarer morte, deux requêtes minimum avant de conclure à un
  silence médiatique.

## Architecture du pipeline

`observatoire-pipeline/` : sources.yaml (manifeste) → src/extract.py
(29 extracteurs, registre EXTRACTORS) → src/derive.py (repères R1-R6 +
lentilles auxiliaires) → templates/dashboard.html.tmpl (payload JSON inline
`const D = {...}`) → outputs/dashboard.html → copié vers docs/ (GitHub Pages).

**Routine de mise à jour** (ne pas improviser autre chose) :
1. Fichiers frais dans `Données Québec/` (téléchargés par Joao — convention :
   les données brutes passent par lui, le pipeline lit le dossier).
2. `./maj_dashboard.sh` depuis la racine (archive, build, tests, copie docs/, commit).
3. `git push` — Pages se régénère.

**Tests = sentinelles.** 69 tests d'intégrité épinglent les valeurs-clés. Un
test qui casse après une mise à jour ISQ est le signal voulu : vérifier la
révision dans le fichier source, mettre à jour la valeur attendue en
documentant l'historique dans la docstring (ex. « 15 (avril) → 17 (mai) →
14 (juillet) »). Certains tests sont des alertes inversées : si « 0 film QC au
top 20 » casse, c'est une bonne nouvelle à signaler au chroniqueur.

## Pièges connus des données

- **Noms de fichiers ISQ instables** : suffixes `_2`/`_3` à chaque
  téléchargement, libellés parfois raccourcis (« cut et des comm »), suffixes
  géographiques qui apparaissent/disparaissent. Les patterns de sources.yaml
  sont des globs ; le pipeline prend le plus récent par mtime. Resserrer un
  pattern quand deux tableaux partagent un préfixe (cf. cinéma hebdo vs annuel).
- **Unicode** : les accents des noms de fichiers peuvent être en NFD (glob
  Python les rate — itérer avec `iterdir()` + `in`) ; la ligature œ n'est pas
  décomposée par NFKD (normaliser explicitement œ→oe dans les matchers).
- **Marqueurs ISQ** : `..` non disponible, `...` n'ayant pas lieu de figurer,
  valeurs supprimées pour confidentialité — les respecter, jamais les inventer.
- **Refs CANSIM dans les fichiers ISQ** : elles ressemblent à des numéros de
  fiche ISQ. Toujours valider par l'URL permanente.
- **`round()` Python fait du banker's rounding** (round(1.325, 2) → 1.32).
- **Séries terminées** : à conserver comme capsules historiques avec
  `statut_serie: terminee` (ex. tableau 2142, ventes top 200 de l'ère Nielsen).
- **Millésimes** : ne jamais fusionner une lecture cumulative YTD en cours
  (ex. top 20 2026) avec un bilan annuel clos (ex. palmarès artistes 2025).
  Chaque carte du dashboard porte son millésime.

## Périmètres à ne pas confondre

- **MusicBrainz ≠ définition ISQ** : MusicBrainz rattache par lieu de
  naissance/formation (Mylène Farmer, Leonard Cohen y sont QC) ; l'ISQ définit
  « interprète du Québec » autrement. Signaler l'écart quand on croise.
- **Taux de liens MusicBrainz = planchers de complétude des métadonnées
  ouvertes**, jamais des taux de présence réelle sur les plateformes.
- **Dénominateurs AEI** : usage_pct d'une subregion = part dans le pays ;
  usage_pct d'un pays = part dans le monde. Ne pas comparer entre niveaux.
- **Géographies de la grille AI-exposure** : lentilles 1b et 2 sont Québec,
  1a reste Canada national (StatCan ne descend pas en subregion).

## Accès aux données de plateformes (leçons acquises, ne pas re-tester)

- **Deezer** : API publique ouverte, sans clé, ~50 req/5 s. Notre unique
  source de popularité par artiste (nb_fan) — choix structurel, pas pis-aller.
- **Spotify** : verrouillé pour les apps en mode développement depuis
  février 2026 — batch 403, plafond ~600 appels/jour, champs
  popularité/followers/genres retirés des réponses (même avec token
  utilisateur PKCE, testé le 2026-07-23). Seule issue : Extended Quota Mode.
- **Apple Music** : aucune métrique de popularité par artiste dans aucune API
  publique. Les flux marketing RSS (rss.marketingtools.apple.com) sont ouverts
  et servent le top 100 Canada.
- **MusicBrainz** : User-Agent applicatif obligatoire, 1 req/s, 503 fréquents
  (retry backoff). CC0. Le browse d'une zone province englobe ses villes.
- **Hugging Face (AEI)** : téléchargement direct ouvert. Pinner l'ingest sur un
  dossier release_YYYY_MM_DD précis — le schéma change entre vintages.
- **Règle absolue** : ne jamais contourner un blocage d'accès (pas de curl de
  substitution, pas de scraping de pages protégées). Un blocage documenté est
  une donnée ; le consigner avec sa date et sa nature.

## Sources compilées manuellement

Quand une donnée n'existe qu'en communiqué ou article (ex. Chart 1 de StatCan
C-AIOE, communiqué ISQ du bilan musical), la compiler en CSV/JSON dans
`Données Québec/` avec champs source, date_compilation et methode_compilation
explicites, puis l'intégrer comme source normale. À recouper quand le tableau
officiel paraît.

## Scripts de récolte (racine du projet)

`moissonneur_musicbrainz.py` (catalogue artistes QC, reprenable),
`enrichir_deezer.py` (nb_fan), `recolter_apple_top100.py` (top 100 Canada),
`enrichir_spotify.py` (identités seulement, métriques verrouillées),
`test_spotify_pkce.py` et `sonde_musicbrainz.py` (sondes de faisabilité,
garder comme références méthodologiques). Exécutés par Joao, sorties datées
dans `Données Québec/`.

## Cadres analytiques

- **Protocole des repères** (`Protocole_reperes_observatoire.md`, v1.1.0,
  gelé) : R1 écart de découvrabilité, R2 profondeur du catalogue, R3
  consommation absolue, R4 indice d'angle mort, R5 volume d'œuvres (en
  chantier — sources ADISQ/SODEC/OCCQ à identifier). R6 (vitalité des arts
  vivants subventionnés, CALQ) est auxiliaire, à formaliser en v1.2.0.
- **Grille AI-exposure à trois lentilles** (skill
  `ai-exposure-creative-sector`) : 1a demande experte (C-AIOE), 1b demande
  marché (postes vacants), 2 usage révélé (AEI). L'écart entre lentilles est
  le constat. Lentille 3 améliorée : effectifs × rémunération.
- **Cadre UNESCO 2025** (chroniques) : ECC, lentille praxéologique,
  4 capitaux, 3 étapes.
- **Motifs éditoriaux établis** : l'iceberg de la découvrabilité (catalogue →
  documenté → mesuré → palmarès), la longue traîne (médiane 185 fans, top 1 %
  = 75,8 %), la courbe de profondeur (densité QC ~5 % à toutes les
  profondeurs du palmarès), la bascule d'ère (ventes 58,9 % → streaming
  7,1 %), l'asymétrie d'accès aux données de plateformes, rendre visible ≠
  redistribuer.

## Agents du Carnet

- **Chroniqueur** (skill `chroniqueur-carnet` + tâche `chroniqueur-hebdo-carnet`,
  vendredi 9 h) : données → angle → revue médiatique QC (la présence ET
  l'absence sont des faits ; deux requêtes minimum avant de conclure au
  silence, requêtes listées) → brouillon dans `chroniques/` (privé, gitignoré).
  L'agent propose, Joao publie. Réviser les brouillons en éditeur : vérifier
  chiffres aux sources ET références médiatiques externes avant publication.
- **Veille MCCQ + CRTC** (tâche `veille-mccq-crtc`, lundi 8 h) : digest
  réglementaire hebdo, focus Loi 109/découvrabilité, avec protocole de
  vérification des restrictions d'accès aux sources (voir le prompt de la
  tâche).

## Repères du dépôt

- `observatoire-pipeline/` — le pipeline (README.md pour les détails).
- `Données Québec/` — données brutes (xlsx ISQ, zips CANSIM, JSON récoltés) ;
  `_archives/` par date.
- `chroniques/` — atelier éditorial privé (gitignoré) : chroniques numérotées,
  brouillons du chroniqueur (`brouillon-AAAA-MM-JJ-slug.md`), veilles.
- `docs/` — tableau de bord publié (GitHub Pages) :
  https://joaoroquedasilvajunior.github.io/culture-numerique/
- `Manifeste_observatoire_souverainete_culturelle.md` — posture éditoriale.
- `Protocole_reperes_observatoire.md` — protocole gelé des repères.
