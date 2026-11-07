from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class StrategyBase(ABC):
    """A strategy turns prices into target positions (fractions of capital), one column per market."""

    @abstractmethod
    def generate_signals(self, prices):
        ...


class MultiAssetStrategyBase(StrategyBase):
    def compute_vol_scaled_positions(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Inverse blended volatility per market (70% fast / 30% slow EWMA), capped at 7."""
        returns = prices.pct_change(fill_method=None).fillna(0.0)
        sigma_fast = returns.ewm(alpha=1 - np.exp(-1 / 5.0)).std() * np.sqrt(252)
        sigma_slow = returns.ewm(alpha=1 - np.exp(-1 / 20.0)).std() * np.sqrt(252)
        blended_vol = 0.7 * sigma_fast + 0.3 * sigma_slow
        return (1 / blended_vol).clip(upper=7.0).ffill().fillna(0.0)
