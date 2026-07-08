"""
Eight Core Industries (ICI) fetcher — LIVE. Populates: core8.

Source: Office of the Economic Adviser, DPIIT — https://eaindustry.nic.in/
The homepage links a full time-series workbook under eight_core_infra/,
e.g. Core_Industries_2011_12_20260622.xlsx (filename carries a YYYYMMDD
stamp that changes each release, so the link is re-scraped from the
homepage every run rather than hard-coded).

Workbook layout (verified Jul 2026):
  * sheet 'Index'      — monthly index levels, base 2011-12=100
  * sheet 'Growth (%)' — col A month (datetime for monthly rows; fiscal-year
    STRINGS like '2025-26(Apr-Mar)' for annual/cumulative rows — skip those),
    col B 'Overall Growth rate' = ICI combined YoY %, as printed by PIB.

Provisional prints get two scheduled revisions (1st and 3rd following
month), so the trailing months in the file supersede earlier press notes.

Writes data/live/core8.json: {"freq": "M", "obs": [["YYYY-MM-01", yoy], ...]}
"""
import io
import json
import re
from datetime import datetime
from pathlib import Path

import openpyxl
import requests

HOME = "https://eaindustry.nic.in/"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def _workbook_url():
    html = requests.get(HOME, headers=H, timeout=60, verify=True).text
    m = re.search(r'href="(eight_core_infra/Core_Industries_2011_12_\d+\.xlsx)"',
                  html)
    if not m:
        raise RuntimeError("ICI workbook link not found on eaindustry.nic.in")
    return HOME + m.group(1)


def fetch():
    xls = requests.get(_workbook_url(), headers=H, timeout=120).content
    ws = openpyxl.load_workbook(io.BytesIO(xls))["Growth (%)"]
    obs = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if isinstance(row[0], datetime) and isinstance(row[1], (int, float)):
            obs.append([row[0].strftime("%Y-%m-01"), round(float(row[1]), 1)])
    obs.sort()
    (LIVE / "core8.json").write_text(json.dumps({"freq": "M", "obs": obs}))
    print("core8", len(obs), "obs; last3:", obs[-3:])


if __name__ == "__main__":
    fetch()
