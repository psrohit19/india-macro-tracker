"""
NSDL FPI Monitor fetcher — LIVE (accumulating). Populates: fii (daily).

Parses https://www.fpi.nsdl.co.in/Reports/Latest.aspx — the daily equity
sub-total net investment (₹ crore): Stock Exchange + Primary market & others.
Verified structure (Jul 2026): table rows
    [date, 'Equity', 'Stock Exchange', buy, sell, net, net_usd, fx]
    ['Primary market & others', buy, sell, net, net_usd]
    ['Sub-total', buy, sell, net, net_usd]          <- we take this net

The page only shows the latest day, so the series ACCUMULATES one observation
per run — fii/fii_m tiles flip from SAMPLE to LIVE automatically once ≥14
daily observations have been collected (~3 weeks of daily refreshes).
Historical backfill option: NSDL fortnightly/yearwise archives (VIEWSTATE
postback) or a one-time manual CSV seed into data/live/fii.json.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["fii"]
URL = "https://www.fpi.nsdl.co.in/Reports/Latest.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"


def _num(s):
    s = s.replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        return -float(s[1:-1])
    return float(s)


def fetch():
    html = requests.get(URL, timeout=45, headers=H).text
    soup = BeautifulSoup(html, "lxml")
    m = re.search(r"Daily Trends in FPI Investments on (\d{2}-\w{3}-\d{4})", html)
    if not m:
        raise ValueError("NSDL: date header not found — page structure changed?")
    iso = datetime.strptime(m.group(1), "%d-%b-%Y").date().isoformat()

    net = None
    rows = soup.find_all("table")[0].find_all("tr")
    in_equity = False
    for tr in rows:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if not cells:
            continue
        if len(cells) >= 2 and cells[1] == "Equity":
            in_equity = True
        elif in_equity and cells[0] == "Sub-total":
            net = _num(cells[3])           # Net Investment (₹ crore)
            break
    if net is None:
        raise ValueError("NSDL: equity sub-total row not found")

    f = LIVE / "fii.json"
    obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
    obs[iso] = net
    LIVE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"freq": "D", "obs": sorted(obs.items())}))
    print(f"  fii: {iso} = {net:+,.0f} cr ({len(obs)} obs accumulated)")


if __name__ == "__main__":
    fetch()
