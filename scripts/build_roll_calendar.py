#!/usr/bin/env python
"""
Build a futures roll calendar for every futures market in config.universe.

For every contract of every instrument it writes the first notice day (physically
delivered contracts only), the last trading day, and a Carver-style roll date:
5 business days before whichever of first-notice / last-trade comes first.

Exchange rules are encoded per instrument. Business days skip weekends, US federal
holidays and Good Friday; non-US exchange holidays are not modelled, so dates for
EUREX / HKEX / ICE Europe contracts can be off by a day around local holidays.

Usage
-----
python scripts/build_roll_calendar.py --out data/roll_calendar.csv
"""
import argparse
import os

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar, GoodFriday, AbstractHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

START_YEAR, END_YEAR = 2004, 2026
ROLL_OFFSET = 5          # business days before first-notice / last-trade
MONTH_CODES = "FGHJKMNQUVXZ"


class _ExchangeHolidays(AbstractHolidayCalendar):
    rules = USFederalHolidayCalendar.rules + [GoodFriday]


BDAY = CustomBusinessDay(calendar=_ExchangeHolidays())


def _bdays(start, end):
    return pd.date_range(start, end, freq=BDAY)


def _last_bday(year, month):
    return _bdays(pd.Timestamp(year, month, 1), pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0))[-1]


def _first_bday(year, month):
    return _bdays(pd.Timestamp(year, month, 1), pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0))[0]


def _prev_month(year, month, n=1):
    p = pd.Timestamp(year, month, 1) - pd.DateOffset(months=n)
    return p.year, p.month


def _nth_weekday(year, month, weekday, n):
    days = pd.date_range(pd.Timestamp(year, month, 1), periods=31, freq="D")
    days = days[(days.month == month) & (days.weekday == weekday)]
    return days[n - 1]


def _on_or_before_bday(day):
    return day if BDAY.is_on_offset(day) else day - BDAY


# ---- last-trading-day rules ---------------------------------------------
def ltd_third_friday(y, m):            # CME / EUREX equity index
    return _on_or_before_bday(_nth_weekday(y, m, 4, 3))


def ltd_nikkei(y, m):                  # CME Nikkei: business day before 2nd Friday
    return _nth_weekday(y, m, 4, 2) - BDAY


def ltd_hsi(y, m):                     # HKEX: second-last business day of month
    return _last_bday(y, m) - BDAY


def ltd_treasury_long(y, m):           # ZN/ZB/UB: 7 bdays before last bday of month
    return _last_bday(y, m) - 7 * BDAY


def ltd_treasury_short(y, m):          # ZT/ZF/FV: last bday of contract month
    return _last_bday(y, m)


def ltd_wti(y, m):                     # 3 bdays before the 25th of the prior month
    py, pm = _prev_month(y, m)
    d25 = pd.Timestamp(py, pm, 25)
    return _on_or_before_bday(d25) - 3 * BDAY if not BDAY.is_on_offset(d25) else d25 - 3 * BDAY


def ltd_brent(y, m):                   # ICE Brent: last bday of 2nd month before
    return _last_bday(*_prev_month(y, m, 2))


def ltd_prev_month_end(y, m):          # RBOB, heating oil, sugar
    return _last_bday(*_prev_month(y, m))


def ltd_natgas(y, m):                  # 3 bdays before first calendar day of month
    return pd.Timestamp(y, m, 1) - 3 * BDAY


def ltd_grain(y, m):                   # CBOT grains: bday before the 15th
    return pd.Timestamp(y, m, 15) - BDAY


def ltd_metal(y, m):                   # COMEX: 3rd last bday of contract month
    return _last_bday(y, m) - 2 * BDAY


def ltd_coffee(y, m):                  # ICE coffee: 8 bdays before last bday of month
    return _last_bday(y, m) - 8 * BDAY


def ltd_cocoa(y, m):                   # ICE cocoa: 11 bdays before last bday of month
    return _last_bday(y, m) - 11 * BDAY


def ltd_cotton(y, m):                  # ICE cotton: 17 bdays before last bday of month
    return _last_bday(y, m) - 17 * BDAY


def ltd_fx(y, m):                      # CME FX: 2 bdays before 3rd Wednesday
    return _nth_weekday(y, m, 2, 3) - 2 * BDAY


def ltd_dairy(y, m):                   # CME dairy: bday before USDA class price release (~first week of next month)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return _first_bday(ny, nm) + 2 * BDAY


