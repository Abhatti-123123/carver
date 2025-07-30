# src/lib/strat/strategy_base.py
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class StrategyBase(ABC):
    """
    Abstract base class for ALL strategies.
    Every subclass must implement `generate_signals`.
    A ‘signal’ is a pandas Series whose values are the *target position*
    (can be fractional, negative, or zero) at each timestamp.
    """

    def __init__(self,
                 target_vol: float | None = None,
                 vol_window: int | None = None):
        self.target_vol  = target_vol      # e.g. 0.20 for 20 % p.a.
        self.vol_window  = vol_window      # e.g. 20 trading days

    @abstractmethod
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Return a position series indexed like `prices`."""
        ...

    # --- shared utilities everyone will need -------------------------
    def _rolling_vol(self, returns: pd.Series) -> pd.Series:
        """
        Annualised rolling stdev of daily returns using the window set
        in `self.vol_window`. 252≈trading days per year.
        """
        if self.vol_window is None:
            raise ValueError("vol_window not set")
        return returns.rolling(self.vol_window).std() * (252**0.5)


class MultiAssetStrategyBase(StrategyBase):
    def compute_vol_scaled_positions(self, prices, target_vol):
        """
        Compute per-asset risk-scaled raw positions using the same logic
        as in RiskScaledBuyAndHoldStrategy (individual scaling only).
        """
        returns = prices.pct_change(fill_method=None).fillna(0.0)
        sigma_fast = returns.ewm(alpha=1 - np.exp(-1 / 5.0)).std() * np.sqrt(252)
        sigma_slow = returns.ewm(alpha=1 - np.exp(-1 / 20.0)).std() * np.sqrt(252)
        blended_vol = 0.7 * sigma_fast + 0.3 * sigma_slow

        raw_positions = (1 / blended_vol).clip(upper=7.0)
        return raw_positions.ffill().fillna(0.0)

    def compute_portfolio_vol(self, weights, cov_matrix):
        """
        Compute portfolio volatility: sqrt(w^T * C * w)
        """
        return np.sqrt((weights.T @ cov_matrix @ weights).sum(axis=1))
