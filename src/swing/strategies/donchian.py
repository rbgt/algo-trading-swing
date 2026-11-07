"""Stratégie S1 : cassure de Donchian (règles : docs/regles_tendance.md).

- Achat si la clôture journalière dépasse le plus haut des 55 bougies précédentes, vente si elle passe
  sous le plus bas des 55 précédentes. Entrée à l'ouverture de la séance suivante.
- Stop initial à 2 × ATR20 journalier.
- Sortie à la première clôture sous le plus bas des 20 bougies précédentes (achat) ou au-dessus du plus
  haut des 20 précédentes (vente), à l'ouverture suivante.
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
    entry_bars: int = 55
    exit_bars: int = 20
    stop_atr: float = 2.0
    atr_len: int = 20
    rr: float = 1e6  # pas d'objectif
    max_trades_per_day: int = 1
    max_consec_losses: int = 0


def generate_signals(m1: pd.DataFrame, p: Params, pair: str | None = None) -> pd.DataFrame:
    d = daily_with_times(m1)
    prev_high, prev_low = d["high"].shift(1), d["low"].shift(1)
    entry_hi = prev_high.rolling(p.entry_bars).max().to_numpy()
    entry_lo = prev_low.rolling(p.entry_bars).min().to_numpy()
    exit_hi = prev_high.rolling(p.exit_bars).max().to_numpy()
    exit_lo = prev_low.rolling(p.exit_bars).min().to_numpy()
    a = atr(d, p.atr_len).to_numpy()
    close = d["close"].to_numpy()
    next_open = d["next_open"]
    end = m1.index[-1]

    exit_long = close < exit_lo
    exit_short = close > exit_hi
    rows = []
    for i in np.flatnonzero((close > entry_hi) | (close < entry_lo)):
        if np.isnan(a[i]) or pd.isna(next_open.iloc[i]):
            continue
        direction = 1 if close[i] > entry_hi[i] else -1
        exits = np.flatnonzero((exit_long if direction == 1 else exit_short)[i + 1:])
        deadline = next_open.iloc[i + 1 + exits[0]] if exits.size else end
        if pd.isna(deadline):
            deadline = end
        entry = next_open.iloc[i]
        rows.append({
            "entry_time": entry,
            "direction": direction,
            "stop_dist": p.stop_atr * a[i],
            "stop_level": np.nan,
            "rr": p.rr,
            "deadline": deadline,
            "day": entry.normalize(),
        })
    return pd.DataFrame(rows, columns=SIGNAL_COLUMNS)


# Plages de tirage pour le Monte-Carlo sur les paramètres (fixées avant le premier tirage).
PARAM_SPACE = {
    "entry_bars": ("int", 20, 120),
    "exit_bars": ("int", 10, 60),
    "stop_atr": ("float", 1.0, 4.0),
}
