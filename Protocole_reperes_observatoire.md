# Protocole des repères suivis — Observatoire de la souveraineté culturelle numérique

**Version 1.1.0** — révisée le 2026-05-26 (gel initial : 2026-05-25)
**Cadre :** pluralisme méthodologique + Cadre UNESCO 2025 pour les statistiques culturelles
**Posture éditoriale :** voir *Manifeste de l'Observatoire de la souveraineté culturelle numérique*

---

## Principe directeur

Cinq repères ancrés, à définition figée, re-mesurés à l'identique année après année.
Ce n'est *pas* un indice composite. Ces repères sont l'objet stable *à propos duquel*
les grilles de lecture (UNESCO 2025, Loi 109, autres) peuvent se prononcer — y compris
divergemment. C'est cette divergence entre grilles que le pluralisme méthodologique
traite comme résultat.

Quatre repères sont mesurables aujourd'hui. Un cinquième (5b, en annexe) est annoncé
publiquement comme *en chantier de recherche*, parce que la statistique publique
québécoise ne le mesure pas encore — ce qui est en soi un résultat.

## Cadence

Tous les repères sont mesurés **annuellement**, sur l'année civile (1ᵉʳ janvier → 31 décembre).
Mesure prise au **1ᵉʳ mars de l'année suivante**, sur la base des dernières données ISQ
disponibles à cette date.

## Année de référence (baseline pré-règlement)

**2025** est l'année de référence. La *Loi sur la souveraineté culturelle et la
découvrabilité des contenus francophones* (Loi 109, chapitre 38 des lois de 2025) a
été sanctionnée le 12 décembre 2025 ; les règlements d'application n'étaient pas
entrés en vigueur au moment de la rédaction du présent protocole.

Les valeurs 2025 servent de **point de comparaison fixe** pour toute observation
ultérieure. Une révision rétroactive d'une valeur de baseline n'est admise que pour
suivre une révision ISQ documentée, et est inscrite au journal de révisions
(voir *Discipline du gel*).

## Discipline du gel

1. **Versionnement (semver-light).**
   - `x.0` — révision majeure : ajout, retrait, ou modification d'ensemble des repères.
   - `x.y` — révision mineure : redéfinition opérationnelle d'un repère existant.
   - `x.y.z` — correction factuelle : précision sur une source, enrichissement de
     traçabilité, sans changement de définition.
   Toute modification déclenche une nouvelle version avec note de motivation au journal.
2. Les valeurs déjà publiées ne sont pas réécrites silencieusement ; l'historique des
   révisions est tenu en annexe.
3. Le pipeline `observatoire-pipeline/` calcule les repères à partir des sources
   fixées ici. Le ledger trace les fichiers sources utilisés à chaque exécution
   (SHA-256, mtime, build_iso).
4. Aucun nouveau repère ne s'ajoute sans révision majeure du protocole (passage à 2.0).

---

## Repère 1 — Écart de découvrabilité

**Concept.** Rapport entre la part québécoise dans les canaux d'achat intentionnel et
la part québécoise dans les canaux algorithmiques. Mesure la pression structurelle
qu'exerce la médiation algorithmique sur la souveraineté culturelle.

**Définition opérationnelle.**

Soient, en pourcentage cumulatif annuel :
- *p_alb* = part des interprètes du Québec dans les ventes d'albums en fichier numérique téléchargés ;
- *p_str* = part des interprètes du Québec dans les écoutes en streaming musical.

Deux formes complémentaires, publiées ensemble :

- **Ratio** (sans dimension) : `R = p_alb / p_str`
- **Écart absolu** (en points de %) : `E = p_alb − p_str`

**Source.** ISQ — tableau **4153** « Part des interprètes du Québec dans la
consommation d'enregistrements musicaux, données hebdomadaires »
(compilation OCCQ, données Luminate Data).
URL permanente : `https://statistique.quebec.ca/fr/produit/tableau/4153`

**Période.** Cumulatif annuel YTD, prélevé sur la dernière semaine de l'année publiée
par l'ISQ (typiquement semaine 52 ou la plus tardive disponible avant clôture).

**Baseline 2025.** À confirmer auprès de l'archive ISQ du tableau 4153.
**Observation de référence** (mai 2026, en attente de la baseline 2025 définitive) :
semaine du 24 au 30 avril 2026, cumulatif annuel — *p_str* = 6,9 % ; *p_alb* = 24,5 %.
D'où *R* ≈ 3,55 ; *E* = 17,6 pts.

**Direction « sovereignty gain ».** *R* se comprime vers 1 ; *E* diminue.

**Limites à citer systématiquement.**
- Le streaming n'est pas un canal 100 % algorithmique (recherche directe possible) ;
  le téléchargement n'est pas 100 % intentionnel (recommandations sur Apple / Google).
  Le repère mesure la *direction* de la pression algorithmique, pas son intensité absolue.
