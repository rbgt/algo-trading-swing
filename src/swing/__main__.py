"""Ligne de commande.

    python -m swing backtest --strategy donchian
    python -m swing evaluate --strategy tsmom          # les 7 critères fixés à l'avance, sur 2015–2021
    python -m swing montecarlo --strategy donchian     # jeux de réglages tirés au hasard
    python -m swing final --strategy donchian --final  # validation unique sur 2022 → fin des données
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import evaluation
from .strategies import STRATEGIES

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def _print_summary(title: str, s: dict) -> None:
    print(f"\n--- {title} ---")
    print(f"trades {s['trades']} | R moyen {s['R_moyen']:+.3f} | t-stat {s['t_stat']:+.2f} | réussite {s['réussite_%']} % "
          f"| swap moyen {s['swap_moyen_R']:.3f} R | années positives {s['années_positives']}")
    print("par instrument (trades, R moyen) :", s["par_instrument"])
    print("R par année :", s["par_année"])


def cmd_backtest(args):
    if args.period == "oos" and not args.final:
        sys.exit("La période 2022 → fin des données ne sert qu'une fois, pour la validation finale. Ajouter --final.")
    m1s, converter = evaluation.load(args.period, args.pairs)
    params = STRATEGIES[args.strategy].Params()
    trades = evaluation.run_all(args.strategy, params, m1s, converter, args.period, args.pairs, stress=args.stress)
    RESULTS_DIR.mkdir(exist_ok=True)
    trades.to_csv(RESULTS_DIR / f"{args.strategy}_{args.period}{'_stress' if args.stress else ''}.csv", index=False)
    _print_summary(f"{args.strategy}, {args.period}{', coûts de stress' if args.stress else ''}", evaluation.summary(trades))


def cmd_evaluate(args):
    ok, criteria, details = evaluation.evaluate(args.strategy, args.flips)
    _print_summary(f"{args.strategy} : réglages de base, 2015–2021", details["base"])
    _print_summary("coûts de stress", details["stress"])
    print("\nTest contre le hasard (trades des 4 instruments réunis) :", details["hasard"])
    print("Variantes (R moyen réuni) :", details["variantes"])
    print("\n" + criteria.to_string(index=False))
    print(f"\nVerdict : {'RETENUE pour la validation finale' if ok else 'REJETÉE'}")


def cmd_montecarlo(args):
    table = evaluation.param_montecarlo(args.strategy, args.samples, args.seed)
    RESULTS_DIR.mkdir(exist_ok=True)
    table.to_csv(RESULTS_DIR / f"montecarlo_{args.strategy}.csv", index=False)
    q = table["R_réuni"].quantile([0.1, 0.5, 0.9])
    print(f"{args.samples} jeux de réglages | R réuni p10 / médiane / p90 : {q[0.1]:+.3f} / {q[0.5]:+.3f} / {q[0.9]:+.3f} "
          f"| positifs : {(table['R_réuni'] > 0).mean() * 100:.0f} %")


def cmd_final(args):
    if not args.final:
        sys.exit("Validation unique sur 2022 → fin des données. Ajouter --final pour confirmer.")
    ok, s = evaluation.final_validation(args.strategy)
    _print_summary(f"{args.strategy} : validation finale (2022 → fin des données)", s)
    print(f"\nVerdict : {'VALIDÉE' if ok else 'ÉCHEC de la validation'}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="swing")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backtest", help="Backtest sur les 4 instruments")
    b.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    b.add_argument("--pairs", nargs="+", default=evaluation.PAIRS)
    b.add_argument("--period", choices=["is", "oos"], default="is")
    b.add_argument("--final", action="store_true")
    b.add_argument("--stress", action="store_true", help="spread le plus élevé et swap × 2")
    b.set_defaults(func=cmd_backtest)

    e = sub.add_parser("evaluate", help="Les 7 critères fixés à l'avance, sur 2015–2021")
    e.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    e.add_argument("--flips", type=int, default=10_000)
    e.set_defaults(func=cmd_evaluate)

    m = sub.add_parser("montecarlo", help="Jeux de réglages tirés au hasard (2015–2021)")
    m.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    m.add_argument("--samples", type=int, default=200)
    m.add_argument("--seed", type=int, default=0)
    m.set_defaults(func=cmd_montecarlo)

    f = sub.add_parser("final", help="Validation unique sur 2022 → fin des données")
    f.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    f.add_argument("--final", action="store_true")
    f.set_defaults(func=cmd_final)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
