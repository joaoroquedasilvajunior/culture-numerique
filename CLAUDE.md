# Carnet de données — souveraineté culturelle numérique

Instructions de projet pour Claude. Ce fichier est canonique et remplace
`INSTRUCTIONS_PROJET.md` (conservé pour l'historique). Mis à jour le 2026-10-02.

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
(33 sources, registre EXTRACTORS) → src/derive.py (repères R1-R7 +
lentilles auxiliaires) → templates/dashboard.html.tmpl (payload JSON inline
`const D = {...}`) → outputs/dashboard.html → copié vers docs/ (GitHub Pages).

**Routine de mise à jour** (ne pas improviser autre chose) :
1. Fichiers frais dans `Données Québec/` (téléchargés par Joao — convention :
   les données brutes passent par lui, le pipeline lit le dossier).
2. `./maj_dashboard.sh` depuis la racine (archive, build, tests, copie docs/, commit).
3. `git push` — Pages se régénère.

**Tests = sentinelles.** 81 tests d'intégrité épinglent les valeurs-clés. Un
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
- **Séries révisées rétroactivement** : la série mensuelle EERH est en moyennes
  mobiles de trois mois et l'ISQ révise les mois déjà publiés. Mai 2026 valait
  n = 14 820 dans le fichier du 20 août et n = 14 734 dans celui du 12 septembre
  (5121), ce qui déplace la variation Jan → Mai de +8,39 % à +7,76 % sans
  qu'aucune donnée nouvelle n'intervienne. Conséquence : une variation
  rattachée à un mois donné n'est pas stable d'un millésime à l'autre. Toujours
  la reconstituer depuis le fichier courant plutôt que citer une valeur
  antérieure, y compris une valeur publiée par nous.
- **Séries terminées** : à conserver comme capsules historiques avec
  `statut_serie: terminee` (ex. tableau 2142, ventes top 200 de l'ère Nielsen).
- **Millésimes** : ne jamais fusionner une lecture cumulative YTD en cours
  (ex. top 20 2026) avec un bilan annuel clos (ex. palmarès artistes 2025).
  Chaque carte du dashboard porte son millésime.
- **Coupes invisibles dans le nom de fichier** : certains tableaux ISQ
  (ex. 4949, arts de la scène) exposent leurs dimensions à l'interface de
  téléchargement — année, région, discipline, provenance, langue, taille de
  salle — sans les inscrire dans le nom. La coupe retenue n'est lisible qu'en
  L3 à L9 du classeur. Un `file_pattern` ne peut donc pas distinguer deux
  coupes du même tableau. Déclarer alors `multi_fichiers: true` dans
  sources.yaml : l'extracteur reçoit la liste complète des fichiers et indexe
  chaque coupe par ce qu'elle déclare. Le ledger empreinte chaque fichier
  consommé, et « Sources OK » compte les sources, pas les fichiers.
- **Ruptures de série déclarées** : l'ISQ annonce parfois une
  non-comparabilité (ex. tableau 4949, les données 2024+ ne se raccordent pas
  à 2004-2023 : périodicité, population d'enquête et questionnaire changés).
  Transporter le caveat jusqu'au tableau de bord plutôt que le laisser en note
  de bas de classeur, et ne jamais raccorder les deux segments.

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

- **Protocole des repères** (`Protocole_reperes_observatoire.md`, v1.3.0) :
  R1 écart de découvrabilité, R2 profondeur du catalogue, R3 consommation
  absolue, R4 indice d'angle mort (9/12, A = 0,750), R5 volume d'œuvres (en
  chantier, sources ADISQ/SODEC/OCCQ à identifier ; couvertures partielles
  documentées), R6 vitalité des arts vivants et arts visuels subventionnés
  (CALQ), officialisé en v1.2.0, R7 captation de valeur dans le spectacle
  vivant payant (ISQ 4949), créé en v1.3.0 et provisoire. Baseline annuelle
  2025 figée pour R1 à R3, avec la lecture hebdomadaire YTD conservée en
  parallèle.
  **R7 est le miroir des autres repères** : là où R1 à R3 mesurent des marchés
  où le Québec est minoritaire partout, R7 mesure un domaine où la
  souveraineté de production est acquise (87,9 % des représentations) et où la
  question devient le partage de la recette (68,3 % des revenus), soit un
  gradient de +19,6 points au T1 2025. Périmètre à ne pas confondre avec celui
  du CALQ qui porte R6 : toutes les représentations payantes contre les seuls
  organismes subventionnés.
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
  redistribuer, **le gâteau grossit et la tranche reste** (septembre 2026 :
  le box-office québécois toutes origines progresse de 5,1 % sur un an
  pendant que la part des films québécois tombe à 3,2 % ; le volume de
  streaming dépasse le rythme de 2025 pendant que la part québécoise stagne
  à 7,1 %. Une part stable dans un marché en croissance n'est pas une
  position tenue, et seule la mesure absolue de R3 le montre).

## Surface d'exécution

Le projet se pilote depuis **Claude Code**, à la racine du dépôt. Les tâches
planifiées de l'application de bureau ont été dépréciées le **2026-10-02** ;
les deux agents du Carnet qui en dépendaient sont devenus des **skills du
dépôt**, invoqués à la demande. Rien n'est perdu : la méthode complète vit
désormais dans des fichiers versionnés plutôt que dans la configuration d'un
planificateur.

Conséquence méthodologique à assumer : **sans planificateur, les fenêtres
temporelles ne sont plus garanties.** Un agent conçu pour couvrir sept jours
peut en couvrir vingt. Chaque skill concerné doit établir l'intervalle réel
depuis la dernière exécution plutôt que présumer sa cadence nominale. Une
fenêtre élargie annoncée comme telle vaut mieux qu'une fenêtre nominale fausse.

- `.claude/skills/` : skills du projet, versionnés, chargés automatiquement
  par Claude Code quand le dépôt est le dossier de travail. Frontmatter
  minimal : `name` et `description`. La `description` est le seul texte vu
  avant chargement, donc elle doit dire ce que fait le skill ET quand le
  déclencher.
- `CLAUDE.md` (ce fichier) : déjà la convention Claude Code, chargé à chaque
  session. Aucune migration nécessaire.
- Pas de planification automatique pour l'instant. Si le besoin revient, les
  pistes sont launchd sur le Mac (attention aux problèmes connus
  d'authentification quand le processus part de launchd) ou GitHub Actions
  (mais les données brutes sont gitignorées, donc seules les sorties publiées
  dans `docs/` y seraient lisibles). À vérifier contre la documentation
  courante avant de s'y engager.

## Agents du Carnet

Les deux agents sont des skills de `.claude/skills/`. Ils proposent, Joao
décide. Aucun des deux ne publie ni ne pousse quoi que ce soit.

- **Chroniqueur** (`chroniqueur-carnet`, cadence recommandée : vendredi) :
  données → angle → revue médiatique QC (la présence ET l'absence sont des
  faits ; deux requêtes minimum avant de conclure au silence, requêtes
  listées) → brouillon dans `chroniques/` (privé, gitignoré). Réviser les
  brouillons en éditeur : vérifier les chiffres aux sources ET les références
  médiatiques externes avant publication.
- **Veille MCCQ + CRTC** (`veille-mccq-crtc`, cadence recommandée : lundi) :
  digest réglementaire, focus Loi 109 et découvrabilité, avec protocole de
  vérification des restrictions d'accès aux sources. Distinction cardinale :
  « la source n'a rien publié » (vérifié) n'est pas « la source n'a pas pu
  être vérifiée » (vide ou bloquée). La seconde ne se présente jamais comme
  la première.

L'ordre compte : la veille du lundi alimente le chroniqueur en pistes
réglementaires avant qu'il ne choisisse son angle.

## Repères du dépôt

- `.claude/skills/` — les deux agents du Carnet (`chroniqueur-carnet`,
  `veille-mccq-crtc`), versionnés avec leurs références.
- `observatoire-pipeline/` — le pipeline (README.md pour les détails).
- `Données Québec/` — données brutes (xlsx ISQ, zips CANSIM, JSON récoltés) ;
  `_archives/` par date.
- `chroniques/` — atelier éditorial privé (gitignoré) : chroniques numérotées,
  brouillons du chroniqueur (`brouillon-AAAA-MM-JJ-slug.md`), veilles.
- `docs/` — tableau de bord publié (GitHub Pages) :
  https://joaoroquedasilvajunior.github.io/culture-numerique/
- `Manifeste_observatoire_souverainete_culturelle.md` — posture éditoriale.
- `Protocole_reperes_observatoire.md` — protocole gelé des repères.
