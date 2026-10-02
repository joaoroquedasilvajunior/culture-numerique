# Carte des sources du pipeline (24 sources, état juillet 2026)

Racine du projet : dossier « Culture Québec en donnée ». Le manifeste
complet est `observatoire-pipeline/sources.yaml` (labels, URLs permanentes,
notes méthodologiques par source) — le lire pour tout détail.

## Familles de sources

**Consommation et marché (ISQ/OCCQ)** : part des interprètes QC dans la
consommation musicale (hebdo), volume musique par produit, palmarès top 20,
cinéma (pays d'origine hebdo + annuel, langue de projection, classement,
indicateurs depuis 1975), livres neufs (mensuel + par point de vente),
livres numériques (annuel 2014-2025, tableau 3408), établissements
culturels, évolution de statistiques clés (2002-2025).

**Emploi et rémunération** : EERH mensuel désaisonnalisé + annuel
2001-2025 (tableau ISQ 2576, SCIAN 2022), rémunérations EERH via CANSIM
14-10-0223.

**Grille AI-exposure (3 lentilles)** : 1a demande experte (StatCan
C-AIOE, Canada), 1b demande marché (CANSIM 14-10-0442 postes vacants,
Québec), 2 usage révélé (Anthropic Economic Index, Canada). Plus la
lentille 3 améliorée (ratio rémunération/effectifs).

**Écosystème subventionné (CALQ)** : théâtre/cirque (série 1994-2024 avec
productions, représentations, spectateurs QC/hors-QC), diffuseurs
pluridisciplinaires (2016-2024), arts visuels/numériques (2017-2024).
Alimente le repère R6.

**Présence catalogue (sources ouvertes)** : MusicBrainz artistes QC
(9 731 artistes, CC0, récolte via moissonneur_musicbrainz.py) et Deezer
(1 203 artistes, nb_fan, via enrichir_deezer.py).

## Chiffres de référence à jour (juillet 2026)

- Iceberg découvrabilité : 9 731 artistes au catalogue → 3 852 avec lien
  streaming → 1 943 avec lien Spotify → 1 203 mesurés Deezer → 1 seul
  dans le top 20 ISQ sur 7 semaines (Les Cowboys Fringants).
- Longue traîne Deezer : médiane 185 fans, top 1 % capte 75,8 % des fans,
  41,6 % des artistes sous 100 fans.
- Livre : verdict « addition » papier+numérique 2014-2024 (papier +12,7 %,
  numérique +52,7 %) mais numérique < 2 % du marché en valeur ; pic 2020.
- R6 CALQ 2023-2024 : 214 organismes, 13 379 représentations, 4,19 M
  spectateurs, 40 % d'aide publique (58 % QC / 17 % Canada / 24 %
  municipal), 17 % de spectateurs hors-Québec au théâtre.
- AI-exposure : jeu vidéo ~75 % de tâches à potentiel de substitution
  (HE_LC) selon StatCan/C-AIOE.

## Contexte réglementaire

Loi 109 (sanctionnée 12 déc. 2025) : découvrabilité, Bureau de la
découvrabilité, quotas, métadonnées. Directive fédérale juin 2026 :
recul CRTC sur les 15 % CanCon (décision 2026-95). Chaîne politique
2014-2026 : PCNQ, Comité des sages 2016, Mission FR-QC 2020, Guide MCC
2021, Comité-conseil 2024, Stratégie 2025-2030.

## Pièges connus

- Les fichiers ISQ contiennent parfois des numéros CANSIM (StatCan) qui
  ressemblent à des numéros de fiche ISQ : valider par l'URL permanente.
- round() Python fait du banker's rounding.
- Lentilles 1a et 2 sont Canada national, 1b est Québec : le signaler
  dans toute comparaison.
- Taux de liens MusicBrainz = plancher de complétude des métadonnées,
  pas présence réelle sur plateformes.
