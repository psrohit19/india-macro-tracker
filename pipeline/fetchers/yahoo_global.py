"""
Global daily market data via Yahoo Finance chart API — LIVE.
Populates: brent, dxy, ust10y.

FRED (the catalog's preferred source) is unreachable from this box, and
stooq.com serves an anti-bot interstitial then denies CSV downloads, so
this fetcher uses https://query1.finance.yahoo.com/v8/finance/chart/{sym}
(unauthenticated, verified reachable Jul 2026):

  * brent  <- BZ=F      Brent crude front-month future (US$/bbl). Proxy for
                        the FRED/EIA Brent SPOT series — front-month tracks
                        spot within a few tens of cents outside extreme
                        contango/backwardation.
  * dxy    <- DX-Y.NYB  ICE US Dollar Index. NOTE: the catalog info text
                        prefers FRED's broad trade-weighted index; with FRED
                        blocked the tile carries classic EUR-heavy DXY,
                        which matches the tile's name/unit.
  * ust10y <- ^TNX      CBOE 10-Year Treasury Note yield index. Although
                        ^TNX is nominally 'yield*10', Yahoo's chart API
                        returns the yield in % directly (verified: meta
                        regularMarketPrice 4.529 on 2026-07-08) — no
                        divisor applied.

Daily closes, ~13 months of history per run (range=1y is plenty for the
dashboard's 1Y window; extend range= if the long-term view needs more).

Writes data/live/{id}.json: {"freq": "D", "obs": [["YYYY-MM-DD", val], ...]}
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

SYMBOLS = {          # series_id: (yahoo symbol, divisor, round digits)
    "brent":  ("BZ=F", 1, 2),
    "dxy":    ("DX-Y.NYB", 1, 2),
    "ust10y": ("^TNX", 1, 2),
}


def fetch():
    for sid, (sym, div, nd) in SYMBOLS.items():
        r = requests.get(API.format(sym), headers=H, timeout=45,
                         params={"range": "1y", "interval": "1d"})
        r.raise_for_status()
        res = r.json()["chart"]["result"][0]
        ts = res["timestamp"]
        closes = res["indicators"]["quote"][0]["close"]
        obs = []
        for t, c in zip(ts, closes):
            if c is None:
                continue
            d = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
            obs.append([d, round(c / div, nd)])
        # de-dup (last wins) & sort
        obs = sorted({d: v for d, v in obs}.items())
        obs = [[d, v] for d, v in obs]
        (LIVE / f"{sid}.json").write_text(json.dumps({"freq": "D", "obs": obs}))
        print(sid, len(obs), "obs; last2:", obs[-2:])


if __name__ == "__main__":
    fetch()
