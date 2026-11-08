import numpy as np
import pandas as pd

from fxbt.data import daily_bars
from fxbt.strategies.indicators import atr
from swing.daily import daily_with_times
from swing.strategies import donchian, smc, smc_ob, tsmom

TZ = "Europe/Zurich"


def synthetic_m1(days=400, seed=0, drift=0.0):
    """Marche aléatoire M1 du dimanche 23h au vendredi 23h (heure de Zurich), comme le forex."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-07 23:00", periods=days * 1440, freq="1min", tz=TZ)
    ny = idx.tz_convert("America/New_York")
    open_week = ~((ny.day_of_week == 4) & (ny.hour >= 17) | (ny.day_of_week == 5) | (ny.day_of_week == 6) & (ny.hour < 17))
    idx = idx[open_week]
    close = 1.10 + np.cumsum(rng.normal(drift, 0.00005, len(idx)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + 0.00002,
                         "low": np.minimum(open_, close) - 0.00002, "close": close, "volume": 1.0},
                        index=pd.DatetimeIndex(idx, name="time"))


def test_daily_execution_time_is_next_session_open():
    m1 = synthetic_m1(days=30)
    d = daily_with_times(m1)
    # Clôture à 17h New York ; l'exécution suit, et la bougie du vendredi s'exécute à la réouverture du dimanche.
    assert (d["close_time"].dt.tz_convert("America/New_York").dt.hour == 17).all()
    d = d.dropna(subset=["next_open"])  # le dernier jour n'a pas de séance suivante
    assert (d["next_open"] >= d["close_time"]).all()
    fridays = d[d.index.day_of_week == 4]
    assert (fridays["next_open"].dt.tz_convert("America/New_York").dt.day_of_week == 6).all()


def test_donchian_signals_follow_channel_rules():
    m1 = synthetic_m1(days=400, seed=1)
    p = donchian.Params()
    sig = donchian.generate_signals(m1, p, "EURUSD")
    assert len(sig) > 0
    d = daily_with_times(m1)
    hi = d["high"].shift(1).rolling(55).max()
    lo = d["low"].shift(1).rolling(55).min()
    a = atr(daily_bars(m1), 20)
    for s in sig.itertuples():
        day = d.index[d["next_open"] == s.entry_time][0]
        assert (d.loc[day, "close"] > hi[day]) if s.direction == 1 else (d.loc[day, "close"] < lo[day])
        assert np.isclose(s.stop_dist, 2 * a[day])
        assert s.deadline > s.entry_time


def test_tsmom_direction_is_sign_of_12_month_performance():
    m1 = synthetic_m1(days=560, seed=2, drift=0.000002)  # tendance haussière
    sig = tsmom.generate_signals(m1, tsmom.Params(), "EURUSD")
    assert len(sig) >= 3
    d = daily_bars(m1)
    month_end = d.groupby([d.index.year, d.index.month]).tail(1)["close"]
    perf = month_end / month_end.shift(12) - 1
    first = sig.iloc[0]
    expected = 1 if perf.dropna().iloc[0] > 0 else -1
    assert first.direction == expected
    # Chaque trade se termine quand le suivant commence (1 minute avant son entrée).
    gaps = (sig["entry_time"].iloc[1:].to_numpy() - sig["deadline"].iloc[:-1].to_numpy())
    assert (gaps == np.timedelta64(1, "m")).all()


def test_smc_swing_sweeps_previous_week_and_exits_after_hold_days():
    m1 = synthetic_m1(days=400, seed=4)
    d = daily_bars(m1)
    week = d.index - pd.to_timedelta(d.index.day_of_week, unit="D")
    weekly = d.groupby(week).agg(hi=("high", "max"), lo=("low", "min"))
    for module in (smc, smc_ob):
        p = module.Params()
        sig = module.generate_signals(m1, p, "EURUSD")
        assert len(sig) > 0
        for s in sig.itertuples():
            prev = weekly.loc[:smc.trading_date(pd.DatetimeIndex([s.entry_time]))[0]].iloc[-2]
            # Le stop est au-delà de la liquidité de la semaine précédente (extrême du sweep, plus une marge).
            assert s.stop_level < prev["lo"] if s.direction == 1 else s.stop_level > prev["hi"]
            assert s.deadline == min(s.entry_time + pd.Timedelta(days=p.hold_days), m1.index[-1])
