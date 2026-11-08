# Stratégies S3 et S4 : Smart Money Concepts en swing (H4, liquidité de la semaine précédente)

> Règles validées et commitées **avant tout test**. Elles ne changent plus au vu des résultats.
> C'est le même schéma que la stratégie G du repo intraday (`docs/regles_smc.md`), transposé sur plusieurs jours :
> chasse aux stops du plus haut ou du plus bas de la **semaine précédente**, CHoCH en **H4**, puis entrée au
> retour dans le **FVG** (S3) ou dans l'**order block** (S4).
> Les choix marqués *(choix)* sont des valeurs que la méthode SMC ne fixe pas.

## 1. Définitions

| Notion | Définition automatique |
|---|---|
| **Bougies H4** | Agrégées depuis les M1, alignées sur l'ouverture de la séance forex (23h00, 03h00, 07h00… heure de Zurich). |
| **Semaine** | Les journées de trading (clôture à 17h à New York) du lundi au dimanche. En forex, la séance du dimanche soir appartient au lundi. |
| **Liquidité** | Le plus haut et le plus bas de la **semaine de trading précédente**. |
| **Sweep** (achat) | Une bougie H4 dont le plus bas passe sous le bas de la semaine précédente, suivie dans les **6 bougies H4** (en comptant celle du dépassement) d'une clôture H4 revenue au-dessus. Seul le **premier dépassement** de la semaine compte pour chaque côté. |
| **Extrême du sweep** | Le plus bas atteint depuis le premier dépassement, mis à jour jusqu'au CHoCH. |
| **Sommet de swing H4** | Plus haut que les `N` = 2 bougies H4 avant et après, connu à la clôture de la 2ᵉ bougie suivante. |
| **CHoCH** | Clôture H4 au-dessus du dernier sommet de swing confirmé avant l'extrême, dans les **30 bougies H4** (environ 5 jours) après le premier dépassement, et dans la même semaine. *(choix)* |
| **FVG** | Comme en intraday, sur les bougies H4 de la jambe impulsive (de l'extrême au CHoCH) ; on garde le dernier. Obligatoire pour S3 **et** S4. |
| **Order block** | La dernière bougie H4 baissière entre la bougie de l'extrême (incluse) et les 5 qui la précèdent (définition ICT, comme la version G-OB). |

La vente est le symétrique (sweep du haut de la semaine précédente).

## 2. Règles (achat ; la vente est le symétrique)

1. Sweep, CHoCH et FVG comme ci-dessus. Pour S4, il faut aussi un order block.
2. **Signal** : la première bougie M1 après la clôture du CHoCH dont le plus bas touche le **haut du FVG** (S3) ou le
   **haut de l'order block** (S4), dans les **12 bougies H4** (environ 2 jours) qui suivent le CHoCH. *(choix)*
3. **Entrée** à l'ouverture de la bougie M1 suivante.
4. **Stop** : extrême du sweep moins **0,1 × ATR14 journalier** (celui de la veille). *(choix : une marge en pips
   n'aurait pas de sens pour le BTC)*
5. **Objectif** : **2 R**.
6. **Sortie forcée** **14 jours** après l'entrée si ni le stop ni l'objectif n'est touché. *(choix)*
7. Une seule position à la fois par instrument. Risque 1 %, levier 1:5 (1:2 pour le BTC), swap compris.

Instruments, périodes, coûts et coûts de stress : ceux de `docs/regles_tendance.md` (EUR/USD, GBP/USD, USD/CHF, BTC/USD ;
conception sur 2015–2021, validation unique sur 2022 → fin des données).

## 3. Critères de réussite

Les **7 critères** de la section 5 de `docs/regles_tendance.md`, appliqués séparément à S3 et à S4
(R moyen réuni ≥ +0,05, t-stat ≥ 2, positif sur au moins 3 instruments sur 4, 4 années positives sur 7,
positif avec les coûts de stress, hasard qui fait mieux < 5 %, toutes les variantes positives).

## 4. Variantes de sensibilité (fixées à l'avance)

| Réglage | Base | Variantes |
|---|---|---|
| `N` (swings H4) | 2 | 1 · 3 |
| Délai de réintégration (bougies H4) | 6 | 3 · 12 |
| Délai du CHoCH (bougies H4) | 30 | 15 · 60 |
| Délai du retour dans la zone (bougies H4) | 12 | 6 · 24 |
| Objectif | 2 R | 1,5 R · 3 R |
| Sortie forcée | 14 jours | 7 · 28 jours |

## 5. Limites connues

- Avec 100 € (ou même 1 000 €), les stops H4 en forex font souvent plus de 50 pips : la position réelle serait sous le
  micro-lot. Comme pour S1 et S2, le verdict se fait en R, avec une taille non arrondie.
- Peu de setups attendus : au plus 2 par semaine et par instrument, avant les filtres.
