"""Market universes (Yahoo Finance tickers)."""

# Original list. FDAX, FCHI, STOXX50E, HSI and FV are no longer served by Yahoo, and RTY / UB / BZ / PL
# fail the 10% missing-data rule from 2005, leaving 21 usable markets.
YF_TICKERS = [
    "ES=F", "NQ=F", "YM=F", "RTY=F", "NIY=F", "HSI=F", "FDAX=F", "FCHI=F", "STOXX50E=F",   # equity index
    "ZB=F", "ZN=F", "ZF=F", "ZT=F", "UB=F", "FV=F",                                         # rates
    "CL=F", "BZ=F", "RB=F", "NG=F", "HO=F",                                                 # energy
    "GC=F", "SI=F", "HG=F", "PL=F", "PA=F",                                                 # metals
    "ZC=F", "ZW=F", "ZS=F", "KC=F", "SB=F",                                                 # agriculture
]

# Final universe: the 21 usable originals plus 10 markets from sectors with long-run drift.
YF_TICKERS_31 = [
    "ES=F", "NQ=F", "YM=F", "NIY=F", "NKD=F",                  # equity index
    "ZT=F", "ZF=F", "ZN=F", "ZB=F",                            # rates
    "CL=F", "RB=F", "NG=F", "HO=F",                            # energy
    "GC=F", "SI=F", "HG=F", "PA=F",                            # metals
    "ZC=F", "ZW=F", "KE=F", "ZS=F", "ZL=F", "ZM=F",            # grains / oilseeds
    "KC=F", "SB=F", "CC=F", "CT=F", "OJ=F",                    # softs
    "LE=F", "GF=F", "HE=F",                                    # livestock
]

# Two 35-market variants for the "more assets != more profit" comparison (both share the 27 non-bond markets).
_BASE_27 = [t for t in YF_TICKERS_31 if t not in ("ZT=F", "ZF=F", "ZN=F", "ZB=F")]
YF_TICKERS_35_BONDS = _BASE_27 + ["ZT=F", "ZF=F", "ZN=F", "ZB=F", "ZQ=F", "6E=F", "6J=F", "6B=F"]
YF_TICKERS_35_NOBONDS = _BASE_27 + ["ZO=F", "ZR=F", "QM=F", "QG=F", "EH=F", "PL=F", "CB=F", "DC=F"]

# Robustness check: liquid spot crypto (Jan 2023 - Nov 2025).
CRYPTO_TICKERS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD",
    "LINK-USD", "DOT-USD", "MATIC-USD", "TRX-USD", "LTC-USD", "UNI-USD", "APT-USD", "BTC=F", "ETH=F",
]

UNIVERSES = {
    "original": YF_TICKERS,
    "31": YF_TICKERS_31,
    "35_bonds": YF_TICKERS_35_BONDS,
    "35_nobonds": YF_TICKERS_35_NOBONDS,
    "crypto": CRYPTO_TICKERS,
}
