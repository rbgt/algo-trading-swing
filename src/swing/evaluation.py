"""Évaluation des stratégies sur plusieurs jours selon les critères fixés à l'avance (docs/regles_tendance.md)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd

from fxbt import data
from fxbt.simulation import montecarlo
from fxbt.simulation.engine import Converter, account_for, run

from .strategies import MODULE_PATHS, STRATEGIES

PAIRS = ["EURUSD", "GBPUSD", "USDCHF", "BTCUSD"]
# Conception sur 2015–2021 ; 2022 → fin des données réservé à une seule validation finale.
PERIODS = {"is": ("2015-01-01", "2022-01-01"), "oos": ("2022-01-01", None)}
LOAD_FROM = {"is": "2014-01-01", "oos": "2021-01-01"}  # préchauffage : 12 mois pour le momentum
VARIANTS = {
    "donchian": [("entry_bars", 20), ("entry_bars", 100), ("exit_bars", 10), ("exit_bars", 40),
                 ("stop_atr", 1.5), ("stop_atr", 3.0)],
    "tsmom": [("lookback_months", 3), ("lookback_months", 6), ("stop_atr", 2.0), ("stop_atr", 5.0)],
}


def load(period: str, pairs=PAIRS):
    _, end = PERIODS[period]
    m1s = {p: data.load_m1(p, LOAD_FROM[period], end) for p in sorted(set(pairs) | {"EURUSD"})}
    return m1s, Converter({p: df["close"] for p, df in m1s.items()})


def run_all(name: str, params, m1s, converter, period: str, pairs=PAIRS, stress: bool = False) -> pd.DataFrame:
    """Trades de tous les instruments. Stress : spread le plus élevé de l'instrument et swap × 2."""
    module = STRATEGIES[name]
    start = pd.Timestamp(PERIODS[period][0], tz=data.TZ)
    frames = []
    for pair in pairs:
        signals = module.generate_signals(m1s[pair], params, pair)
        signals = signals[signals["entry_time"] >= start]
        inst = data.INSTRUMENTS[pair]
        cost = inst.costs[-1] if stress else inst.costs[0]
        trades = run(signals, m1s[pair], pair, params, account_for(pair), cost, converter,
                     financing_multiplier=2.0 if stress else 1.0)
        frames.append(trades)
    return pd.concat([f for f in frames if not f.empty], ignore_index=True)


def t_stat(r: pd.Series) -> float:
    return float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))) if len(r) > 1 else np.nan


def summary(trades: pd.DataFrame) -> dict:
    r = trades["r"]
    by_pair = trades.groupby("pair")["r"].agg(["size", "mean"])
    years = trades.groupby(pd.to_datetime(trades["entry_time"], utc=True).dt.year)["r"].sum()
    return {
        "trades": len(r),
        "R_moyen": round(float(r.mean()), 3),
        "t_stat": round(t_stat(r), 2),
        "réussite_%": round(float((r > 0).mean() * 100), 1),
        "swap_moyen_R": round(float(trades["swap_r"].mean()), 3),
        "par_instrument": {p: (int(row["size"]), round(float(row["mean"]), 3)) for p, row in by_pair.iterrows()},
        "années_positives": f"{int((years > 0).sum())}/{len(years)}",
        "par_année": years.round(1).to_dict(),
    }


def pooled_null(name: str, params, m1s, converter, period: str, flips: int = 10_000, seed: int = 0) -> dict:
    start = pd.Timestamp(PERIODS[period][0], tz=data.TZ)
    samples = montecarlo.direction_samples(MODULE_PATHS[name], params, m1s, converter, start, PAIRS, None)
    arrays = [np.concatenate(parts) for parts in zip(*samples.values())]
    return montecarlo.null_summary(*arrays, flips, np.random.default_rng(seed))


def evaluate(name: str, flips: int = 10_000) -> tuple[bool, pd.DataFrame, dict]:
    """Applique les 7 critères de la section 5 sur 2015–2021."""
    m1s, converter = load("is")
    base = STRATEGIES[name].Params()
    trades = run_all(name, base, m1s, converter, "is")
    s = summary(trades)
    stress = summary(run_all(name, base, m1s, converter, "is", stress=True))
    null = pooled_null(name, base, m1s, converter, "is", flips)
    variants = {}
    for key, value in VARIANTS[name]:
        variants[f"{key}={value}"] = summary(run_all(name, dataclasses.replace(base, **{key: value}), m1s, converter, "is"))["R_moyen"]

    positive_pairs = sum(1 for _, (_, mean) in s["par_instrument"].items() if mean > 0)
    good_years, n_years = (int(x) for x in s["années_positives"].split("/"))
    criteria = pd.DataFrame([
        ("1. R moyen ≥ +0,05", s["R_moyen"], s["R_moyen"] >= 0.05),
        ("2. t-stat ≥ 2,0", s["t_stat"], s["t_stat"] >= 2.0),
        ("3. positif sur ≥ 3 instruments sur 4", f"{positive_pairs}/4", positive_pairs >= 3),
        ("4. ≥ 4 années positives sur 7", s["années_positives"], good_years >= 4),
        ("5. positif avec coûts de stress", stress["R_moyen"], stress["R_moyen"] > 0),
        ("6. hasard qui fait mieux < 5 %", f"{null['part_du_hasard_qui_fait_mieux_%']} %", null["part_du_hasard_qui_fait_mieux_%"] < 5),
        ("7. toutes les variantes positives", min(variants.values()), min(variants.values()) > 0),
    ], columns=["critère", "valeur", "rempli"])
    details = {"base": s, "stress": stress, "hasard": null, "variantes": variants}
    return bool(criteria["rempli"].all()), criteria, details


def final_validation(name: str) -> tuple[bool, dict]:
    """Validation unique sur 2022 → fin des données : R moyen réuni > 0 et positif sur ≥ 3 instruments sur 4."""
    m1s, converter = load("oos")
    s = summary(run_all(name, STRATEGIES[name].Params(), m1s, converter, "oos"))
    positive_pairs = sum(1 for _, (_, mean) in s["par_instrument"].items() if mean > 0)
    return s["R_moyen"] > 0 and positive_pairs >= 3, s


def param_montecarlo(name: str, samples: int = 200, seed: int = 0, workers: int | None = None) -> pd.DataFrame:
    """Jeux de réglages tirés dans PARAM_SPACE ; R moyen réuni (pondéré par le nombre de trades)."""
    start, end = PERIODS["is"]
    table = montecarlo.param_montecarlo(MODULE_PATHS[name], samples, seed, PAIRS, LOAD_FROM["is"], end, start,
                                        "histdata", None, workers or montecarlo.default_workers())
    n = table[[f"{p}_trades" for p in PAIRS]].to_numpy(float)
    r = np.nan_to_num(table[[f"{p}_R" for p in PAIRS]].to_numpy(float))
    table["R_réuni"] = (n * r).sum(axis=1) / np.maximum(n.sum(axis=1), 1)
    return table
