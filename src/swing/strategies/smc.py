"""Stratégie S3 : Smart Money Concepts en H4 (règles : docs/regles_smc_swing.md).

- Liquidité : plus haut et plus bas de la semaine de trading précédente.
- Sweep en H4 (réintégration en 6 bougies au plus), CHoCH H4 dans les 30 bougies, dans la même semaine.
- Entrée au premier contact M1 avec le haut du dernier FVG de la jambe impulsive (S3) ou de l'order block (S4),
  dans les 12 bougies H4 qui suivent le CHoCH.
- Stop à l'extrême du sweep moins 0,1 × ATR14 journalier, objectif à 2R, sortie forcée après 14 jours.

Le cœur est celui de la stratégie G du repo intraday (fxbt.strategies.smc.find_setups).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from fxbt.data import OHLCV, daily_bars
from fxbt.strategies import smc
from fxbt.strategies.indicators import atr


@dataclass(frozen=True)
class Params(smc.Params):
    tf: str = "4h"
    swing_n: int = 2
    reclaim_bars: int = 6
    choch_bars: int = 30
    retest_bars: int = 12
    entry_zone: str = "fvg"
    buffer_atr: float = 0.1
    atr_len: int = 14
    rr: float = 2.0
    hold_days: int = 14
    min_stop_pips: float = 0.0
    max_trades_per_day: int = 2
    max_consec_losses: int = 0


def h4_bars(m1: pd.DataFrame) -> pd.DataFrame:
    """Bougies H4 alignées sur l'ouverture de la séance forex (23h00, 03h00, 07h00… heure de Zurich)."""
    return m1.resample("4h", label="left", closed="left", offset="3h").agg(OHLCV).dropna(subset=["open"])


def trading_date(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Journée de trading (clôture à 17h à New York), comme fxbt.data.daily_bars."""
    ny = index.tz_convert("America/New_York")
    return (ny + pd.Timedelta(hours=7)).tz_localize(None).normalize()


def generate_signals(m1: pd.DataFrame, p: Params, pair: str | None = None) -> pd.DataFrame:
    bars = h4_bars(m1)
    date = trading_date(bars.index)
    week = date - pd.to_timedelta(date.day_of_week, unit="D")

    daily = daily_bars(m1)
    daily_week = daily.index - pd.to_timedelta(daily.index.day_of_week, unit="D")
    weekly = daily.groupby(daily_week).agg(hi=("high", "max"), lo=("low", "min"))
    prev = weekly.shift(1).reindex(week)
    hi, lo = prev["hi"].to_numpy(), prev["lo"].to_numpy()
    ok = ~np.isnan(hi)

    prev_atr = atr(daily, p.atr_len).shift(1).reindex(date).to_numpy()
    buffer = p.buffer_atr * prev_atr
    ok &= ~np.isnan(buffer)
    always = np.ones(len(bars), bool)
    no_limit = np.full(len(bars), np.iinfo(np.int64).max)

    setups = smc.find_setups(bars, m1, week.asi8, hi, lo, ok, always, always, buffer, no_limit, p)
    end = m1.index[-1]
    return smc.to_signals(setups, p, lambda entry: (entry + pd.Timedelta(days=p.hold_days)).where(
        entry + pd.Timedelta(days=p.hold_days) < end, end))


# Plages de tirage pour le Monte-Carlo sur les paramètres (fixées avant le premier tirage).
PARAM_SPACE = {
    "swing_n": ("int", 1, 3),
    "reclaim_bars": ("int", 3, 12),
    "choch_bars": ("int", 15, 60),
    "retest_bars": ("int", 6, 24),
    "rr": ("float", 1.5, 3.0),
    "hold_days": ("int", 7, 28),
}
