"""Stratégie S2 : momentum de série temporelle (règles : docs/regles_tendance.md).

- À la clôture de la dernière bougie journalière de chaque mois : performance sur 12 mois (de fin de mois à
  fin de mois). Achat si elle est positive, vente si elle est négative.
- Entrée à l'ouverture de la séance suivante, sortie à l'ouverture qui suit la fin du mois suivant.
  Chaque mois est un trade séparé.
- Stop de protection à 3 × ATR20 journalier.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from fxbt.strategies.base import SIGNAL_COLUMNS, BaseParams
from fxbt.strategies.indicators import atr

from ..daily import daily_with_times


@dataclass(frozen=True)
class Params(BaseParams):
    lookback_months: int = 12
    stop_atr: float = 3.0
    atr_len: int = 20
    rr: float = 1e6  # pas d'objectif
    max_trades_per_day: int = 1
    max_consec_losses: int = 0


def generate_signals(m1: pd.DataFrame, p: Params, pair: str | None = None) -> pd.DataFrame:
    d = daily_with_times(m1)
    d["atr"] = atr(d, p.atr_len)
    month_end = d.groupby([d.index.year, d.index.month]).tail(1)
    perf = (month_end["close"] / month_end["close"].shift(p.lookback_months) - 1).to_numpy()
    index = m1.index

    rows = []
    for k in range(len(month_end) - 1):
        start, nxt = month_end.iloc[k], month_end.iloc[k + 1]
        if np.isnan(perf[k]) or perf[k] == 0 or np.isnan(start["atr"]) or pd.isna(start["next_open"]) or pd.isna(nxt["next_open"]):
            continue
        # Entrée sur la 2ᵉ bougie de la séance : la 1ʳᵉ sert à clôturer le trade du mois précédent.
        pos = index.searchsorted(start["next_open"]) + 1
        if pos >= len(index):
            continue
        entry = index[pos]
        rows.append({
            "entry_time": entry,
            "direction": 1 if perf[k] > 0 else -1,
            "stop_dist": p.stop_atr * start["atr"],
            "stop_level": np.nan,
            "rr": p.rr,
            "deadline": nxt["next_open"],
            "day": entry.normalize(),
        })
    return pd.DataFrame(rows, columns=SIGNAL_COLUMNS)


# Plages de tirage pour le Monte-Carlo sur les paramètres (fixées avant le premier tirage).
PARAM_SPACE = {
    "lookback_months": ("int", 1, 12),
    "stop_atr": ("float", 1.5, 6.0),
}
