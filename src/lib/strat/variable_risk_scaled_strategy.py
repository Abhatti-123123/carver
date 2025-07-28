# src/lib/strat/variable_risk_scaled_strategy.py
from __future__ import annotations
import pandas as pd
from .strategy_base import StrategyBase

class VariableRiskScaledBuyAndHoldStrategy(StrategyBase):
    """
    Carver Strategy 3 – Buy and Hold with Variable Risk Target

    Key formula:
      TargetVol_t = 0.7 × σ_fast + 0.3 × σ_slow
      Position_t  = TargetVol_t / σ_fast

    All vols are annualised, and EWMA smoothed.
    """

    def __init__(self,
                 fast_lambda: float = 0.60,
                 slow_lambda: float = 0.97,
                 max_leverage: float = 7.0):
        super().__init__(target_vol=None, vol_window=None)
        self.fast_lambda = fast_lambda
        self.slow_lambda = slow_lambda
        self.max_leverage = max_leverage

    def _ewma_vol(self, returns: pd.Series, lambda_: float) -> pd.Series:
        """
        EWMA volatility (annualised) for given decay λ.
        """
        ewma_var = returns.ewm(alpha=1 - lambda_).var(bias=False)
        return (ewma_var**0.5) * (252**0.5)

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        if prices.empty:
            raise ValueError("Empty price series passed to strategy")

        returns = prices.pct_change().fillna(0.0)
        sigma_fast = self._ewma_vol(returns, self.fast_lambda)
        sigma_slow = self._ewma_vol(returns, self.slow_lambda)

        # Carver's dynamic blended volatility target
        blended_vol = 0.7 * sigma_fast + 0.3 * sigma_slow
        # print(f"vol:{blended_vol}")

        # Position sizing
        raw_pos = (blended_vol / sigma_fast).clip(upper=self.max_leverage)
        position = raw_pos.fillna(method="ffill")
        # raw_pos = (1.0 / blended_vol).clip(upper=self.max_leverage)
        # position = raw_pos.ffill()
        # print(f"position:{position}")

        return position
