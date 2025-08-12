import pandas as pd
import numpy as np
from .strategy_base import MultiAssetStrategyBase
from lib.indicators.trending_indicator import trend_mask, macd_signal, macd_signal_prices

#Sharpe above 1...first such strategy
#Sharpe remains constant for all target vols....Higher target vols have higher cagr and returns along with higher mdd and vol
#The mdd are stable...even with total vol around 0.4, ther mdd is about the same...Not big

#This follows dynamic positioning, even after trend starts the position will be continued to change according to the volatility
class PortfolioRiskScaledStrategy(MultiAssetStrategyBase):
    def __init__(self, target_vol=0.60, short_lookback=20, long_lookback=60, lambda_=0.5, rebalance=True, trend_mode: str = "mask"): #Traget vol can be easily half of the expected sharpe
        #When I increased target vol from 20% to 40% the returns and cagr increase signififcantly with minimum change in vol, mdd and sharpe
        #Follow trend improves overall algororithm
        super().__init__()
        self.target_vol = target_vol
        self.short_lookback = short_lookback
        self.long_lookback = long_lookback
        self.lambda_ = lambda_  # 0 = use only long-term cov, 1 = use only short-term cov
        self.rebalance = rebalance
        self.trend_mode = trend_mode.lower()         # ← NEW FLAG: "none" | "mask" | "strength"
        # Strategy‑7 constants (used only when trend_mode == "strength")
        self._VOL_LAMBDA   = 0.07   # EW stdev half‑life ≈ 20 days
        self._SCALE_K      = 4.0    # 1 σ ↦ ~5 forecast units
        self._FORECAST_CAP = 20.0
        self._FAST_L      = 2 / 65          # ≈ 0.0308  (64‑day half‑life)
        self._SLOW_L      = 2 / 257         # ≈ 0.0078  (256‑day half‑life)
        self._SCALAR = 1.9          # Carver’s empirical scalar for slow EWMAC

    def generate_signals(self, prices, initial_capital=1.0):
        raw_weights = self.compute_vol_scaled_positions(prices, self.target_vol)
        returns = prices.pct_change(fill_method=None)
        returns.fillna(0.0)

        positions = pd.DataFrame(index=raw_weights.index, columns=raw_weights.columns)
        max_vol = 0
        min_vol = 100
        # if self.trend_mode == "strength":
        #     forecast_df = self._trend_strength_forecast(prices)
        #     positions *=  forecast_df / 10 # –2 … +2

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
            if port_vol_annual > max_vol:
                max_vol = port_vol_annual
            if min_vol > port_vol_annual:
                min_vol = port_vol_annual
            scale = self.target_vol / port_vol_annual if port_vol_annual > 0 else 1.0

            # Adjust for equity drawdowns (optional)
            if self.rebalance:
                equity = self._equity_over_time(t, positions, prices, initial_capital)
                scale *= initial_capital / equity

            positions.iloc[t] = (raw_weights.iloc[t] * scale).clip(upper=5.0)
        # ------------- TREND OVERLAY ----------------------------------------
        if self.trend_mode == "mask":
            positions *= trend_mask(prices)                        # ±1 / 0
        # elif self.trend_mode == "strength":
        #     forecast_df = self._trend_strength_forecast(prices)
        #     positions *=  forecast_df / 10 # –2 … +2
        #     # positions *= trend_mask(prices) 
        # if self.trend_mode == "strength":
        #     forecast_df = self._trend_strength_forecast(prices)
        #     # Calculate relative change in forecast per asset
        #     rel_change = (forecast_df - forecast_df.shift(1)).abs() / (forecast_df.shift(1).abs() + 1e-12)
        #     update_mask = rel_change > 0.05

        #     new_positions = positions.copy()
        #     for col in positions.columns:
        #         for t in range(1, len(positions)):
        #             # Only update when change in forecast is above 5%
        #             if update_mask.iloc[t, positions.columns.get_loc(col)]:
        #                 new_positions.iloc[t, positions.columns.get_loc(col)] = positions.iloc[t, positions.columns.get_loc(col)]
        #             else:
        #                 new_positions.iloc[t, positions.columns.get_loc(col)] = new_positions.iloc[t-1, positions.columns.get_loc(col)]
        #     positions = new_positions
        if self.trend_mode == "strength":
            forecast_df = self._trend_strength_forecast(prices) / 10
            rel_change = (forecast_df - forecast_df.shift(1)).abs() / (forecast_df.shift(1).abs() + 1e-12)
            update_mask = rel_change > 0.10

            new_positions = positions.copy()
            new_positions.iloc[0] = positions.iloc[0] * forecast_df.iloc[0]
            for col in positions.columns:
                for t in range(1, len(positions)):
                    col_idx = positions.columns.get_loc(col)
                    if update_mask.iloc[t, col_idx]:
                        # Update to the *new* value based on forecast
                        new_positions.iloc[t, col_idx] = raw_weights.iloc[t, col_idx] * forecast_df.iloc[t, col_idx] / 10
                    else:
                        # Hold previous position
                        new_positions.iloc[t, col_idx] = new_positions.iloc[t-1, col_idx]
            positions = new_positions

        return positions.fillna(0.0).ffill()

    def _equity_over_time(self, t, positions, prices, initial_capital):
        # Approximate portfolio equity up to time t for rebalancing
        pnl = ((positions.shift(1) * prices.pct_change(fill_method=None).fillna(0.0)).iloc[:t]).sum(axis=1)
        return initial_capital + pnl.sum()

    def _trend_strength_forecast(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Carver Strategy‑7 forecast: linear scaling, cap ±20.
        Steps:
        1. returns -> vol in price terms
        2. slow EWMAC(64,256) on returns
        3. risk‑adjust MACD by vol  (z_t)
        4. scale by SCALAR so E|forecast| ≈10
        5. clip to ±20, replace NaNs with 0
        """
        # ---------- Step‑0 : returns & price‑vol ----------
        rets = prices.pct_change(fill_method=None).fillna(0.0)
        pct_sigma = rets.ewm(alpha=self._VOL_LAMBDA, adjust=False).std()   # %
        vol = prices * pct_sigma                                           # σ in price units

        # ---------- Step‑1 : slow MACD (64 / 256 half‑lives) ----------
        macd = macd_signal_prices(
            prices,
            fast_lambda=self._FAST_L,
            slow_lambda=self._SLOW_L,
        )

        # ---------- Step‑2 : risk‑normalised strength ----------
        z = macd / vol
        z = z.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # ---------- Step‑3 : scale and clip ----------
        forecast = (z)             # linear scaling
        forecast = forecast.clip(-self._FORECAST_CAP, self._FORECAST_CAP)

        return forecast.fillna(0.0).astype(float)