- Ne couvre que la musique. La transposition au cinéma et au livre exige des données
  équivalentes que l'ISQ ne publie pas dans la même forme.

---

## Repère 2 — Profondeur du catalogue québécois consommé

**Concept.** Nombre d'interprètes québécois distincts présents dans les palmarès,
sur deux fenêtres. Mesure la diversité interne de la souveraineté : une part qui
monte portée par un seul superstar est fragile.

**Définition opérationnelle.**
- *N₂₀* = nombre d'interprètes québécois distincts dans le top 20 streaming cumulatif annuel.
- *N₂₀₀* = idem sur le top 200 (si publié).

**Source.** ISQ — **tableau 2620** « Palmarès des enregistrements musicaux »
(URL permanente : `https://statistique.quebec.ca/fr/produit/tableau/2620`).
Pour *N₂₀₀* : sources ADISQ ou Luminate à confirmer si l'ISQ ne le publie pas directement.

**Période.** Cumulatif annuel.

**Baseline 2025.** *N₂₀* : à confirmer auprès de l'archive ISQ.
**Observation de référence** (cumulatif 2026 en mai) : *N₂₀* = 1 (Les Cowboys Fringants, rang 15).

**Direction « sovereignty gain ».** *N₂₀* et *N₂₀₀* augmentent.

**Limites.**
- Ne se lit qu'en regard du repère 1. Faible diversité + part forte = monoculture ;
  forte diversité + part faible = présence dispersée. Les deux configurations existent
  et n'ont pas le même sens politique.
- Top 20 sensible aux fluctuations d'un seul succès ; top 200 plus robuste mais
  dépendant de sources non standardisées.

---

## Repère 3 — Consommation québécoise absolue

**Concept.** Volume effectif de culture québécoise consommée au Québec, par canal.
Pondération multiplicative : `volume_total × part_QC`. Évite l'effet trompeur d'un
marché total qui grossit sans gain de souveraineté.

**Définition opérationnelle.** Pour chaque canal *c* :
`C_c = volume_total_annuel_c × part_QC_c`

Canaux retenus :
- Streaming musical (écoutes québécoises de musique québécoise, en milliers).
- Albums en fichier numérique téléchargés (unités).
- Albums sur support physique (unités).
- Pistes numériques unitaires (unités).
- Cinéma — recettes québécoises de films québécois (à intégrer si série annuelle
  cohérente disponible).

**Sources ISQ.**
- Volumes totaux : **tableau 3171** *Évolution de statistiques clés de la culture et des
  communications* (clé pipeline : `evolution_stats`) ; **tableau 2140** *Consommation
  d'enregistrements musicaux selon le type de produit* (clé : `volume_musique`).
- Parts QC musique : tableau 4153 (voir repère 1).
- Cinéma : **tableau 2736** *Indicateurs des résultats d'exploitation des établissements
  cinématographiques* + **tableau 3059** *Résultats d'exploitation selon le pays d'origine
  des films* (clés : `indicateurs_cinema`, `cinema_pays`).

**Période.** Annuelle.

**Baseline 2025.** À calculer pour chaque canal à partir des données ISQ 2025.

**Direction « sovereignty gain ».** *C_c* en hausse, canal par canal.

**Limites.**
- Pondération multiplicative — un canal en déclin structurel (support physique :
  12,3 M albums en 2002, 1,1 M en 2025) peut faire chuter le repère même si la part
  québécoise progresse. Lecture nécessairement canal par canal.
- La comparabilité 2024 → 2025+ sur les albums physiques est affectée par le
  changement de méthodologie Luminate Data (29 décembre 2023).

---

## Repère 4 — Indice d'angle mort

**Concept.** Part de la matrice UNESCO 2025 (4 capitaux × 3 étapes) effectivement
couverte par la statistique culturelle publique québécoise. Mesure l'efficacité
indirecte de l'apparat de mesure — en particulier des recommandations 25-26 du
Comité-conseil 2024 sur le partage de données par les plateformes.

**Définition opérationnelle.**
`A = nb_cellules_couvertes / 12`
où une cellule est dite *couverte* lorsqu'au moins un indicateur publié par l'ISQ,
l'OCCQ, le MCC ou le CRTC en propose une mesure publique.

Les 12 cellules sont l'intersection :
- 4 capitaux UNESCO : économique, naturel, humain, social.
- 3 étapes : Création-Production ; Diffusion-Consommation ; Préservation-Transmission.

