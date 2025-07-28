VENDOR  = "POLYGON"     

SYMBOLS = [
    # Equity index
    "CME_ES1",    "CME_NQ1",    "EUREX_FDAX1",
    # Rates/Bonds
    "CME_TY1",    "CME_US1",    "EUREX_FGBL1",
    # Commodities
    "CME_CL1",    "CME_GC1",    "ICE_KC1", "ICE_SB1",
]

SYMBOLS_POLY = [
  "C:ES",    # CME_ES1 → ES
  "C:NQ",   # CME_NQ1 → NQ
  "C:FDAX",  # EUREX_FDAX1 → FDAX
  "C:TY",    # CME_TY1 → TY
  "C:US",    # CME_US1 → US
  "C:FGBL",  # EUREX_FGBL1 → FGBL
  "C:CL",    # CME_CL1 → CL
  "C:GC",    # CME_GC1 → GC
  "C:KC",    # ICE_KC1 → KC
  "C:SB"     # ICE_SB1 → SB
]

YF_TICKERS = [
    "ES=F",   # E-mini S&P 500 futures      :contentReference[oaicite:0]{index=0}
    "NQ=F",   # E-mini Nasdaq 100 futures   :contentReference[oaicite:1]{index=1}
    "ZB=F",   # 30-Year U.S. T-Bond futures :contentReference[oaicite:3]{index=3}
    "CL=F",   # Crude Oil futures
    "GC=F",   # Gold futures
    "KC=F",   # Coffee futures
    "SB=F",   # Sugar futures
    "NG=F"    # Natural gas futures
]
# YF_TICKERS = [
#     "ZB=F",   # E-mini S&P 500 futures      :contentReference[oaicite:0]{index=0}
#     "ES=F",   # E-mini S&P 500 futures      :contentReference[oaicite:0]{index=0}
# ]
