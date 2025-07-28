import pandas as pd
import numpy as np
from .strategy_base import MultiAssetStrategyBase
from lib.indicators.trending_indicator import trend_mask

#Sharpe above 1...first such strategy
#Sharpe remains constant for all target vols....Higher target vols have higher cagr and returns along with higher mdd and vol
#The mdd are stable...even with total vol around 0.4, ther mdd is about the same...Not big
class PortfolioRiskScaledStrategy(MultiAssetStrategyBase):
    def __init__(self, target_vol=0.90, short_lookback=20, long_lookback=60, lambda_=0.5, rebalance=True, follow_trend=True): #Traget vol can be easily half of the expected sharpe
        #When I increased target vol from 20% to 40% the returns and cagr increase signififcantly with minimum change in vol, mdd and sharpe
        super().__init__()
        self.target_vol = target_vol
        self.short_lookback = short_lookback
        self.long_lookback = long_lookback
        self.lambda_ = lambda_  # 0 = use only long-term cov, 1 = use only short-term cov
        self.rebalance = rebalance
        self.follow_trend = follow_trend

    def generate_signals(self, prices, initial_capital=1.0):
        raw_weights = self.compute_vol_scaled_positions(prices, self.target_vol)
        returns = prices.pct_change(fill_method=None)
        returns.fillna(0.0)

        positions = pd.DataFrame(index=raw_weights.index, columns=raw_weights.columns)

        for t in range(1, len(raw_weights)):
            if t < self.short_lookback or t < self.long_lookback:
                w0 = raw_weights.iloc[t].copy()
                # ── normalise so |weights| sum to 1 ─────────────────────────  Very crucial to improce results...put in notes
                nom = w0.abs().sum()
                if nom > 0:
                    w0 = w0 / nom
                else:
                    w0[:] = 0.0          # all NaN or zero ‑‑ stay flat

                # optional: respect per‑asset leverage cap
                w0 = w0.clip(upper=1.0)  # or your chosen cap

                positions.iloc[t] = w0
                continue
            short_cov = returns.iloc[t - self.short_lookback:t].cov()
            long_cov = returns.iloc[t - self.long_lookback:t].cov()

            # Blend covariances
            cov = ((1 - self.lambda_) * long_cov + self.lambda_ * short_cov).values

            w_t = raw_weights.iloc[t].values.reshape(-1, 1)
            port_vol = np.sqrt(w_t.T @ cov @ w_t).item()
            port_vol_annual = port_vol * np.sqrt(252)

            scale = self.target_vol / port_vol_annual if port_vol_annual > 0 else 1.0

            # Adjust for equity drawdowns (optional)
            if self.rebalance:
                equity = self._equity_over_time(t, positions, prices, initial_capital)
                scale *= initial_capital / equity

            positions.iloc[t] = (raw_weights.iloc[t] * scale).clip(upper=7.0)

        if self.follow_trend == True:
            mask = trend_mask(prices)
            print(mask.shape)
            print(positions.shape)
            print(mask.value_counts())
            positions = positions * mask
        return positions.ffill()

    def _equity_over_time(self, t, positions, prices, initial_capital):
        # Approximate portfolio equity up to time t for rebalancing
        pnl = ((positions.shift(1) * prices.pct_change(fill_method=None).fillna(0.0)).iloc[:t]).sum(axis=1)
        return initial_capital + pnl.sum()