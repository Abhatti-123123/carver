from lib import STRATEGY_REGISTRY
from lib.backtester.backtester import backtest_multi_asset
import pandas as pd, argparse, os

def main(start: str, end: str, tc: float,
         strategy_name: str, out: str):

    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    strat        = strategy_cls()
    price_df     = pd.read_parquet("data/panel.parquet")

    # no column loop — pass full panel into signal generator
    signals      = strat.generate_signals(price_df)
    results_df, metrics = backtest_multi_asset(price_df, signals, tc)

    # save results
    os.makedirs(os.path.dirname(out), exist_ok=True)
    results_df.to_csv(out)
    print("[✓] Equity curve saved")
    print(metrics)

if __name__ == "__main__":
    p = argparse.ArgumentParser("Run portfolio-level strategy")
    p.add_argument("--start",   default="2020-01-01")
    p.add_argument("--end",     default="2021-01-01")
    p.add_argument("--tc",      default=0.0005, type=float)
    p.add_argument("--strategy", default="portfolio_risk_scaled",
                   choices=list(STRATEGY_REGISTRY.keys()))
    p.add_argument("--out", default="results/portfolio.csv")
    args = p.parse_args()

    main(args.start, args.end, args.tc, args.strategy, args.out)
