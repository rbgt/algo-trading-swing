# Suivi de tendance sur plusieurs jours : règles écrites avant tout test

> Règles commitées **avant tout test**. Elles ne changent plus au vu des résultats.

## 1. Pourquoi le suivi de tendance

Les recherches sur l'intraday (repo [algo-trading-intraday](https://github.com/rbgt/algo-trading-intraday)) n'ont trouvé
aucun avantage : 7 stratégies techniques et fondamentales, plus de 1 700 jeux de réglages et des tests contre le hasard.
Deux raisons principales : le coût pèse lourd face aux petits mouvements intraday, et l'information est intégrée en
quelques minutes.

Le **suivi de tendance sur plusieurs jours ou semaines** est l'approche la mieux documentée sur le long terme (Moskowitz,
Ooi et Pedersen, *Time series momentum*, 2012 ; les fonds « CTA »). On l'explique par des comportements persistants :
réactions lentes à l'information, puis suivi des tendances par les autres acteurs. Les mouvements visés font des
centaines de pips : le spread devient négligeable, mais le **coût de portage de nuit (swap)** devient important.

**Exception aux règles de Rick, pour la recherche** : les positions sont gardées la nuit et le week-end, et il n'y a
plus de fenêtre horaire. Le risque de 1 % par trade et le levier maximal (1:5, 1:2 pour le BTC) restent en place.

## 2. Cadre commun

- **Instruments** : EUR/USD, GBP/USD, USD/CHF (HistData, depuis 2014) et BTC/USD (BTC/USDT de Binance, depuis août 2017).
- **Bougies journalières** : la journée se termine à 17h à New York (bougie « D » de TradingView). Le BTC a une bougie
  chaque jour, week-end compris.
- **Signal** sur la clôture journalière, **entrée** à la première bougie M1 qui suit (ouverture de la séance suivante).
- **Sorties** résolues en M1 : stop compté d'abord en cas d'ambiguïté, gap exécuté à l'ouverture.
- **Taille** : 1 % de risque sur le stop initial, levier plafonné, capital de 100 € par instrument, composé.
- **Coûts de base** : spread de base de l'instrument (1,1 pip pour EUR/USD et GBP/USD, 1,5 pip pour USD/CHF, 0,2 % pour
  le BTC) **plus le swap** à chaque passage de 17h à New York : 3 %/an du nominal pour le forex (triple le mercredi),
  20 %/an pour le BTC (chaque nuit).
- **Coûts de stress** : le niveau de spread le plus élevé de l'instrument, et le swap × 2.
- Une seule position à la fois par instrument.

## 3. Stratégie S1 : cassure de Donchian

1. **Achat** si la clôture dépasse le plus haut des **55** bougies journalières précédentes. **Vente** si elle passe sous
   le plus bas des 55 précédentes.
2. **Stop initial** : 2 × ATR20 journalier (calculé à la clôture du signal), depuis le prix d'entrée.
3. **Sortie** : pour un achat, à la première clôture sous le plus bas des **20** bougies précédentes (symétrique pour une
   vente), à l'ouverture de la séance suivante. Pas d'objectif.

## 4. Stratégie S2 : momentum de série temporelle

1. À la clôture de la **dernière bougie journalière de chaque mois** : performance sur **12 mois**, c'est-à-dire de la
   clôture de fin de mois d'il y a 12 mois à celle d'aujourd'hui.
2. **Achat** si elle est positive, **vente** si elle est négative. Entrée à l'ouverture de la séance suivante.
3. **Sortie** à l'ouverture de la séance qui suit la fin du mois suivant. On recalcule alors, et on reprend une position
   pour un mois. Chaque mois est compté comme un trade, qui paie donc le spread : hypothèse prudente.
4. **Stop de protection** : 3 × ATR20 journalier.

## 5. Critères de réussite (fixés à l'avance)

Période de conception : **2015–2021** (BTC à partir de septembre 2017, après le préchauffage des indicateurs).
Les trades des 4 instruments sont **réunis**. Une stratégie est retenue **seulement si toutes les conditions sont remplies** :

