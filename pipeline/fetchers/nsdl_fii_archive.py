"""
NSDL FPI Monitor — historical backfill fetcher. Populates: fii (daily).

Complements nsdl_fii.py (which scrapes only the latest day from Latest.aspx)
by pulling FULL MONTHS of daily equity net investment (₹ crore) from:

  * https://www.fpi.nsdl.co.in/web/Reports/Monthly.aspx
        current calendar month, one block of rows per reporting date
  * https://www.fpi.nsdl.co.in/web/Reports/Archive.aspx
        any past month, via classic ASP.NET postback:
        GET the page, harvest __VIEWSTATE / __EVENTVALIDATION /
        __VIEWSTATEGENERATOR hidden fields, then POST them back with
            __EVENTTARGET = "btnSubmit1"
            txtDate = hdnDate = "DD-Mon-YYYY"   (any date in the wanted month,
                                                 format %d-%b-%Y)
        The response contains the month containing that date UP TO that
        date (month-to-date) — so always request the LAST day of the month.

Row structure per reporting date (verified Jul 2026):
    [date, 'Equity', 'Stock Exchange', buy, sell, net, net_usd, fx]
    ['Primary market & others', buy, sell, net, net_usd]
    ['Sub-total', buy, sell, net, net_usd]     <- equity sub-total net (₹ cr)
followed by Debt-General Limit / Debt-VRR / FAR / Hybrid / MF / AIF blocks,
each with their own Sub-total rows — only the Sub-total immediately following
an 'Equity' date row is taken. Negative values print as "(1,234.56)".

Merges into data/live/fii.json, PRESERVING any observation already present
(the accumulating Latest.aspx fetcher owns the newest day).
"""
import calendar
import json
import re
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["fii"]
ARCHIVE_URL = "https://www.fpi.nsdl.co.in/web/Reports/Archive.aspx"
MONTHLY_URL = "https://www.fpi.nsdl.co.in/web/Reports/Monthly.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def _num(s):
    s = s.replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        return -float(s[1:-1])
    return float(s)


def _parse_equity_daily(html):
    """{iso_date: equity_subtotal_net_rs_cr} from a Monthly/Archive page."""
    soup = BeautifulSoup(html, "lxml")
    out = {}
    cur_iso, in_equity = None, False
    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if not cells:
            continue
        m = re.match(r"\d{2}-[A-Za-z]{3}-\d{4}$", cells[0])
        if m and len(cells) >= 3:
            cur_iso = datetime.strptime(cells[0], "%d-%b-%Y").date().isoformat()
            in_equity = cells[1] == "Equity"
        elif in_equity and cells[0] == "Sub-total" and len(cells) >= 4:
            out[cur_iso] = _num(cells[1 + 2])  # buy, sell, NET
            in_equity = False
    return out


def _fetch_month(session, any_date_in_month):
    """One archive month via VIEWSTATE postback. any_date_in_month: date."""
    r = session.get(ARCHIVE_URL, timeout=60)
    sp = BeautifulSoup(r.text, "lxml")
    data = {i["name"]: i.get("value", "") for i in
            sp.find_all("input", type="hidden") if i.get("name")}
    txt = any_date_in_month.strftime("%d-%b-%Y")
    data.update({"__EVENTTARGET": "btnSubmit1", "__EVENTARGUMENT": "",
                 "txtDate": txt, "hdnDate": txt})
    r2 = session.post(ARCHIVE_URL, data=data, timeout=90)
    r2.raise_for_status()
    return _parse_equity_daily(r2.text)


def fetch(months_back=3):
    """Backfill the current month + `months_back` archive months into fii.json."""
    s = requests.Session()
    s.headers.update(H)

    merged = _parse_equity_daily(s.get(MONTHLY_URL, timeout=60).text)
    today = date.today()
    y, m = today.year, today.month
    for _ in range(months_back):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        last_day = calendar.monthrange(y, m)[1]
        merged.update(_fetch_month(s, date(y, m, last_day)))

    f = LIVE / "fii.json"
    obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
    added = 0
    for d, v in merged.items():
        if d not in obs:            # never overwrite the accumulating fetcher
            obs[d] = v
            added += 1
    LIVE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"freq": "D", "obs": sorted(obs.items())}))
    print(f"  fii backfill: +{added} obs, total {len(obs)}")
    return obs


if __name__ == "__main__":
    fetch()