**Règle de comptage** (v1.1.0). Binaire. Une cellule est *couverte* si elle dispose
d'un indicateur statistique au sens strict (état **plein**, ✓) **ou** d'un indicateur
partiel / d'un proxy explicitement identifié (état **partiel**, ⚠). La qualité de la
couverture est documentée dans la matrice annexée mais n'entre pas dans le numérateur —
conformément à la limite déjà reconnue ci-dessous (« qualité non incluse »).

**Source.** Recensement manuel annuel des publications ISQ / OCCQ / MCC / CRTC, mené
par l'Observatoire au 1ᵉʳ mars.

**Période.** Annuelle.

**Baseline 2025.** Matrice initiale figée le 2026-05-25, détail en **Annexe R4**
(*infra*). Compte : **8 cellules couvertes sur 12** (*A* = 0,667), dont une seule
pleinement couverte (Économique × Diffusion-Consommation, instrumentée par la
triade de l'article 33 de la Loi 109) et sept couvertes partiellement. Quatre
cellules ✗ non couvertes : la colonne *Naturel* en création-production et
diffusion-consommation, *Social × Création-Production*, *Social × Préservation-Transmission*.

**Direction « sovereignty gain ».** *A* augmente.

**Limites.**
- Qualité non incluse — une cellule couverte par un indicateur faible compte autant
  qu'une cellule bien instrumentée.
- Définit l'instrumentation, pas le phénomène. À ne jamais lire seul.

---

## Repère 5 — Volume d'œuvres québécoises rendues publiques

**Concept.** Output créatif québécois, mesuré indépendamment de la statistique salariée
EERH (qui exclut les travailleurs autonomes — voir annexe 5b).

**Définition opérationnelle.** Trois volumes annuels :
- *O_alb* = albums québécois sortis dans l'année.
- *O_film* = films québécois produits dans l'année.
- *O_liv* = livres québécois publiés dans l'année.

**Sources.** À identifier précisément lors de la première mesure :
- Albums : ADISQ ; Luminate Data ; ISQ / OCCQ si publication équivalente.
- Films : ISQ, *Indicateurs des résultats d'exploitation des établissements
  cinématographiques* ; SODEC ; Téléfilm Canada.
- Livres : ISQ, *Statistiques sur l'édition de livres* / OCCQ ; BAnQ (dépôt légal).

**Définitions « œuvre québécoise »** (v1.1.0 — alignement sur les conventions
institutionnelles existantes, pas de définition maison) :
- **Musique** : critères ADISQ d'interprète québécois.
- **Cinéma** : grille SODEC de qualification du film québécois. *À préciser
  avant gel formel* : choisir explicitement entre la grille du crédit d'impôt
  remboursable (section dédiée du règlement) et la grille du palmarès québécois,
  les deux n'étant pas identiques.
- **Livre** : convention OCCQ de l'édition lorsqu'elle existe publiquement ;
  à défaut, éditeur québécois selon le dépôt légal BAnQ. *À confirmer dans la
  documentation méthodologique OCCQ avant gel formel.*

Exclusions à documenter explicitement à la première mesure : auto-édition non
déposée, auteurs québécois publiés par des maisons étrangères, et tout cas
limite identifié.

**Période.** Annuelle.

**Baseline 2025.** À confirmer après identification définitive des sources (action de
mise en service du repère).

**Direction « sovereignty gain ».** Maintien ou augmentation des trois volumes.

**Limites.**
- Mesure l'output, pas la survie économique des créateurs. Voir repère 5b.
- Définition de « québécois » à figer formellement pour chaque support (lieu de
  production ? résidence du créateur ? maison d'édition ? ADISQ ?). Choix à
  documenter dans la première mesure.

---

## Annexe 5b — Chantier de recherche : indicateur dual EERH ↔ noyau créatif

**Statut.** En chantier de recherche. Pas encore opérationnel.

**Concept.** Confronter la statistique officielle de l'emploi culturel (EERH, qui
n'inclut que les travailleurs salariés porteurs de T4) à une estimation du noyau
créatif effectif (incluant les autonomes invisibles à l'EERH). L'*écart* entre les
deux mesures est le résultat.

**Cible.** Chronique 03 ou 04 de l'Observatoire — la première publication à dire
publiquement, données à l'appui, ce que la statistique culturelle québécoise ne
mesure pas.

**Pistes de sources pour le second terme.**
- Déclarations fiscales des travailleurs autonomes (Revenu Québec, Statistique Canada,
  si décompositions sectorielles disponibles).
- Créateurs avec au moins une œuvre déposée à BAnQ (dépôt légal) sur l'année.
- Membres ADISQ / UNEQ / SARTEC / autres associations professionnelles.

**Posture éditoriale.** Annoncer l'existence du chantier dans toute publication
mentionnant les cinq repères. La phrase éditoriale : *« cinq repères, dont quatre
déjà mesurables et un en construction parce que la statistique publique ne le
mesure pas encore — ce qui est en soi un résultat »*.

---

## Annexe R4 — Matrice initiale (état au 2026-05-25)

États : **✓ plein** (indicateur statistique au sens strict), **⚠ partiel**
(indicateur partiel, sous-ensemble, ou proxy explicitement identifié),
**✗ absent** (aucune mesure publique connue dans le périmètre ISQ / OCCQ /
MCC / CRTC). Règle de comptage : ✓ et ⚠ comptent (binaire) ; ✗ ne compte pas.

| Capital × Étape | État | Source |
|---|---|---|
| Économique × Création-Production | ⚠ | Indicateurs des résultats d'exploitation des établissements cinématographiques (ISQ **2736**) — composante production |
| Économique × Diffusion-Consommation | ✓ | Triade Loi 109 art. 33 — ISQ **4153** / **2620** / **2140** / **3059** / **2342** / **3171** |
| Économique × Préservation-Transmission | ⚠ | Nombre d'établissements culturels (ISQ **929**) — sous-ensemble institutions muséales |
| Naturel × Création-Production | ✗ | — |
| Naturel × Diffusion-Consommation | ✗ | — |
| Naturel × Préservation-Transmission | ⚠ | Registre du patrimoine culturel (MCC) — couverture indirecte par inventaire patrimonial |
| Humain × Création-Production | ⚠ | Emplois salariés EERH (ISQ **2576**) — salariés seulement, autonomes invisibles à la statistique |
| Humain × Diffusion-Consommation | ⚠ | Emplois salariés EERH (ISQ **2576**) — même limite |
| Humain × Préservation-Transmission | ⚠ | Statistiques des bibliothèques publiques du Québec (MCC / BAnQ) — proxy de transmission culturelle |
| Social × Création-Production | ✗ | — |
| Social × Diffusion-Consommation | ⚠ | Principaux indicateurs en culture par région (ISQ **4850**) — proxy faible, ne couvre pas le capital social au sens strict |
| Social × Préservation-Transmission | ✗ | — |

**Compte.** 1 ✓ plein + 7 ⚠ partiels = **8 cellules couvertes / 12** ; *A* = 0,667.
Cellules ✗ (4) : la colonne *Naturel* en création-production et diffusion-consommation
(absence d'instrumentation statistique du capital patrimonial-naturel dans les
deux premières étapes), *Social × Création-Production* et *Social × Préservation-Transmission*
(absence d'instrumentation du capital social hors de l'angle régional).

**Toute modification ultérieure de cette annexe** — reclassement d'une cellule,
ajout ou retrait d'une source, changement d'état d'un proxy — **exige un bump de
version du protocole et une entrée au journal des révisions**, conformément à la
discipline du gel. Le dériveur `observatoire-pipeline/src/derive.py` porte cette
matrice en dur, encodée dans la constante `MATRICE_R4` ; toute modification de
la matrice doit s'accompagner d'une mise à jour synchrone du dériveur et de
`tests/test_derive_reperes.py`.

---

## Journal des révisions

| Version | Date       | Modification                        |
|---------|------------|-------------------------------------|
| 1.0     | 2026-05-25 | Création initiale, 5 repères + 5b. |
| 1.0.1   | 2026-05-25 | Correction factuelle. Vérification croisée des numéros de tableau ISQ par lecture systématique des fichiers .xlsx sources (R1 = 4153 confirmé ; R2 = 2620 ; R3 sources = 3171, 2140, 2736, 3059). Champ `isq_table_id` ajouté à `sources.yaml`. Faux positif détecté pour `evolution_stats` (« 051 » provenait d'une référence interne à *Statistique Canada CANSIM Tableau 051-0001*, pas de la fiche permanente ISQ qui est 3171). |
| 1.1.0   | 2026-05-26 | Révision mineure. R4 : règle de comptage binaire explicitée (✓ et ⚠ couvrent, ✗ ne couvre pas) ; matrice initiale figée en *Annexe R4* (8/12, dont 1 ✓ et 7 ⚠) ; intégration des sources MCC (Registre du patrimoine culturel) et MCC/BAnQ (bibliothèques publiques) au périmètre du recensement, ce qui reclasse Naturel × Préservation-Transmission et Humain × Préservation-Transmission en ⚠. R5 : alignement explicite des définitions « œuvre québécoise » sur les conventions institutionnelles externes (ADISQ, SODEC, OCCQ/BAnQ) plutôt que définition maison. Dériveur des repères implémenté (`src/derive.py`, `tests/test_derive_reperes.py`). |

---

*Document gelé le 2026-05-25. Toute révision future créera une version 1.x distincte
avec note de motivation. — Observatoire de la souveraineté culturelle numérique.*
