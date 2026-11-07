"""Stratégies sur plusieurs jours. Même interface que fxbt (fxbt.strategies.base)."""

from . import donchian, tsmom

STRATEGIES = {
    "donchian": donchian,
    "tsmom": tsmom,
}

# Chemin de module, utilisé par le Monte-Carlo de fxbt (processus parallèles).
MODULE_PATHS = {name: module.__name__ for name, module in STRATEGIES.items()}
