"""Utility functions to generate an exponential‑MACD trend signal.

Implements the idea in Robert Carver’s Strategy 5 (trend‑following overlay):
    * Two exponentially weighted moving averages with different lambdas
    * MACD = EMA_fast − EMA_slow (percentage terms)
    * A position is allowed only when MACD > 0  (long‑bias); < 0 blocks longs
      and allows shorts; ==0 blocks both.

The function returns a DataFrame of the *same shape* as the input price frame,
containing +1 when an instrument is trending **up**, –1 when trending **down**,
0 otherwise.  Clients can element‑wise multiply this mask with their raw
position weights to zero out contra‑trend exposures.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple

# Default lambdas from Carver book (fast ≈ 40‑day half‑life, slow ≈ 160‑day)
DEFAULT_FAST_LAMBDA = 0.15
DEFAULT_SLOW_LAMBDA = 0.03


def _ema(series: pd.Series, lambd: float) -> pd.Series:
    """Exponentially weighted moving average with decay parameter *lambda*."""
    return series.ewm(alpha=lambd, adjust=False).mean()


def macd_signal(
    prices: pd.DataFrame | pd.Series,
    fast_lambda: float = DEFAULT_FAST_LAMBDA,
    slow_lambda: float = DEFAULT_SLOW_LAMBDA,
) -> pd.DataFrame | pd.Series:
    """Return the signed MACD series (+/-) for each column of *prices*.

    Positive values imply upward trend, negative values downward.
    The magnitude can be interpreted as MACD strength in percent terms.
    """
    returns = prices.pct_change(fill_method=None)
    fast    = returns.ewm(alpha=fast_lambda, adjust=False).mean()
    slow    = returns.ewm(alpha=slow_lambda, adjust=False).mean()
    return fast - slow

def macd_signal_prices(
    prices: pd.DataFrame | pd.Series,
    fast_lambda: float = DEFAULT_FAST_LAMBDA,
    slow_lambda: float = DEFAULT_SLOW_LAMBDA,
) -> pd.DataFrame | pd.Series:
    """Return the signed MACD series (+/-) for each column of *prices*.

    Positive values imply upward trend, negative values downward.
    The magnitude can be interpreted as MACD strength in percent terms.
    """
    fast = prices.ewm(alpha=fast_lambda, adjust=False).mean()
    slow = prices.ewm(alpha=slow_lambda, adjust=False).mean()
    return fast - slow

def trend_mask(
    prices: pd.DataFrame | pd.Series,
    fast_lambda: float = DEFAULT_FAST_LAMBDA,
    slow_lambda: float = DEFAULT_SLOW_LAMBDA,
    threshold: float = 0.0,
) -> pd.DataFrame | pd.Series:
    """Binary (+1 / –1 / 0) trend direction mask.

    * +1  → bullish trend (MACD >  threshold)
    * –1  → bearish trend (MACD < –threshold)
    * 0   → no clear trend (|MACD| ≤ threshold)
    """
    macd = macd_signal(prices, fast_lambda, slow_lambda)
    mask = pd.DataFrame(index=macd.index, columns=macd.columns)
    mask[macd >  0] = 1
    mask[macd < -0.3] = -1
    mask = mask.fillna(0)
    return mask.astype(int)