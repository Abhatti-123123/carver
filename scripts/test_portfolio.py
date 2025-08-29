# from lib import STRATEGY_REGISTRY
# from lib.backtester.backtester import backtest_multi_asset
# import pandas as pd, argparse, os
# import matplotlib.pyplot as plt
# import numpy as np
# import seaborn as sns
# from scipy.stats import skew, kurtosis

# def main(start: str, end: str, tc: float,
#          strategy_name: str, out: str):

#     strategy_cls = STRATEGY_REGISTRY[strategy_name]
#     strat        = strategy_cls()
#     price_df     = pd.read_parquet("data/panel.parquet")
#     # Drop columns with >10% NaNs
#     threshold = 0.10  # 10%
#     valid_cols = price_df.columns[price_df.isnull().mean() <= threshold]
#     price_df = price_df[valid_cols]

#     # Forward-fill remaining NaNs (e.g., from weekends or illiquid assets)
#     price_df = price_df.ffill()

#     # no column loop — pass full panel into signal generator
#     signals      = strat.generate_signals(price_df)
#     results_df, metrics = backtest_multi_asset(price_df, signals, tc)

#     # save results
#     os.makedirs(os.path.dirname(out), exist_ok=True)
#     results_df.to_csv(out)
#     df = results_df.copy()
#     df = df.reset_index()
#     # Plot equity curve
#     plt.figure(figsize=(12,6))
#     plt.plot(df["Date"], df["equity_curve"], label="Equity Curve", linewidth=2)
#     plt.title("Equity Curve")
#     plt.xlabel("Date")
#     plt.ylabel("Equity")
#     plt.legend()
#     plt.grid(True)
#     plt.show()

#     # Plot portfolio returns
#     plt.figure(figsize=(12,6))
#     plt.bar(df["Date"], df["portfolio_return"], width=1.0, label="Daily Returns")
#     plt.title("Portfolio Returns")
#     plt.xlabel("Date")
#     plt.ylabel("Return")
#     plt.legend()
#     plt.grid(True, axis="y")
#     plt.show()
#     # --- Distribution of daily returns ---
#     plt.figure(figsize=(10,6))
#     sns.histplot(df["portfolio_return"], bins=50, kde=True, stat="density")
#     plt.title("Distribution of Daily Returns")
#     plt.xlabel("Daily Return")
#     plt.ylabel("Density")
#     plt.grid(True)
#     plt.show()

#     # --- Summary statistics ---
#     rets = df["portfolio_return"].dropna()

#     stats = {
#         "Mean": rets.mean(),
#         "Std Dev": rets.std(),
#         "Skewness": skew(rets),
#         "Kurtosis": kurtosis(rets, fisher=True),  # excess kurtosis
#         "Min": rets.min(),
#         "Max": rets.max(),
#         "5% Quantile": np.percentile(rets, 5),
#         "1% Quantile": np.percentile(rets, 1),
#         "Median": rets.median(),
#     }

#     print("\n[Daily Return Distribution Stats]")
#     for k, v in stats.items():
#         print(f"{k:>12}: {v:.6f}")
#     print("[✓] Equity curve saved")
#     print(metrics)

# if __name__ == "__main__":
#     p = argparse.ArgumentParser("Run portfolio-level strategy")
#     p.add_argument("--start",   default="2000-01-01")
#     p.add_argument("--end",     default="2021-01-01")
#     p.add_argument("--tc",      default=0.0005, type=float)
#     p.add_argument("--strategy", default="portfolio_risk_scaled",
#                    choices=list(STRATEGY_REGISTRY.keys()))
#     p.add_argument("--out", default="results/portfolio_trend_mask.csv")
#     args = p.parse_args()

#     main(args.start, args.end, args.tc, args.strategy, args.out)

from lib import STRATEGY_REGISTRY
from lib.backtester.backtester import backtest_multi_asset
import pandas as pd, argparse, os
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import skew, kurtosis, norm, jarque_bera

