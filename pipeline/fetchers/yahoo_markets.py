"""
Yahoo Finance chart-API fetcher — LIVE. Populates: nifty, vix (daily closes).

NSE blocks unauthenticated bots and stooq.com sits behind a JS proof-of-work
challenge, so daily index levels come from Yahoo Finance's public chart API:

    https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=6mo&interval=1d

Symbols:  ^NSEI = Nifty 50,  ^INDIAVIX = India VIX.
Values are official NSE closes redistributed by Yahoo (verified Jul 2026
against press coverage of NSE closes). The response carries IST timestamps;
each bar is bucketed to its IST trading date. The current (unfinished) day
appears with regularMarketTime — it is included, then overwritten by the
next run once final. Null closes (holiday placeholder rows) are skipped.

nifty_pe has no Yahoo equivalent (NSE-proprietary computation) — seeded
separately, see data/live/nifty_pe.json.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SERIES_IDS = ["nifty", "vix"]
SYMBOLS = {"nifty": "^NSEI", "vix": "^INDIAVIX"}
API = "https://query1.finance.yahoo.com/v8/finance/chart/{}?range=6mo&interval=1d"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
IST = timezone(timedelta(hours=5, minutes=30))
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def _closes(symbol):
    r = requests.get(API.format(requests.utils.quote(symbol)), headers=H,
                     timeout=45)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]
    close = res["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, close):
        if c is not None:
            iso = datetime.fromtimestamp(t, IST).date().isoformat()
            out[iso] = round(float(c), 2)
    return out


def fetch():
    LIVE.mkdir(parents=True, exist_ok=True)
    for sid, sym in SYMBOLS.items():
        new = _closes(sym)
        f = LIVE / f"{sid}.json"
        obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
        obs.update(new)
        f.write_text(json.dumps({"freq": "D", "obs": sorted(obs.items())}))
        last = sorted(obs)[-1]
        print(f"  {sid}: {len(obs)} obs, latest {last} = {obs[last]:,.2f}")


if __name__ == "__main__":
    fetch()
