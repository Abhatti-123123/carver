"""Performance statistics and the alpha regression used throughout."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st


def perf(r: pd.Series) -> dict:
    """Total return, CAGR, vol, Sharpe (0% risk-free: futures P&L is already an excess return), max drawdown."""
    eq = (1 + r).cumprod()
    return {"total": eq.iloc[-1] - 1, "cagr": eq.iloc[-1] ** (252 / len(r)) - 1, "vol": r.std() * np.sqrt(252),
            "sharpe": r.mean() / r.std() * np.sqrt(252), "mdd": (eq / eq.cummax() - 1).min()}


def windows(r: pd.Series, is_end: str = "2016-12-31", oos_start: str = "2017-01-01") -> dict:
    return {"full": perf(r), "is": perf(r.loc[:is_end]), "oos": perf(r.loc[oos_start:]),
            "since_2020": perf(r.loc["2020":])}


def distribution(r: pd.Series) -> dict:
    q = lambda a: float(np.percentile(r, a))
    return {"mean": r.mean(), "median": r.median(), "daily_vol": r.std(), "skew": st.skew(r),
            "excess_kurtosis": st.kurtosis(r), "worst": r.min(), "best": r.max(),
            "var95": q(5), "var99": q(1), "cvar95": r[r <= q(5)].mean(), "cvar99": r[r <= q(1)].mean(),
            "sortino": r.mean() * 252 / (r[r < 0].std() * np.sqrt(252)),
            "tail_ratio": abs(q(95) / q(5)), "hit_rate": (r > 0).mean(),
            "avg_up": r[r > 0].mean(), "avg_down": r[r < 0].mean(),
            "profit_factor": r[r > 0].sum() / -r[r < 0].sum(),
            "jarque_bera_p": st.jarque_bera(r).pvalue, "acf1": r.autocorr(1)}


def alpha(strategy: pd.Series, benchmark: pd.Series, hac_lags: int = 6) -> dict:
    """Regress compounded monthly strategy returns on the benchmark; HAC (Newey-West) standard errors."""
    df = pd.concat([(1 + strategy).resample("ME").prod() - 1,
                    (1 + benchmark).resample("ME").prod() - 1], axis=1).dropna()
    df.columns = ["strategy", "benchmark"]
    m = sm.OLS(df["strategy"], sm.add_constant(df["benchmark"])).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return {"alpha": m.params["const"], "t": m.tvalues["const"], "p": m.pvalues["const"],
            "beta": m.params["benchmark"], "r2": m.rsquared}
