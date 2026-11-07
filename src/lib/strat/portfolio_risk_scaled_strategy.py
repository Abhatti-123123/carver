import numpy as np
import pandas as pd

from .strategy_base import MultiAssetStrategyBase
from lib.indicators.trending_indicator import ewma_crossover


class PortfolioRiskScaledStrategy(MultiAssetStrategyBase):
    """
    Strategy 4 (trend_mode="none"): portfolio risk parity.
        Weight each market by 1 / blended vol, then rescale the whole book to the vol target
        using a blend of short- and long-window covariance.
    Strategy 6/7 (trend_mode="strength", the final system): the S4 positions sized by trend strength.
        Forecast = slow EWMA crossover / price vol, scaled and capped; position = S4 position x forecast / 10.

    Every strategy here is a buy-and-hold variant: a zero signal means "hold the last size"
    (see the backtester), so a long-only forecast floored at 0 fades positions out instead of shorting.
    """

    FAST_SPAN, SLOW_SPAN = 64, 256    # Carver's slow EWMAC(64, 256)
    VOL_ALPHA = 0.07                  # EWMA decay for the price-vol used to risk-adjust the crossover
    FORECAST_CAP = 20.0

    def __init__(self, target_vol=0.2, short_lookback=60, long_lookback=120, lambda_=0.5, scale_halflife=20,
                 trend_mode="strength", long_only=True, forecast_scalar=1.9, update_threshold=0.05,
                 max_position=5.0):
        super().__init__()
        self.target_vol = target_vol
        self.short_lookback = short_lookback
        self.long_lookback = long_lookback
        self.lambda_ = lambda_                  # weight on the short-window covariance
        self.scale_halflife = scale_halflife    # EWMA half-life (days) of the portfolio scale factor; None = off
        self.trend_mode = trend_mode.lower()    # "none" | "strength"
        self.long_only = long_only              # floor the forecast at 0: fade out instead of shorting
        self.forecast_scalar = forecast_scalar  # Carver's scalar for slow EWMAC
        self.update_threshold = update_threshold  # re-size only when the forecast moves more than this (relative)
        self.max_position = max_position        # per-market cap, in units of capital

    def generate_signals(self, prices):
        positions = self._risk_scale(prices, self.compute_vol_scaled_positions(prices))
        if self.trend_mode == "strength":
            positions = self._size_by_trend(prices, positions)
        elif self.trend_mode != "none":
            raise ValueError(f"unknown trend_mode {self.trend_mode!r}")
        return positions.fillna(0.0).ffill()

    def _risk_scale(self, prices, raw_weights):
        """Rescale the inverse-vol book to the vol target each day (S4)."""
        returns = prices.pct_change(fill_method=None)
        positions = pd.DataFrame(np.nan, index=raw_weights.index, columns=raw_weights.columns)
        warmup = max(self.short_lookback, self.long_lookback)
        smooth_scale = None
        for t in range(1, len(raw_weights)):
            w = raw_weights.iloc[t]
            if t < warmup:
                # not enough history for covariance: hold normalised weights (|w| sums to 1)
                gross = w.abs().sum()
                positions.iloc[t] = (w / gross).clip(upper=1.0) if gross > 0 else 0.0
                continue
            cov = ((1 - self.lambda_) * returns.iloc[t - self.long_lookback:t].cov()
                   + self.lambda_ * returns.iloc[t - self.short_lookback:t].cov()).values
            port_vol = np.sqrt(w.values @ cov @ w.values) * np.sqrt(252)
            scale = self.target_vol / port_vol if port_vol > 0 else 1.0
            if self.scale_halflife:
                a = 1 - 0.5 ** (1 / self.scale_halflife)
                smooth_scale = scale if smooth_scale is None else a * scale + (1 - a) * smooth_scale
                scale = smooth_scale
            positions.iloc[t] = (w * scale).clip(upper=self.max_position)
        return positions

    def _size_by_trend(self, prices, positions):
        """Multiply each position by its trend forecast / 10, re-sizing only on meaningful forecast moves."""
        f = self.trend_forecast(prices) / 10
        if self.long_only:
            f = f.clip(lower=0.0)
        rel_change = (f - f.shift(1)).abs() / (f.shift(1).abs() + 1e-12)
        sized = (positions * f).where(rel_change > self.update_threshold)
        sized.iloc[0] = positions.iloc[0] * f.iloc[0]
        return sized.ffill()

    def trend_forecast(self, prices):
        """Risk-adjusted slow EWMA crossover, scaled and capped at +/-20."""
        rets = prices.pct_change(fill_method=None).fillna(0.0)
        price_vol = prices * rets.ewm(alpha=self.VOL_ALPHA, adjust=False).std()
        z = ewma_crossover(prices, self.FAST_SPAN, self.SLOW_SPAN) / price_vol
        z = z.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return (z * self.forecast_scalar).clip(-self.FORECAST_CAP, self.FORECAST_CAP).fillna(0.0)