1. R moyen net (coûts de base, swap compris) **≥ +0,05**.
2. **t-stat ≥ 2,0** du R par trade.
3. R moyen **positif sur au moins 3 instruments sur 4**.
4. Au moins **4 années positives sur 7** (somme des R de l'année).
5. R moyen encore **positif avec les coûts de stress**.
6. **Test contre le hasard** : les mêmes trades avec un sens tiré à pile ou face, 10 000 fois. Moins de **5 %** des tirages
   doivent faire aussi bien.
7. Toutes les **variantes** de la section 6 ont un R moyen réuni **positif**.

En plus, à titre d'information : Monte-Carlo sur les paramètres (jeux de réglages tirés au hasard).

**Validation finale** (une seule fois, uniquement pour une stratégie qui remplit les 7 critères) : du 1ᵉʳ janvier 2022 à
la fin des données. Elle est réussie si le R moyen réuni est **positif** et que le R moyen est **positif sur au moins
3 instruments sur 4**.

## 6. Variantes de sensibilité (fixées à l'avance)

| Stratégie | Réglage | Base | Variantes |
|---|---|---|---|
| S1 | Canal d'entrée (bougies) | 55 | 20 · 100 |
| S1 | Canal de sortie (bougies) | 20 | 10 · 40 |
| S1 | Stop initial (× ATR20) | 2 | 1,5 · 3 |
| S2 | Période de la performance (mois) | 12 | 3 · 6 |
| S2 | Stop de protection (× ATR20) | 3 | 2 · 5 |

## 7. Limites connues

- **Écart de taux ignoré** : en réalité, le swap dépend de la différence de taux entre les deux devises (le « carry »).
  Un swap fixe de 3 %/an dans les deux sens est une simplification prudente.
- **Peu de trades** pour S1 (quelques-uns par an et par instrument) : c'est pour ça que les trades des 4 instruments sont
  réunis et qu'on exige une t-stat.
- **Chaque instrument est simulé avec son propre compte de 100 €.** On n'étudie pas ici un portefeuille avec plusieurs
  positions simultanées.

## 8. Résultats (2015–2021) : **les deux stratégies sont rejetées**

Tests lancés après le commit des règles (87a4fa6) et du code (647c346), sans modification.

### S1, cassure de Donchian

| Critère | Valeur | Rempli |
|---|---|---|
| 1. R moyen ≥ +0,05 | +0,161 | ✅ |
| 2. t-stat ≥ 2,0 | 0,33 | ❌ |
| 3. positif sur ≥ 3 instruments sur 4 | 1/4 | ❌ |
| 4. ≥ 4 années positives sur 7 | 4/7 | ✅ |
| 5. positif avec coûts de stress | −0,072 | ❌ |
| 6. hasard qui fait mieux < 5 % | 33,9 % | ❌ |
| 7. toutes les variantes positives | min. −0,108 | ❌ |

Par instrument (trades, R moyen) : **BTC 17 trades, +4,35 R** ; EUR/USD 31, −0,31 ; GBP/USD 34, −0,45 ; USD/CHF 34, −0,90.
Le swap coûte en moyenne 0,22 R par trade. Le R positif réuni vient **entièrement du BTC**, surtout de la tendance de 2020 (+44,9 R).

### S2, momentum de série temporelle

| Critère | Valeur | Rempli |
|---|---|---|
| 1. R moyen ≥ +0,05 | −0,121 | ❌ |
| 2. t-stat ≥ 2,0 | −2,14 | ❌ |
| 3. positif sur ≥ 3 instruments sur 4 | 1/4 | ❌ |
| 4. ≥ 4 années positives sur 7 | 1/7 | ❌ |
| 5. positif avec coûts de stress | −0,219 | ❌ |
| 6. hasard qui fait mieux < 5 % | 75,5 % | ❌ |
| 7. toutes les variantes positives | min. −0,149 | ❌ |

Par instrument : BTC 39 trades, +0,12 R ; EUR/USD 82, −0,13 ; GBP/USD 82, −0,11 ; USD/CHF 82, −0,23.

### Monte-Carlo sur les paramètres (200 jeux de réglages par stratégie)

- **Momentum** : R réuni médian de −0,10, **0 %** des jeux positifs.
- **Donchian** : R réuni médian de −0,07, 38 % des jeux positifs. Mais **0 %** des jeux sont positifs sur les trois paires
  de devises (R médian : EUR/USD −0,42, GBP/USD −0,57, USD/CHF −1,05), alors que le **BTC a un R médian de +3,47** par trade.

**La validation finale n'a pas lieu** : aucune stratégie ne remplit les 7 critères.

**Ce qu'on apprend** : sur 2015–2021, le suivi de tendance ne marche **pas sur les paires de devises** (EUR/USD, GBP/USD et
USD/CHF sont restés dans des fourchettes, et le swap coûte cher). En revanche, il marche **sur le BTC** quel que soit le
réglage, grâce à ses tendances très longues. Cette observation est une **nouvelle hypothèse**, née de ces données : elle est
écrite et testée à part (section 9), sur la période 2022 → fin des données, à laquelle personne n'a encore touché.
