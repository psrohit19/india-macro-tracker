"""
FBIL G-Sec valuation fetcher — LIVE.
Populates: gsec10y (D, %).

FBIL's site (www.fbil.org.in) is an Angular SPA; the underlying JSON API
(base https://www.fbil.org.in/wasdm, discovered from the app bundle) is
open and needs no auth:

  GET /wasdm/gsec/fetchfiltered?fromDate=YYYY-M-D&toDate=YYYY-M-D
      &authenticated=false
      -> [{"processRunDate": "YYYY-MM-DD", "archive": ...}, ...] the list of
         published valuation days (weekends/holidays absent).
  GET /wasdm/gsec/downloadPublished?date=YYYY-MM-DD
      -> XLSX blob "FBIL GOI Prices including Par Yield ..." (a 500 JSON
         error for non-publication days).

The workbook's "Par Yield" sheet is the FBIL base/par yield curve; the row
with Tenor (Year) == 10 gives the constant-maturity 10Y in two columns:
YTM% semi-annual and annualized. The SEMI-ANNUAL column is the number the
RBI itself prints as "10-Year G-Sec Par Yield (FBIL)" in the WSS 'Ratios
and Rates' table (verified: WSS week-ended 19 Jun 2026 = 6.87 = FBIL
semi-annual; the annualized column read 6.98) — so that is what is stored.

Note: publication of the valuation files lags the market by a few working
days, so "latest" here can be ~1 week old.
"""
import json
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import openpyxl
import requests

SERIES_IDS = ["gsec10y"]
API = "https://www.fbil.org.in/wasdm"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0",
     "Referer": "https://www.fbil.org.in/"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def _published_dates(days_back=60):
    t = date.today()
    f = t - timedelta(days=days_back)
    r = requests.get(f"{API}/gsec/fetchfiltered",
                     params={"fromDate": f.isoformat(), "toDate": t.isoformat(),
                             "authenticated": "false"},
                     headers=H, timeout=90)
    r.raise_for_status()
    return sorted({e["processRunDate"] for e in r.json()})


def _par_yield_10y(day):
    r = requests.get(f"{API}/gsec/downloadPublished", params={"date": day},
                     headers=H, timeout=120)
    if r.content[:2] != b"PK":
        raise ValueError(f"no workbook for {day}")
    ws = openpyxl.load_workbook(BytesIO(r.content))["Par Yield"]
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == 10:
            return float(row[1])          # YTM% p.a. semi-annual
    raise ValueError(f"tenor-10 row missing for {day}")


def fetch(want=24):
    obs = {}
    for day in reversed(_published_dates()):
        if len(obs) >= want:
            break
        try:
            obs[day] = _par_yield_10y(day)
        except Exception as e:
            print(f"  gsec10y: {day} failed: {e}")
    if len(obs) < 14:
        print(f"  gsec10y: only {len(obs)} obs — NOT writing")
        return
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / "gsec10y.json").write_text(
        json.dumps({"freq": "D", "obs": [[d, v] for d, v in pairs]}))
    print(f"  gsec10y: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")


if __name__ == "__main__":
    fetch()
