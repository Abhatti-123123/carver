# src/lib/strat/risk_scaled_strategy.py
import pandas as pd
from .strategy_base import StrategyBase

class RiskScaledBuyAndHoldStrategy(StrategyBase):
    """
    Strategy 2 – always long, but scale exposure to hit constant vol.
    """

    def __init__(self,
                 target_vol: float = 0.20,   # 20 % p.a. target risk
                 vol_window: int  = 20):     # 1‑month look‑back
        super().__init__(target_vol, vol_window)

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        if prices.empty:
            raise ValueError("Empty price series")
        returns = prices.pct_change().fillna(0.0)
        sigma   = self._rolling_vol(returns)
        # position = target / realised σ; clip huge gearings
        raw_pos = self.target_vol / sigma
        pos     = raw_pos.clip(upper=5.0)
        return pos
