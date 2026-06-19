# Grille de vérification — Baselines 2025 des repères

**Objet.** Confirmer les valeurs annuelles 2025 (année de référence pré-règlement,
Protocole §« Année de référence ») pour basculer les repères mesurables de
`provisional: true` à `provisional: false` dans le dériveur.

**Mode d'emploi.** Pour chaque repère, ouvrir la fiche ISQ, repérer la valeur
**annuelle 2025** (et non le YTD 2026 courant), la consigner dans la colonne
« Valeur 2025 confirmée », puis dater la vérification. Une fois la grille remplie,
me la transmettre : je mets à jour `src/derive.py` et `tests/test_derive_reperes.py`
pour figer ces valeurs.

**Distinction cruciale.** Les tableaux hebdomadaires (4153, 2620, 2140, 3059) se
réinitialisent chaque année. Les fichiers actuels dans `Données Québec/` montrent
le **cumulatif YTD 2026**. Pour la baseline 2025, il faut la valeur **cumulative
de fin 2025** (dernière semaine publiée de 2025, typiquement semaine 52) — ce qui
exige en général de récupérer la version archivée de fin 2025 du tableau, ou de
lire la ligne 2025 si le tableau conserve l'historique. Les tableaux à séries
annuelles (3171, 2736) contiennent déjà 2025.

---

## R1 — Écart de découvrabilité

**Source.** ISQ tableau **4153** — `https://statistique.quebec.ca/fr/produit/tableau/4153`
**Quoi lire.** Cumulatif annuel **2025** (dernière semaine de 2025), deux valeurs.

| Grandeur | YTD 2026 courant (référence) | **Valeur 2025 confirmée** | Date vérif. |
|----------|------------------------------|---------------------------|-------------|
| *p_str* — part streaming (%) | 6,9 % | ____________ | __________ |
| *p_alb* — part albums num. (%) | 24,5 % | ____________ | __________ |

**Calculs dérivés** (automatiques une fois p_str et p_alb confirmés) :
- *R* = p_alb / p_str
- *E* = p_alb − p_str (points de %)

**Note méthodo.** Lire la valeur *cumulative de fin 2025*, pas une semaine isolée.
Attention à la rupture de comparabilité Luminate Data (29 déc. 2023) si on remonte
avant 2024.

---

## R2 — Profondeur du catalogue (N₂₀)

**Source.** ISQ tableau **2620** — `https://statistique.quebec.ca/fr/produit/tableau/2620`
**Quoi lire.** Top 20 streaming **cumulatif 2025** ; compter les interprètes
québécois distincts.

| Grandeur | Cumul 2026 courant (référence) | **Valeur 2025 confirmée** | Date vérif. |
|----------|-------------------------------|---------------------------|-------------|
| *N₂₀* — interprètes QC distincts | 1 (Les Cowboys Fringants, rang 15) | ____________ | __________ |
| Liste des interprètes QC + rangs | — | ____________ | __________ |

**Note méthodo.** « Distinct » : un même interprète présent deux fois compte une
seule fois. Consigner la liste nominative pour traçabilité.

---

## R3 — Consommation québécoise absolue

Pondération `C_c = volume_total_2025 × part_QC_2025`, canal par canal.

### Canal streaming musical

**Volume total.** ISQ tableau **2140** (`volume_musique`) — cumulatif annuel 2025.
**Part QC.** Tableau 4153 (p_str 2025, voir R1).

| Grandeur | YTD 2026 courant (référence) | **Valeur 2025 confirmée** | Date vérif. |
|----------|------------------------------|---------------------------|-------------|
| Volume total streaming (k écoutes) | 4 829 409,6 | ____________ | __________ |
| Part QC streaming (%) | 6,9 % | (= R1 p_str) | __________ |

### Canal albums numériques téléchargés

| Grandeur | YTD 2026 courant (référence) | **Valeur 2025 confirmée** | Date vérif. |
|----------|------------------------------|---------------------------|-------------|
| Volume total albums num. (unités) | _à extraire_ | ____________ | __________ |
| Part QC albums num. (%) | 24,5 % | (= R1 p_alb) | __________ |

### Canal cinéma (recettes québécoises de films québécois)

**Recettes totales.** ISQ tableau **2736** (`indicateurs_cinema`) — série annuelle, valeur **2025**.
**Part QC.** Tableau **3059** (`cinema_pays`) — part du Québec dans le box-office, **2025 annuel**.

| Grandeur | Référence | **Valeur 2025 confirmée** | Date vérif. |
|----------|-----------|---------------------------|-------------|
| Recettes totales cinéma 2025 ($) | série annuelle 2736 | ____________ | __________ |
| Part QC box-office 2025 (%) | YTD 2026 : 4,7 % | ____________ | __________ |

**Note méthodo.** Le cinéma est le canal le plus délicat : `indicateurs_cinema`
est annuel mais `cinema_pays` est hebdomadaire/YTD. Pour la baseline 2025, il faut
la part QC *annuelle 2025*, pas le YTD 2026. Vérifier que les deux portent sur la
même définition (recettes vs assistance).

---

## R4 — Indice d'angle mort

**Aucune vérification ISQ requise.** R4 est gelé par le protocole (matrice
2026-05-25, 8/12), `provisional: false` dès maintenant. Ne rien remplir ici.

---

## R5 — Volume d'œuvres

**Hors périmètre de cette grille.** R5 reste en chantier tant que ses sources
(ADISQ, SODEC, OCCQ/BAnQ) ne sont pas identifiées et figées. Pas de baseline 2025
à confirmer à ce stade.

---

## Une fois la grille remplie

1. Me transmettre les valeurs confirmées + dates de vérification.
2. Je mets à jour `src/derive.py` :
   - bascule `provisional: false` sur R1, R2, R3 pour `annee=2025` ;
   - fige les valeurs 2025 comme baseline de référence (distincte du YTD vivant).
3. Je mets à jour `tests/test_derive_reperes.py` avec les valeurs 2025 attendues.
4. Mise à jour du Protocole (§Baseline de chaque repère) + entrée au journal des
   révisions (probable v1.2.0 — confirmation des baselines = redéfinition mineure
   du statut des repères).
5. `./maj_dashboard.sh` + push : les badges « Lecture YTD » des cards R1-R3
   deviennent « Gelé 2025 ».

---

*Document de travail — Carnet de données — souveraineté culturelle numérique.
Préparé le 2026-05-26 pour la tâche #26 (confirmation des baselines 2025).*
