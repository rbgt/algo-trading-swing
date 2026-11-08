# algo-trading-swing

Recherche de stratégies **sur plusieurs jours** (suivi de tendance) sur EUR/USD, GBP/USD, USD/CHF et BTC/USD.

Ce repo utilise le paquet `fxbt` du repo [algo-trading-intraday](https://github.com/rbgt/algo-trading-intraday) comme
bibliothèque : données M1 (HistData, Binance) avec la correction du fuseau horaire, moteur de backtest (sorties résolues en
M1, levier, coûts, **swap de nuit**), mesures et Monte-Carlo. Les recherches intraday (8 stratégies, aucune retenue) sont
dans ce repo-là.

## Conclusion (novembre 2026) : recherche arrêtée

**Aucune stratégie testée n'a d'avantage exploitable sur le forex**, ni en intraday ni en swing. La recherche sur le
forex est arrêtée.

| Approche | Repo | Résultat sur 2015–2021 (R moyen net par trade) |
|---|---|---|
| A. EMA Breakout (M5 / M15) | intraday | −0,18 (EUR/USD), −0,08 (GBP/USD) |
| B. London Breakout (cassure de la zone asiatique) | intraday | −0,11, −0,04 |
| C. Contre-tendance (retour à la moyenne journalière) | intraday | −0,03, −0,00 |
| D et D2. Breakout Price Action (H4 / H1 / M5) | intraday | de −0,27 à +0,05, variantes négatives |
| E. Fixing de fin de mois | intraday | −1,7 pip par trade, t = −0,70 |
| F. Surprise macro (annonces économiques) | intraday | −0,05, −0,04, R brut négatif |
| G. Smart Money Concepts (sweep, CHoCH, FVG ou order block) | intraday | de −0,41 à +0,05, ne bat pas le hasard |
| S1. Cassure de Donchian | swing | +0,16 réuni, mais seul le BTC est positif ; BTC seul en 2022–2026 : échec |
| S2. Momentum sur 12 mois | swing | −0,12 |
| S3 et S4. SMC en H4 (FVG ou order block) | swing | +0,015 et −0,21 |

Toutes ces approches ont suivi la même méthode : règles écrites et commitées avant le test, conception sur 2015–2021
seulement, coûts réalistes (spread, glissement, swap), sensibilité des réglages, Monte-Carlo sur les paramètres et
test contre le hasard (sens tiré à pile ou face). La période 2022 → 2026 n'a servi qu'une fois, pour le Donchian sur le BTC.

**Ce qu'on en retient**

- **Le problème est l'absence d'avantage brut, pas les coûts.** Sans aucun coût, la meilleure stratégie intraday
  gagne environ +0,06 R par trade. Un broker moins cher, des stops plus larges ou un filtre d'annonces ne changent
  aucun verdict.
- **C'est la logique des stratégies, pas le réglage.** Sur plus de 1 500 jeux de réglages tirés au hasard, aucun
  ne passe les critères.
- **Un résultat positif sur une seule paire est la signature du hasard.** Plusieurs stratégies gagnent sur GBP/USD
  et perdent sur EUR/USD, ou l'inverse.
- **Le capital ne change rien au verdict.** Avec 1 000 € au lieu de 100 €, les résultats en R sont identiques. Plus de
  capital rend les trades exécutables (micro-lot), pas rentables.
- **Le forex majeur est le marché le plus efficient.** Les avantages qui y existent demandent des moyens
  institutionnels (données, exécution, coûts) et une recherche à plein temps.

**Si la recherche reprend un jour**, les pistes les mieux documentées sont sur les **indices actions** (momentum
intraday sur le S&P 500 ou le Nasdaq, retour à la moyenne à court terme, effet de tournant de mois) ou dans
l'**investissement passif et multi-actifs**, avec la même méthode et les mêmes outils (`fxbt`).

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -e ../algo-trading-intraday pytest   # fxbt, depuis une copie locale (données partagées)
.venv/bin/pip install --no-deps -e .
```

Sans copie locale : `.venv/bin/pip install -e ".[dev]"` installe `fxbt` depuis GitHub. Il faut alors indiquer le dossier
des données avec la variable d'environnement `FXBT_DATA_DIR`, et le remplir avec les commandes de `fxbt`
(`download-histdata`, `import-histdata`, `download-binance`).

## Utilisation

```bash
.venv/bin/python -m swing backtest --strategy donchian                 # 4 instruments, 2015–2021
.venv/bin/python -m swing backtest --strategy tsmom --stress           # spread le plus élevé et swap × 2
.venv/bin/python -m swing evaluate --strategy donchian                 # les 7 critères fixés à l'avance
.venv/bin/python -m swing montecarlo --strategy tsmom --samples 200    # jeux de réglages tirés au hasard
.venv/bin/python -m swing final --strategy <retenue> --final           # validation unique, 2022 → fin des données
```

Les trades détaillés sont écrits dans `results/`. La colonne `swap_r` donne le coût de portage de chaque trade, en R.

## Stratégies et résultats

Règles, critères et résultats : [`docs/regles_tendance.md`](docs/regles_tendance.md). Les règles ont été commitées avant
tout test.

| Stratégie | Idée | 2015–2021 (4 instruments) | Verdict |
|---|---|---|---|
| `donchian` | Cassure du canal de 55 jours, sortie sur le canal de 20 jours, stop à 2 × ATR | +0,16 R, mais t = 0,33, positif seulement sur le BTC | Rejetée |
| `tsmom` | Sens de la performance sur 12 mois, revu chaque mois | −0,12 R, 1 année positive sur 7 | Rejetée |
| `smc` | SMC en H4 : sweep de la semaine précédente, CHoCH, entrée au retour dans le FVG | +0,015 R, t = 0,12, positif sur 1 instrument sur 4 | Rejetée |
| `smc_ob` | Comme `smc`, avec entrée sur l'order block (définition ICT) | −0,21 R, 0 instrument positif | Rejetée |
| Donchian sur le BTC seul | Nouvelle hypothèse, testée une fois sur 2022 → 2026 | +0,31 R avec les coûts de base, −0,02 R avec ceux de stress | Échec, de justesse |

**À retenir** : le suivi de tendance ne marche pas sur les paires de devises en 2015–2021. Il semble marcher sur le BTC,
mais le coût de portage des CFD (swap) absorbe la moitié du gain, et l'échantillon est trop petit (26 trades) pour conclure.

## Hypothèses de simulation

- **Bougies journalières** clôturées à 17h à New York. Signal à la clôture, entrée à la première bougie M1 qui suit.
- **Sorties résolues en M1** : stop compté d'abord en cas d'ambiguïté, gap exécuté à l'ouverture.
- **Swap** à chaque passage de 17h à New York : 3 %/an pour le forex (triple le mercredi), 20 %/an pour le BTC (chaque nuit).
  L'écart de taux entre devises (le « carry ») est ignoré : c'est une simplification prudente.
- **1 % de risque** par trade, levier 1:5 (1:2 pour le BTC), 100 € par instrument, capital composé. Chaque instrument a son
  propre compte : on n'étudie pas de portefeuille.

## Organisation

```
src/swing/
├── daily.py             # bougies journalières, heure de clôture et heure d'exécution suivante
├── strategies/          # donchian.py, tsmom.py, smc.py, smc_ob.py (même interface que fxbt.strategies.base)
├── evaluation.py        # périodes, coûts de stress, critères, test contre le hasard réuni, Monte-Carlo
└── __main__.py          # ligne de commande
docs/regles_tendance.md  # règles écrites avant le test, puis résultats
tests/
```
