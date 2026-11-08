"""Stratégie S4 : comme S3 (smc), avec entrée sur l'order block ICT (règles : docs/regles_smc_swing.md)."""

from __future__ import annotations

from dataclasses import dataclass

from . import smc


@dataclass(frozen=True)
class Params(smc.Params):
    entry_zone: str = "ob"


generate_signals = smc.generate_signals
PARAM_SPACE = smc.PARAM_SPACE
