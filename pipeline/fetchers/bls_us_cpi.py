"""
US CPI inflation fetcher — LIVE. Populates: us_cpi.

FRED (the catalog's preferred source) is unreachable from this box; the BLS
public API works UNAUTHENTICATED (verified Jul 2026):
    GET https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0
        ?startyear=YYYY&endyear=YYYY
CUUR0000SA0 = CPI-U, All items, U.S. city average, NOT seasonally adjusted —
the index behind the headline "x.x% annual inflation" print. YoY is computed
here as index[m] / index[m-12] - 1.

Quirks:
  * Oct 2025 index is published as "-" with footnote "Data unavailable due
    to the 2025 lapse in appropriations" (government shutdown). That month
    and its YoY (plus Oct 2026's YoY, which needs it as a base) are skipped.
  * Unregistered API access is rate-limited (~25 req/day) and capped at a
    10-year span per request — one request per run keeps us well inside.

Writes data/live/us_cpi.json: {"freq": "M", "obs": [["YYYY-MM-01", yoy], ...]}
"""
import json
from datetime import date
from pathlib import Path

import requests

API = "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
START_YEAR = 2022  # gives YoY from 2023 onward — plenty for the 12-mo avg


def fetch():
    r = requests.get(API, headers=H, timeout=45,
                     params={"startyear": str(START_YEAR),
                             "endyear": str(date.today().year)})
    r.raise_for_status()
    data = r.json()["Results"]["series"][0]["data"]
    idx = {}
    for row in data:
        if row["period"].startswith("M") and row["value"] not in ("-", ""):
            idx[(int(row["year"]), int(row["period"][1:]))] = float(row["value"])
    obs = []
    for (y, m), v in idx.items():
        prev = idx.get((y - 1, m))
        if prev:
            obs.append([f"{y}-{m:02d}-01", round((v / prev - 1) * 100, 1)])
    obs.sort()
    (LIVE / "us_cpi.json").write_text(json.dumps({"freq": "M", "obs": obs}))
    print("us_cpi", len(obs), "obs; last3:", obs[-3:])


if __name__ == "__main__":
    fetch()
