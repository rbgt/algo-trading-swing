"""Bougies journalières et heures d'exécution pour les stratégies sur plusieurs jours.

La journée se termine à 17h à New York (bougie « D » de TradingView). Un signal sur la clôture du jour D
s'exécute à la première bougie M1 qui suit cette clôture : l'ouverture de la séance suivante, le lundi
pour un signal du vendredi en forex.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fxbt.data import TZ, daily_bars


def daily_with_times(m1: pd.DataFrame) -> pd.DataFrame:
    """Bougies journalières, avec l'heure de clôture et l'heure d'exécution suivante (heure de Zurich)."""
    d = daily_bars(m1)
    close_time = (d.index + pd.Timedelta(hours=17)).tz_localize("America/New_York").tz_convert(TZ)
    d["close_time"] = close_time
    d["next_open"] = next_bar_at_or_after(m1.index, close_time)
    return d


def next_bar_at_or_after(index: pd.DatetimeIndex, times: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Première bougie M1 à partir de chaque heure (NaT après la fin des données)."""
    pos = index.searchsorted(times, side="left")
    out = np.full(len(times), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    ok = pos < len(index)
    out[ok] = index.as_unit("ns").tz_convert("UTC").tz_localize(None).to_numpy()[pos[ok]]
    return pd.DatetimeIndex(out).tz_localize("UTC").tz_convert(TZ)
