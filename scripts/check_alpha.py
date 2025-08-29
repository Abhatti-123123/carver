import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np


# #This code compares returns of strategy to benchmark to check for alpha
# def analyze_alpha_beta(strategy_path, benchmark_path):
#     # Load CSVs with date index
#     strategy_df = pd.read_csv(strategy_path, index_col=0, parse_dates=True)
#     benchmark_df = pd.read_csv(benchmark_path, index_col=0, parse_dates=True)

#     # Extract daily returns
#     strategy_returns = strategy_df["portfolio_return"]
#     benchmark_returns = benchmark_df["portfolio_return"]

#     # Resample to monthly returns
#     monthly_strat = strategy_returns.resample("M").sum()
#     monthly_bench = benchmark_returns.resample("M").sum()

#     # Align and drop missing
#     df = pd.concat([monthly_strat, monthly_bench], axis=1).dropna()
#     df.columns = ["strategy", "benchmark"]

#     # Run OLS regression
#     X = sm.add_constant(df["benchmark"])
#     y = df["strategy"]
#     model = sm.OLS(y, X).fit()

#     # Extract regression stats
#     alpha = model.params["const"]
#     beta = model.params["benchmark"]
#     tstat = model.tvalues["const"]
#     pval  = model.pvalues["const"]

#     # Print results
#     print(f"Alpha: {alpha:.4%} per month  (t = {tstat:.2f}, p = {pval:.4f})")
#     print(f"Beta:  {beta:.2f}")

#     # Plot regression
#     plt.figure(figsize=(8, 6))
#     plt.scatter(df["benchmark"], df["strategy"], alpha=0.7, label="Monthly Data")
#     plt.plot(df["benchmark"], model.predict(X), color="red", label="Regression Line")
#     plt.xlabel("Benchmark Monthly Return")
#     plt.ylabel("Strategy Monthly Return")
#     plt.title("Monthly Return Regression: Strategy vs Benchmark")
#     plt.legend()
#     plt.grid(True)
#     plt.tight_layout()
#     plt.show()

def analyze_alpha_beta(strategy_path, benchmark_path):
    # Load CSVs with date index
    strategy_df = pd.read_csv(strategy_path, index_col=0, parse_dates=True)
    benchmark_df = pd.read_csv(benchmark_path, index_col=0, parse_dates=True)

    # Extract daily excess returns
    strategy_returns = strategy_df["portfolio_return"].astype(float)
    benchmark_returns = benchmark_df["portfolio_return"].astype(float)

    # Resample to monthly (compound, not sum)
    monthly_strat = (1 + strategy_returns).resample("M").prod() - 1
    monthly_bench = (1 + benchmark_returns).resample("M").prod() - 1

    # Align and drop missing
    df = pd.concat([monthly_strat, monthly_bench], axis=1).dropna()
    df.columns = ["strategy", "benchmark"]

    # Run OLS regression with HAC SEs
    X = sm.add_constant(df["benchmark"])
    y = df["strategy"]
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})

    # Extract regression stats
    alpha = model.params["const"]
    beta = model.params["benchmark"]
    tstat = model.tvalues["const"]
    pval  = model.pvalues["const"]

    # Print results
    print(f"Alpha: {alpha:.4%} per month  (t = {tstat:.2f}, p = {pval:.4f})")
    print(f"Alpha (annualized): {(1+alpha)**12 - 1:.2%}")
    print(f"Beta:  {beta:.2f}")
    print(f"R^2:   {model.rsquared:.3f}")

    # Plot regression
    plt.figure(figsize=(8, 6))
    plt.scatter(df["benchmark"], df["strategy"], alpha=0.7, label="Monthly Data")
    x_grid = np.linspace(df["benchmark"].min(), df["benchmark"].max(), 200)
    y_fit  = alpha + beta * x_grid
    plt.plot(x_grid, y_fit, color="red", label="Regression Line")
    plt.xlabel("Benchmark Monthly Excess Return")
    plt.ylabel("Strategy Monthly Excess Return")
    plt.title("Monthly Return Regression: Strategy vs Benchmark")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# === Usage ===
analyze_alpha_beta("results/portfolio_trend_mask.csv", "results/portfolio.csv")

# Alpha: 0.3514% per month  (t = 2.59, p = 0.0120)
# Beta:  1.00
