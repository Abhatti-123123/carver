import numpy as np
import pandas as pd

from .strategy_base import StrategyBase


class VariableRiskScaledBuyAndHoldStrategy(StrategyBase):
    """
    Strategy 3: buy and hold with a variable risk target.
        target_t   = 0.7 * fast vol + 0.3 * slow vol   (EWMA, annualised)
        position_t = target_t / fast vol, capped at max_leverage
    More exposure when recent vol is below its long-run level, less after a spike.
    """

    def __init__(self, fast_lambda: float = 0.60, slow_lambda: float = 0.97, max_leverage: float = 7.0):
        self.fast_lambda = fast_lambda
        self.slow_lambda = slow_lambda
        self.max_leverage = max_leverage

    @staticmethod
    def _ewma_vol(returns: pd.Series, lambda_: float) -> pd.Series:
        return returns.ewm(alpha=1 - lambda_).var(bias=False) ** 0.5 * np.sqrt(252)

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        returns = prices.pct_change(fill_method=None).fillna(0.0)
        fast = self._ewma_vol(returns, self.fast_lambda)
        slow = self._ewma_vol(returns, self.slow_lambda)
        return ((0.7 * fast + 0.3 * slow) / fast).clip(upper=self.max_leverage).ffill()
