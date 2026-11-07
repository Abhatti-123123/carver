import numpy as np
import pandas as pd

from .strategy_base import StrategyBase


class RiskScaledBuyAndHoldStrategy(StrategyBase):
    """Strategy 2: always long, sized to a constant volatility target (20-day realised vol), capped at 5x."""

    def __init__(self, target_vol: float = 0.20, vol_window: int = 20):
        self.target_vol = target_vol
        self.vol_window = vol_window

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        returns = prices.pct_change(fill_method=None).fillna(0.0)
        sigma = returns.rolling(self.vol_window).std() * np.sqrt(252)
        return (self.target_vol / sigma).clip(upper=5.0)
