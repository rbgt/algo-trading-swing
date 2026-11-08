"""Stratégies sur plusieurs jours. Même interface que fxbt (fxbt.strategies.base)."""

from . import donchian, smc, smc_ob, tsmom

STRATEGIES = {
    "donchian": donchian,
    "tsmom": tsmom,
    "smc": smc,
    "smc_ob": smc_ob,
}

# Chemin de module, utilisé par le Monte-Carlo de fxbt (processus parallèles).
MODULE_PATHS = {name: module.__name__ for name, module in STRATEGIES.items()}
