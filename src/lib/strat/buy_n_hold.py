import pandas as pd

from .strategy_base import StrategyBase


class BuyAndHoldStrategy(StrategyBase):
    """Strategy 1: one fixed unit long, held throughout."""

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        return pd.Series(1.0, index=prices.index)