def ltd_qm(y, m):                      # E-mini crude: bday before the WTI last trade
    return ltd_wti(y, m) - BDAY


def ltd_qg(y, m):                      # E-mini nat gas: bday before the NG last trade
    return ltd_natgas(y, m) - BDAY


def ltd_oj(y, m):                      # ICE FCOJ: 14 bdays before last bday of month
    return _last_bday(y, m) - 14 * BDAY


def ltd_month_end(y, m):               # live cattle: last bday of contract month
    return _last_bday(y, m)


def ltd_feeder(y, m):                  # feeder cattle: last Thursday of month
    days = pd.date_range(pd.Timestamp(y, m, 1), pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0))
    return _on_or_before_bday(days[days.weekday == 3][-1])


def ltd_hogs(y, m):                    # lean hogs: 10th bday of contract month
    return _first_bday(y, m) + 9 * BDAY


# ---- first-notice-day rules (physically delivered only) -----------------
def fnd_prev_month_end(y, m):          # CBOT/COMEX/Treasuries: last bday of prior month
    return _last_bday(*_prev_month(y, m))


def fnd_coffee(y, m):                  # 7 bdays before first bday of delivery month
    return _first_bday(y, m) - 7 * BDAY


def fnd_cocoa(y, m):                   # 10 bdays before first bday of delivery month
    return _first_bday(y, m) - 10 * BDAY


def fnd_cotton(y, m):                  # 5 bdays before first bday of delivery month
    return _first_bday(y, m) - 5 * BDAY


QUARTERLY = (3, 6, 9, 12)
MONTHLY = tuple(range(1, 13))

