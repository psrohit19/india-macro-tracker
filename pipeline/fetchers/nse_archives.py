"""
NSE archives fetcher — LIVE. Populates: nifty_pe (daily, trailing P/E, x).

www.nseindia.com blocks unauthenticated bots, but the static archive host
nsearchives.nseindia.com serves the official daily index-close CSV without
cookies:

    https://nsearchives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv

Columns: Index Name, Index Date, Open/High/Low/Closing, ..., P/E, P/B,
Div Yield. The "Nifty 50" row's P/E column is NSE's official trailing
(consolidated-earnings) Nifty P/E. The same file carries the Nifty 50 close
and the India VIX close, which this repo sources from Yahoo (^NSEI,
^INDIAVIX — see yahoo_markets.py); values were cross-checked to match to
the paisa on 07-Jul-2026 (close 24,398.70, VIX 11.65, P/E 21.03).

Trading holidays/weekends simply have no file (404) and are skipped.
"""
import csv
import io
import json
from datetime import date, timedelta
from pathlib import Path

import requests

SERIES_IDS = ["nifty_pe"]
URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{}.csv"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def fetch(days_back=45):
    s = requests.Session()
    s.headers.update(H)
    f = LIVE / "nifty_pe.json"
    obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
    today = date.today()
    for k in range(days_back + 1):
        d = today - timedelta(days=k)
        iso = d.isoformat()
        if iso in obs or d.weekday() >= 5:
            continue
        r = s.get(URL.format(d.strftime("%d%m%Y")), timeout=30)
        if r.status_code != 200:
            continue                      # holiday or not yet published
        for row in csv.DictReader(io.StringIO(r.text)):
            if row["Index Name"].strip() == "Nifty 50":
                try:
                    obs[iso] = float(row["P/E"])
                except ValueError:
                    pass
                break
    LIVE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"freq": "D", "obs": sorted(obs.items())}))
    last = sorted(obs)[-1]
    print(f"  nifty_pe: {len(obs)} obs, latest {last} = {obs[last]}x")
    return obs


if __name__ == "__main__":
    fetch()
