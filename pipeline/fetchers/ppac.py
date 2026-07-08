"""
PPAC petroleum-products consumption fetcher — LIVE. Populates: fuel (MMT, monthly).

Source (verified working, Jul 2026):
  * POST https://ppac.gov.in/AjaxController/getConsumptionPetroleumProductsData
    form fields: financialYear=YYYY-YYYY, reportBy=1 (quantity, '000 MT),
    pageId=43. This is the JSON backend of the public table at
    https://ppac.gov.in/consumption/products-wise (no auth, no captcha).
  * Response: {"result": {"1": {"title": "LPG", "april": 2192, ...}, ...}};
    the row whose title contains TOTAL (it arrives HTML-wrapped as
    '<b id="lupdateddate">TOTAL</b>') is total POL consumption per month in
    TMT ('000 MT). Divide by 1000 -> MMT. Trailing note rows carry titles
    like "i) All figures are provisional." — filter by title, not position.

Quirks:
  * Months of the in-progress FY that haven't printed yet come back as "".
  * Figures are provisional and revise (Jun'26 LPG: 2,184 TMT in the flash
    PDF vs 2,188 in this API two days later). Private-import months are
    prorated until actuals land (per the API's own note rows).
  * The monthly "PPAC Flash Report on Oil & Gas" PDF covers only 4 products —
    not a substitute for the TOTAL row.

Verification performed (Jul 2026):
  * Jun 2026 TOTAL = 19,424 TMT = 19.42 MMT, matching press coverage of the
    PPAC release ("19.42 million metric tonnes in June, down from 20.18 mmt
    in May", -3.1% YoY vs 20,042 TMT in Jun 2025 — 5paisa/PTI, Jul 2026) and
    the API's own note: "Domestic POL consumption for Jun'26 registered a
    de-growth of 3.1 % on YoY basis."

Writes data/live/fuel.json: {"freq": "M", "obs": [["YYYY-MM-01", MMT], ...]}
"""
import json
import time
from pathlib import Path

import requests

API = "https://ppac.gov.in/AjaxController/getConsumptionPetroleumProductsData"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0",
     "X-Requested-With": "XMLHttpRequest"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
START_FY = 2023            # FY 2023-24 onward (API has history to 1998-99)

# FY month order -> calendar (month_name, offset_years_from_fy_start)
FY_MONTHS = [("april", 4, 0), ("may", 5, 0), ("june", 6, 0), ("july", 7, 0),
             ("august", 8, 0), ("september", 9, 0), ("october", 10, 0),
             ("november", 11, 0), ("december", 12, 0), ("january", 1, 1),
             ("february", 2, 1), ("march", 3, 1)]


def fetch():
    print("PPAC consumption pull:")
    from datetime import date
    today = date.today()
    fy_last = today.year if today.month >= 4 else today.year - 1
    obs = {}
    for fy in range(START_FY, fy_last + 1):
        r = requests.post(API, headers=H, timeout=60,
                          data={"financialYear": f"{fy}-{fy + 1}",
                                "reportBy": 1, "pageId": 43})
        r.raise_for_status()
        rows = r.json().get("result") or {}
        total = next((v for v in rows.values()
                      if "TOTAL" in v.get("title", "").upper()), None)
        if not total:
            print(f"  ! FY{fy}: no TOTAL row")
            continue
        for name, cal_m, off in FY_MONTHS:
            v = total.get(name)
            if v in ("", None):
                continue
            mmt = round(float(v) / 1000, 3)
            if 10 < mmt < 30:                     # MMT sanity band
                obs[f"{fy + off}-{cal_m:02d}-01"] = mmt
        time.sleep(0.4)
    LIVE.mkdir(parents=True, exist_ok=True)
    out = sorted(obs.items())
    (LIVE / "fuel.json").write_text(
        json.dumps({"freq": "M", "obs": [[d, v] for d, v in out]}))
    print(f"  fuel: {len(out)} months, latest {out[-1][0]} = {out[-1][1]}")


if __name__ == "__main__":
    fetch()
