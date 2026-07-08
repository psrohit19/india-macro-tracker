"""
RBI/FBIL reference rate archive fetcher — LIVE.
Populates: inrusd (D, ₹ per US$).

Source: https://www.rbi.org.in/scripts/referenceratearchive.aspx
Classic ASP.NET postback form: GET the page for __VIEWSTATE /
__EVENTVALIDATION, then POST them back with chkUSD=on,
txtFromDate/txtToDate in DD/MM/YYYY and btnSubmit=GO. The response embeds
a two-column table "Date | USD (INR / 1 USD)" with dates DD/MM/YYYY,
newest first, only business days.

The rate is the FBIL midday reference fix RBI disseminates (~1:30 pm), not
a market close. Sanity-checked against the WSS 'Ratios and Rates' weekly
"INR-US$ Spot Rate" prints (e.g. both ~94.5-95.4 in late Jun 2026).
"""
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["inrusd"]
URL = "https://www.rbi.org.in/scripts/referenceratearchive.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def fetch(days_back=60):
    sess = requests.Session()
    sess.headers.update(H)
    r = sess.get(URL, timeout=90)
    soup = BeautifulSoup(r.text, "lxml")
    data = {i["name"]: i.get("value", "") for i in soup.find_all("input")
            if i.get("name") and i.get("type") == "hidden"}
    t = date.today()
    f = t - timedelta(days=days_back)
    data.update({"chkUSD": "on",
                 "txtFromDate": f.strftime("%d/%m/%Y"),
                 "txtToDate": t.strftime("%d/%m/%Y"),
                 "btnSubmit": "GO"})
    r2 = sess.post(URL, data=data, timeout=120)
    obs = {}
    for tab in BeautifulSoup(r2.text, "lxml").find_all("table"):
        head = tab.get_text(" ", strip=True)[:80]
        if "USD" not in head or "Date" not in head:
            continue
        cells = [c.get_text(strip=True) for c in tab.find_all("td")]
        for i in range(0, len(cells) - 1):
            if re.fullmatch(r"\d{2}/\d{2}/\d{4}", cells[i]) and \
               re.fullmatch(r"[\d.]+", cells[i + 1]):
                d = datetime.strptime(cells[i], "%d/%m/%Y").date()
                obs[d.isoformat()] = float(cells[i + 1])
    if len(obs) < 14:
        print(f"  inrusd: only {len(obs)} obs — NOT writing")
        return
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / "inrusd.json").write_text(
        json.dumps({"freq": "D", "obs": [[d, v] for d, v in pairs]}))
    print(f"  inrusd: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")


if __name__ == "__main__":
    fetch()
