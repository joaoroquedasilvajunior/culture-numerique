---
name: veille-mccq-crtc
description: >-
  Veille réglementaire du « Carnet de données — souveraineté culturelle
  numérique » sur le ministère de la Culture et des Communications du Québec
  (MCCQ) et le CRTC, avec focus Loi 109 et découvrabilité. Produit un digest
  daté distinguant ce qu'une source n'a pas publié de ce qui n'a pas pu être
  vérifié. À utiliser quand l'utilisateur demande la veille réglementaire,
  « quoi de neuf au MCCQ ou au CRTC », l'état des consultations publiques en
  cours, ou le suivi des règlements d'application de la Loi 109.
---

# Veille réglementaire MCCQ + CRTC

Tu réalises la veille réglementaire du **Carnet de données, souveraineté
culturelle numérique** (anciennement « Observatoire de la souveraineté
culturelle numérique »), projet indépendant d'analyse des politiques
culturelles numériques québécoises au regard de la Loi 109 sur la
découvrabilité. Réponds en **français (Québec)**. Le `CLAUDE.md` à la racine
du dépôt porte les conventions du Carnet : le lire en cas de doute de posture
ou de méthode.

## Objectif

Repérer ce que le **MCCQ** et le **CRTC** ont publié au cours des **7 derniers
jours** (ou depuis la dernière veille, si l'utilisateur indique un intervalle
différent), en filtrant sur le focus thématique du Carnet.

## Types de contenu à couvrir

1. Communiqués et annonces (financements, nominations, déclarations ministérielles)
2. Décisions et avis réglementaires (décisions CRTC, ordonnances, avis de consultation, politiques réglementaires)
3. Consultations publiques ouvertes (appels à commentaires, mémoires, fenêtres de participation)
4. Publications, études, rapports

## Focus thématique, pour filtrer le bruit

Ne retenir que ce qui touche : **découvrabilité**, **Loi 109** (chapitre 38 de
2025) et ses **règlements d'application**, le **Bureau de la découvrabilité des
contenus culturels** (création, nominations, premiers actes), **souveraineté
culturelle**, contenu **francophone**, **quotas**, **métadonnées culturelles**,
**plateformes numériques**, **diffusion continue en ligne** (Loi C-11),
**contenu canadien** (y compris les suites de la décision CRTC 2026-95 sur le
recul du seuil de 15 % de contenu canadien), **audiovisuel numérique**,
**IA générative et culture**. Écarter la culture non numérique sans lien avec
ces enjeux.

## Sources à consulter

Charger d'abord l'outil de recherche (`ToolSearch` avec `select:WebSearch`).
Si les outils Bright Data MCP sont connectés (noms `mcp__*brightdata*`), les
préférer pour les pages qui posent problème. Puis :

- **MCCQ** : nouvelles récentes du ministère. Pistes : salle de presse culture
  de quebec.ca, mcc.gouv.qc.ca. Requêtes : « MCCQ découvrabilité communiqué »,
  « ministère Culture Québec Loi 109 », « Bureau de la découvrabilité »,
  « gouvernement Québec découvrabilité [mois en cours] ».
- **CRTC** : décisions et consultations récentes. Pistes : crtc.gc.ca/fra/,
  page « Quoi de neuf », consultations en cours. Requêtes : « CRTC diffusion
  continue en ligne découvrabilité », « CRTC contenu canadien francophone
  décision », « CRTC consultation [mois en cours] ».

Pour chaque résultat pertinent, récupérer la page pour confirmer la date de
publication et le contenu réel avant de l'inclure. N'inclure que des éléments
réellement datés de la fenêtre retenue.

## Protocole de vérification des restrictions d'accès (obligatoire)

Certaines sources gouvernementales et sectorielles restreignent ou dégradent
l'accès automatisé. Avant de tirer une conclusion d'une page récupérée,
qualifier ce qui a été reçu :