# ticker: (description, contract months, last-trade rule, first-notice rule or None)
SPECS = {
    "ES=F": ("S&P 500 E-mini", QUARTERLY, ltd_third_friday, None),
    "NQ=F": ("Nasdaq 100 E-mini", QUARTERLY, ltd_third_friday, None),
    "YM=F": ("Dow E-mini", QUARTERLY, ltd_third_friday, None),
    "RTY=F": ("Russell 2000 E-mini", QUARTERLY, ltd_third_friday, None),
    "NIY=F": ("Nikkei 225 (JPY)", QUARTERLY, ltd_nikkei, None),
    "HSI=F": ("Hang Seng", MONTHLY, ltd_hsi, None),
    "FDAX=F": ("DAX", QUARTERLY, ltd_third_friday, None),
    "FCHI=F": ("CAC 40", MONTHLY, ltd_third_friday, None),
    "STOXX50E=F": ("Euro Stoxx 50", QUARTERLY, ltd_third_friday, None),
    "ZB=F": ("30y T-Bond", QUARTERLY, ltd_treasury_long, fnd_prev_month_end),
    "ZN=F": ("10y T-Note", QUARTERLY, ltd_treasury_long, fnd_prev_month_end),
    "ZF=F": ("5y T-Note", QUARTERLY, ltd_treasury_short, fnd_prev_month_end),
    "ZT=F": ("2y T-Note", QUARTERLY, ltd_treasury_short, fnd_prev_month_end),
    "UB=F": ("Ultra T-Bond", QUARTERLY, ltd_treasury_long, fnd_prev_month_end),
    "FV=F": ("5y T-Note (alt)", QUARTERLY, ltd_treasury_short, fnd_prev_month_end),
    "CL=F": ("WTI crude", MONTHLY, ltd_wti, None),
    "BZ=F": ("Brent crude", MONTHLY, ltd_brent, None),
    "RB=F": ("RBOB gasoline", MONTHLY, ltd_prev_month_end, None),
    "NG=F": ("Natural gas", MONTHLY, ltd_natgas, None),
    "HO=F": ("Heating oil", MONTHLY, ltd_prev_month_end, None),
    "GC=F": ("Gold", (2, 4, 6, 8, 10, 12), ltd_metal, fnd_prev_month_end),
    "SI=F": ("Silver", (3, 5, 7, 9, 12), ltd_metal, fnd_prev_month_end),
    "HG=F": ("Copper", (3, 5, 7, 9, 12), ltd_metal, fnd_prev_month_end),
    "PL=F": ("Platinum", (1, 4, 7, 10), ltd_metal, fnd_prev_month_end),
    "PA=F": ("Palladium", QUARTERLY, ltd_metal, fnd_prev_month_end),
    "ZC=F": ("Corn", (3, 5, 7, 9, 12), ltd_grain, fnd_prev_month_end),
    "ZW=F": ("Wheat", (3, 5, 7, 9, 12), ltd_grain, fnd_prev_month_end),
    "ZS=F": ("Soybeans", (1, 3, 5, 7, 8, 9, 11), ltd_grain, fnd_prev_month_end),
    "KC=F": ("Coffee", (3, 5, 7, 9, 12), ltd_coffee, fnd_coffee),
    "SB=F": ("Sugar #11", (3, 5, 7, 10), ltd_prev_month_end, None),
    # expanded universe (YF_TICKERS_31)
    "NKD=F": ("Nikkei 225 (USD)", QUARTERLY, ltd_nikkei, None),
    "KE=F": ("KC HRW wheat", (3, 5, 7, 9, 12), ltd_grain, fnd_prev_month_end),
    "ZL=F": ("Soybean oil", (1, 3, 5, 7, 8, 9, 10, 12), ltd_grain, fnd_prev_month_end),
    "ZM=F": ("Soybean meal", (1, 3, 5, 7, 8, 9, 10, 12), ltd_grain, fnd_prev_month_end),
    "CC=F": ("Cocoa", (3, 5, 7, 9, 12), ltd_cocoa, fnd_cocoa),
    "CT=F": ("Cotton #2", (3, 5, 7, 10, 12), ltd_cotton, fnd_cotton),
    "OJ=F": ("Orange juice (FCOJ)", (1, 3, 5, 7, 9, 11), ltd_oj, None),
    # 35-market comparison sets (YF_TICKERS_35_BONDS / YF_TICKERS_35_NOBONDS)
    "ZQ=F": ("30-day fed funds", MONTHLY, ltd_treasury_short, None),
    "6E=F": ("Euro FX", QUARTERLY, ltd_fx, None),
    "6J=F": ("Japanese yen", QUARTERLY, ltd_fx, None),
    "6B=F": ("British pound", QUARTERLY, ltd_fx, None),
    "ZO=F": ("Oats", (3, 5, 7, 9, 12), ltd_grain, fnd_prev_month_end),
    "ZR=F": ("Rough rice", (1, 3, 5, 7, 9, 11), ltd_grain, fnd_prev_month_end),
    "QM=F": ("E-mini crude", MONTHLY, ltd_qm, None),
    "QG=F": ("E-mini nat gas", MONTHLY, ltd_qg, None),
    "EH=F": ("Ethanol", MONTHLY, ltd_metal, None),
    "CB=F": ("Butter (cash-settled)", MONTHLY, ltd_dairy, None),
    "DC=F": ("Class III milk", MONTHLY, ltd_dairy, None),
    "LE=F": ("Live cattle", (2, 4, 6, 8, 10, 12), ltd_month_end, None),
    "GF=F": ("Feeder cattle", (1, 3, 4, 5, 8, 9, 10, 11), ltd_feeder, None),
    "HE=F": ("Lean hogs", (2, 4, 5, 6, 7, 8, 10, 12), ltd_hogs, None),
}


def build_calendar() -> pd.DataFrame:
    rows = []
    for ticker, (name, months, ltd_rule, fnd_rule) in SPECS.items():
        root = ticker.split("=")[0]
        for y in range(START_YEAR, END_YEAR + 1):
            for m in months:
                ltd = ltd_rule(y, m)
                fnd = fnd_rule(y, m) if fnd_rule else pd.NaT
                deadline = min(ltd, fnd) if fnd_rule else ltd
                rows.append({
                    "ticker": ticker,
                    "name": name,
                    "contract": f"{root}{MONTH_CODES[m - 1]}{y % 100:02d}",
                    "contract_month": f"{y}-{m:02d}",
                    "first_notice": fnd,
                    "last_trade": ltd,
                    "roll_date": deadline - ROLL_OFFSET * BDAY,
                })
    cal = pd.DataFrame(rows).sort_values(["ticker", "last_trade"]).reset_index(drop=True)
    for c in ("first_notice", "last_trade", "roll_date"):
        cal[c] = pd.to_datetime(cal[c]).dt.date
    return cal


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/roll_calendar.csv")
    args = p.parse_args()
    cal = build_calendar()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    cal.to_csv(args.out, index=False)
    print(f"[ok] {len(cal)} contracts across {cal.ticker.nunique()} instruments -> {args.out}")