# ---------- helpers ----------
def ensure_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with a guaranteed 'Date' datetime column."""
    out = df.copy()
    if isinstance(out.index, pd.DatetimeIndex):
        out = out.reset_index()
        # index name may be None; enforce "Date"
        out = out.rename(columns={out.columns[0]: "Date"})
    elif "Date" not in out.columns:
        # assume first col is date-like if index was already a column
        out = out.rename(columns={out.columns[0]: "Date"})
    out["Date"] = pd.to_datetime(out["Date"])
    return out

def cvar_empirical(x: pd.Series, p: float) -> float:
    """Empirical Expected Shortfall at tail prob p (e.g., p=0.05 -> 5%)."""
    q = np.percentile(x, 100 * p)
    tail = x[x <= q]
    return float(tail.mean()) if len(tail) else np.nan

def print_block(title: str, d: dict):
    print(f"\n[{title}]")
    for k, v in d.items():
        if isinstance(v, (float, np.floating)):
            print(f"{k:>18}: {v:.6f}")
        else:
            print(f"{k:>18}: {v}")

def main(start: str, end: str, tc: float, strategy_name: str, out: str,
         save_plots: bool = False):
    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    strat        = strategy_cls()

    price_df = pd.read_parquet("data/panel.parquet")

    # Drop columns with >10% NaNs; forward-fill the rest
    threshold = 0.10
    price_df = price_df.loc[:, price_df.isnull().mean() <= threshold].ffill()

    # Generate signals & backtest
    signals = strat.generate_signals(price_df)
    results_df, metrics = backtest_multi_asset(price_df, signals, tc)

    # Persist results (with explicit Date column)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df = ensure_date_column(results_df)
    df.to_csv(out, index=False)

    # ---------- Equity curve ----------
    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"], df["equity_curve"], linewidth=2, label="Equity Curve")
    plt.title("Equity Curve")
    plt.xlabel("Date"); plt.ylabel("Equity")
    plt.grid(True); plt.legend()
    if save_plots: plt.savefig(out.replace(".csv", "_equity.png"), dpi=150, bbox_inches="tight")
    plt.show()

    # ---------- Daily returns (bars) ----------
    plt.figure(figsize=(12, 6))
    plt.bar(df["Date"], df["portfolio_return"], width=1.0, label="Daily Returns")
    plt.title("Portfolio Returns")
    plt.xlabel("Date"); plt.ylabel("Return")
    plt.grid(True, axis="y"); plt.legend()
    if save_plots: plt.savefig(out.replace(".csv", "_returns.png"), dpi=150, bbox_inches="tight")
    plt.show()

    # ---------- Distribution + normal overlay ----------
    rets = pd.Series(df["portfolio_return"].astype(float)).dropna()
    mu, sd = float(rets.mean()), float(rets.std())

    plt.figure(figsize=(10, 6))
    # histogram (density)
    bins = 60
    counts, edges, _ = plt.hist(rets, bins=bins, density=True, alpha=0.6, label="Empirical")
    # normal fit overlay
    x = np.linspace(rets.min(), rets.max(), 400)
    plt.plot(x, norm.pdf(x, mu, sd), linestyle="--", label="Normal fit")
    plt.title("Daily Return Distribution (with Normal Fit)")
    plt.xlabel("Daily Return"); plt.ylabel("Density")
    plt.grid(True); plt.legend()
    if save_plots: plt.savefig(out.replace(".csv", "_dist.png"), dpi=150, bbox_inches="tight")
    plt.show()

    # ---------- Stats ----------
    ex_kurt = kurtosis(rets, fisher=True)            # excess
    var95   = np.percentile(rets, 5)
    var99   = np.percentile(rets, 1)
    cvar95  = cvar_empirical(rets, 0.05)
    cvar99  = cvar_empirical(rets, 0.01)
    downside = rets[rets < 0]
    down_sd  = float(downside.std()) if len(downside) else np.nan
    sortino  = (mu * 252) / (down_sd * np.sqrt(252)) if (down_sd and down_sd > 0) else np.nan
    # payoff metrics
    hit_rate = float((rets > 0).mean())
    avg_up   = float(rets[rets > 0].mean()) if (rets > 0).any() else np.nan
    avg_dn   = float(rets[rets <= 0].mean()) if (rets <= 0).any() else np.nan
    profit_factor = (rets[rets > 0].sum() / abs(rets[rets <= 0].sum())) if (rets[rets <= 0].sum() != 0) else np.nan
    # diagnostics
    jb_stat, jb_p = jarque_bera(rets)
    acf1 = rets.autocorr(lag=1)

    core = {
        "Mean": mu,
        "Std Dev": sd,
        "Skewness": skew(rets),
        "Excess Kurtosis": ex_kurt,
        "Min": float(rets.min()),
        "Max": float(rets.max()),
        "VaR 95%": float(var95),
        "VaR 99%": float(var99),
        "CVaR 95%": float(cvar95),
        "CVaR 99%": float(cvar99),
        "Median": float(rets.median()),
    }
    downside_block = {
        "Downside StDev": down_sd,
        "Sortino (ann.)": sortino,
        "Tail Ratio": (avg_up / abs(avg_dn)) if (avg_dn and avg_dn < 0) else np.nan,
        "Hit Rate": hit_rate,
        "Avg Up Day": avg_up,
        "Avg Down Day": avg_dn,
        "Profit Factor": float(profit_factor) if profit_factor == profit_factor else np.nan,  # NaN-safe
    }
    diag = {"Jarque–Bera p": float(jb_p), "ACF(1)": float(acf1)}

    print_block("Daily Return Stats", core)
    print_block("Downside / Tail", downside_block)
    print_block("Diagnostics", diag)

    print("\n[✓] Equity curve saved")
    print(metrics)

if __name__ == "__main__":
    p = argparse.ArgumentParser("Run portfolio-level strategy")
    p.add_argument("--start",   default="2000-01-01")
    p.add_argument("--end",     default="2021-01-01")
    p.add_argument("--tc",      default=0.0005, type=float)
    p.add_argument("--strategy", default="portfolio_risk_scaled",
                   choices=list(STRATEGY_REGISTRY.keys()))
    p.add_argument("--out", default="results/portfolio_trend_mask.csv")
    p.add_argument("--save_plots", action="store_true", help="Save plots to files next to CSV")
    args = p.parse_args()

    main(args.start, args.end, args.tc, args.strategy, args.out, save_plots=args.save_plots)
