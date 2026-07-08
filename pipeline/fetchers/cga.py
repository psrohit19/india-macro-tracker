"""
CGA monthly accounts fetcher — LIVE. Populates: fisc_def, capex.

Source: CGA "Union Government Accounts at a Glance" monthly HTML report:
    https://cga.nic.in/MonthlyReport/Published/{calendar_month}/{FY}.aspx
e.g. May 2026 (FY 2026-27) = /MonthlyReport/Published/5/2026-2027.aspx

Verified behaviour (Jul 2026):
  * The MonthDashboardReport list.aspx (.xlsm dashboard) grid is loaded via an
    ASP.NET UpdatePanel postback and exposes no direct file links — the
    MonthlyReport HTML pages above are the stable machine-readable route.
  * Pages are Word-exported HTML (MsoNormal spans). Each data row is:
    [sl no, item, ..., BE (Rs cr), Actuals up to month (Rs cr),
     % of Actuals to BE, (same % for corresponding prior-year period)].
  * Numbers appear without thousands separators; % cells like "9.6%"; the
    prior-year comparator sits in parentheses "(0.8%)".
  * Month index in URL = CALENDAR month number (1..12) paired with the fiscal
    year string, so March of FY25-26 is /3/2025-2026.aspx.
  * A month's page 404s / redirects to the shell page until published
    (last working day of the following month).

Series written (data/live/):
  fisc_def.json — Fiscal Deficit, FY-to-date, % of Budget Estimate (resets
                  each April; catalog unit "% of BE").
  capex.json    — Capital Expenditure, FY-to-date actuals, Rs lakh crore
                  (source table is Rs crore -> /1e5).
"""
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

BASE = "https://cga.nic.in/MonthlyReport/Published/{m}/{fy}.aspx"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
START = (2024, 4)          # first month pulled (Apr 2024, FY24-25)


def _fy(y, m):
    a = y if m >= 4 else y - 1
    return f"{a}-{a + 1}"


def _cells(html):
    """All td texts, in document order, tags stripped.

    NOTE: bs4/lxml both return ZERO <td> nodes for these Word-exported pages
    (an early unterminated conditional comment swallows the body), so cells
    are extracted with a raw regex instead."""
    tds = re.findall(r"<td[^>]*>(.*?)</td>", html, re.S | re.I)
    out = []
    for x in tds:
        x = re.sub(r"<[^>]+>", " ", x)
        x = x.replace("&nbsp;", " ").replace("\xa0", " ")
        out.append(" ".join(x.split()))
    return out


def _row(cells, label):
    """Return the numeric cells following the row-label cell."""
    for i, c in enumerate(cells):
        if re.sub(r"\(.*?\)", "", c).strip().lower().startswith(label.lower()):
            out = []
            for c2 in cells[i + 1:i + 8]:
                c2 = c2.replace(",", "").replace(" ", "").strip()
                if re.fullmatch(r"-?\d+(\.\d+)?%?", c2):
                    out.append(c2)
                if len(out) >= 3:
                    break
            return out
    return []


def _parse(html):
    """-> (fisc_def_pct_of_BE, capex_fytd_rs_cr) or (None, None)."""
    cells = _cells(html)
    fd = _row(cells, "Fiscal Deficit")
    cap = _row(cells, "Capital Expenditure")
    fd_pct = cap_cr = None
    # fd = [BE, actuals-to-date, pct%]  (pct cell carries the % sign)
    for c in fd:
        if c.endswith("%"):
            fd_pct = float(c[:-1])
            break
    if cap and len(cap) >= 2:
        cap_cr = float(cap[1])        # [BE, actuals, pct]
    return fd_pct, cap_cr


def fetch():
    print("CGA monthly accounts pull:")
    today = date.today()
    fisc, capex = {}, {}
    y, m = START
    while (y, m) <= (today.year, today.month):
        url = BASE.format(m=m, fy=_fy(y, m))
        try:
            r = requests.get(url, timeout=60, headers=H)
            if r.status_code == 200 and "Fiscal Deficit" in r.text:
                fd_pct, cap_cr = _parse(r.text)
                iso = f"{y}-{m:02d}-01"
                if fd_pct is not None:
                    fisc[iso] = fd_pct
                if cap_cr is not None:
                    capex[iso] = round(cap_cr / 1e5, 3)   # Rs cr -> lakh cr
                print(f"  {iso}: FD {fd_pct}% of BE, capex FYTD "
                      f"{cap_cr and round(cap_cr / 1e5, 2)} lakh cr")
        except Exception as e:
            print(f"  {y}-{m:02d}: {e}")
        time.sleep(0.5)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    LIVE.mkdir(parents=True, exist_ok=True)
    for sid, d in (("fisc_def", fisc), ("capex", capex)):
        obs = sorted(d.items())
        if obs:
            (LIVE / f"{sid}.json").write_text(json.dumps({"freq": "M", "obs": obs}))
            print(f"  {sid}: {len(obs)} months, latest {obs[-1][0]} = {obs[-1][1]}")
    return fisc, capex


if __name__ == "__main__":
    fetch()
