import numpy as np
import pandas as pd


def compute_strategy_returns(prices: pd.Series, signals: pd.Series, transaction_cost: float):
    """
    Daily returns of one market. Positions are fractions of capital, traded the day after the signal.
    A zero signal holds the previous position (every strategy is a buy-and-hold variant).
    """
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    positions = signals.replace(0, np.nan).shift(1).ffill().fillna(0.0)
    trades = positions.diff().abs().fillna(0.0)
    return positions * returns - trades * transaction_cost


def backtest_multi_asset(prices: pd.DataFrame, signals: pd.DataFrame, transaction_cost: float = 0.0):
    """Portfolio return = sum of per-market returns (signals are already sized as fractions of capital)."""
    per_market = pd.DataFrame({c: compute_strategy_returns(prices[c], signals[c].astype(float), transaction_cost)
                               for c in prices.columns}).fillna(0.0)
    portfolio = per_market.sum(axis=1)
    return portfolio, per_market