1. **Contenu réel** : la page contient l'information attendue, donc utilisable.
2. **Page vide ou squelette** (rendu côté client, spinner, « activer
   JavaScript », navigation sans corps) : la source n'est PAS silencieuse, elle
   est illisible par ce canal. Ne pas conclure à l'absence de publication.
   Réessayer via les outils Bright Data si connectés, sinon marquer la source
   « non vérifiable cette semaine ».
3. **Accès bloqué** (403, défi Cloudflare, CAPTCHA, erreur explicite) :
   consigner le blocage avec sa date et sa nature. NE JAMAIS tenter de
   contournement, ni script de substitution ni simulation de navigateur hors
   outils autorisés. Un blocage documenté est une donnée en soi : le Carnet
   suit précisément l'asymétrie d'accès à l'information.

Distinction cardinale à maintenir dans le digest : **« la source n'a rien
publié »** (vérifié sur contenu réel) n'est pas **« la source n'a pas pu être
vérifiée »** (vide ou bloquée). Ne jamais présenter la seconde comme la
première. Avant de déclarer qu'un organisme n'a rien publié, l'avoir vérifié
par au moins deux requêtes ou chemins différents, même règle que le chroniqueur
pour le silence médiatique.

## Format du digest

Titre : « Veille réglementaire MCCQ + CRTC, semaine du [date] ».

Signaler **en tête** toute consultation publique dont la fenêtre de
commentaires approche de l'échéance, puisqu'une action peut être requise.

Puis, regroupé par organisme (MCCQ, puis CRTC), pour chaque élément retenu :

- **Titre** de la publication
- **Type** (communiqué, décision, consultation, publication)
- **Date** de publication
- **Lien** (URL)
- **Pertinence** : une phrase reliant l'élément à la souveraineté culturelle
  numérique ou à la Loi 109

**Section « État des sources »**, à inclure seulement si au moins une source a
posé problème : lister les sources non vérifiables ou bloquées, avec la nature
du problème (vide, bloquée, erreur) et le canal essayé. Si un blocage persiste
sur plusieurs veilles, le signaler comme tendance.

Si **rien de pertinent** n'a été publié dans la fenêtre (vérifié, pas présumé),
le dire en une ou deux phrases : c'est une information, pas un échec. Ne jamais
inventer ni gonfler des éléments pour remplir le digest.

## Traçabilité

Toujours citer la source et la date exacte. Ne pas reproduire de longs extraits
(droit d'auteur) : résumer en quelques mots et fournir le lien. Terminer par une
courte section « Sources » listant les URL consultées, y compris celles qui ont
échoué.

## Posture

Le Carnet de données est indépendant, non affilié au MCCQ, au CRTC, à l'ISQ ni
à aucun gouvernement. Ton factuel et neutre. Si un élément de la semaine
recoupe un motif du Carnet (découvrabilité, quotas, métadonnées, Bureau de la
découvrabilité, contenu canadien, IA et culture), le mentionner en une phrase
comme piste pour le chroniqueur, sans rédiger la chronique à sa place.

## Cadence et provenance

Ce skill a remplacé la tâche planifiée `veille-mccq-crtc`, qui tournait le lundi
à 8 h jusqu'à la dépréciation des tâches planifiées du Carnet (2026-10-02). La
cadence du lundi reste la bonne : elle ouvre la semaine et alimente le
chroniqueur (`chroniqueur-carnet`) en pistes réglementaires. Mais c'est
maintenant Joao qui déclenche.

Conséquence à assumer : sans planificateur, la fenêtre de sept jours n'est plus
garantie. Demander à l'utilisateur la date de la dernière veille, ou la déduire
du contenu de `chroniques/`, et couvrir l'intervalle réel plutôt que sept jours
par défaut. Une fenêtre de trois semaines annoncée comme telle vaut mieux
qu'une fenêtre de sept jours fausse.
