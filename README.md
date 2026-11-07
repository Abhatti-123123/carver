# Carver-style systematic futures: why diversification matters

A replication and extension of Robert Carver's *Advanced Futures Trading Strategies* on public Yahoo
Finance data: 31 liquid futures, 2005 – mid-2025, 5 bp cost per unit of position change.

| Final system (S6/7), 31 markets | Sharpe | CAGR | Vol | Max drawdown |
|---|---|---|---|---|
| 2005–2025 | 1.04 | 11.8% | 11.3% | −26.9% |
| In-sample 2005–2016 (settings chosen here) | 0.89 | 9.4% | 10.7% | −20.3% |
| Out-of-sample 2017–2025 | 1.23 | 15.2% | 12.1% | −26.9% |
| Since 2020 | 1.48 | 19.8% | 12.7% | −13.0% |

Trend-strength sizing adds 0.44% a month over the risk-scaled portfolio (t = 3.13, HAC).
Presentation: `carver_presentation.pptx`.

## The strategies

Every strategy is a buy-and-hold variant: a zero signal means *hold the last size*, never *sell*.

| | Class | What it does |
|---|---|---|
| S1 | `BuyAndHoldStrategy` | one fixed unit long per market |
| S2 | `RiskScaledBuyAndHoldStrategy` | size each market to a 20% vol target (20-day realised vol) |
| S3 | `VariableRiskScaledBuyAndHoldStrategy` | vol target blended from fast and slow EWMA vol |
| S4 | `PortfolioRiskScaledStrategy(trend_mode="none")` | inverse-vol weights, whole book rescaled to the vol target with 60/120-day covariance; scale factor smoothed (20-day half-life) |
| S6/7 | `PortfolioRiskScaledStrategy()` — the final system | S4 positions × trend forecast / 10. Forecast = EWMAC(64,256) ÷ price vol × 1.9, capped ±20, floored at 0 (long-only), re-sized when it moves > 5% |

## Reproduce

```bash
pip install -e .
python scripts/build_roll_calendar.py --out data/roll_calendar.csv
python scripts/build_panel.py --universe 31 --out data/panel_31.parquet          # also: original, 35_bonds, 35_nobonds
python scripts/run_results.py --data data --out results/final.json              # ladder, alpha, vol dial, universes, detail
python scripts/select_settings.py --panel data/panel_31.parquet                  # how the settings were chosen (2005-16 only)
python scripts/build_panel.py --universe crypto --start 2023-01-01 --end 2025-11-28 --out data/panel_crypto.parquet
python scripts/crypto_run.py --panel data/panel_crypto.parquet
python scripts/dltm_app1.py --dltm <folder with d* series>                       # dLTM extension
python scripts/build_presentation.py carver_presentation.pptx
```

`scripts/run_portfolio.py` runs one configuration and `scripts/check_alpha.py` regresses any two result CSVs.
Yahoo revises history and drops contracts, so a fresh download can move the numbers slightly.

## Data and limitations

- Yahoo front-month series. Contract-roll days are found from an exchange roll calendar and their return is
  set to zero (`lib/rolls.py`); true back-adjustment would need individual contract prices.
- Flat 5 bp cost on every market; no slippage or capacity model; no carry strategies.
- Only markets Yahoo still lists back to 2005. The 31-market universe was chosen after comparing others.
- Sharpe uses a 0% risk-free rate: futures prices embed financing, so futures P&L is already an excess return.

See `notes.txt` for research notes.
