"""Trend indicators."""
import pandas as pd


def ewma_crossover(prices: pd.DataFrame | pd.Series, fast_span: int, slow_span: int) -> pd.DataFrame | pd.Series:
    """Fast minus slow exponential moving average of price (Carver's EWMAC), in price units."""
    fast = prices.ewm(alpha=2 / (fast_span + 1), adjust=False).mean()
    slow = prices.ewm(alpha=2 / (slow_span + 1), adjust=False).mean()
    return fast - slow
