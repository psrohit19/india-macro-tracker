"""
Kharif sowing fetcher — SEEDED, with a working PIB scraper. Populates: sowing.

Series: cumulative all-India area sown under kharif crops, lakh hectares,
from the Dept. of Agriculture & Farmers Welfare weekly release
("Progress of area coverage under Kharif crops as on DD.MM.YYYY").

Source landscape (verified Jul 2026):
  * agriwelfare.gov.in — 403 for datacenter IPs even with browser headers;
    agricoop.nic.in CONNECT is denied by the egress proxy. Don't bother.
  * PIB (https://www.pib.gov.in) works and carries the weekly release.
    - The archive form  /allRel.aspx?reg=3&lang=1  is an ASP.NET postback:
      GET once for __VIEWSTATE etc., then POST with
      ctl00$ContentPlaceHolder1$ddlMinistry=27 (Agriculture & Farmers
      Welfare), ddlMonth, ddlYear, ddlday=0 and
      __EVENTTARGET=ctl00$ContentPlaceHolder1$ddlMinistry.
      The day-level filter (ddlday=N) does NOT work with a single postback —
      keep it 0 and filter titles client-side.
    - Release pages /PressReleasePage.aspx?PRID=xxxx render the crop table as
      plain <td> text; the all-crops row matches  r"Total\\s+((?:\\d+\\.\\d+\\s+)+)".
      2025 layout: Total | normal-area | this-year | last-year [| diff]
      2026 layout: Total | normal-2026 | normal-alt | this-year | last-year.
      Robust rule used below: this-year = the value in the row immediately
      before last-year, where the row's first 1-2 entries (~1096-1134) are
      "normal area" constants; equivalently take cells[-2].
  * Some weeks never get an English PIB release (04.07.2025, 22/29.08.2025,
    19.09.2025 are absent from the complete month listings). The DoA data
    still reaches wires: e.g. Business Standard reported the 06.07.2026
    figure (350.85 lakh ha, -21% YoY) a day before any PIB posting; ICICI
    Research (via newkerala.com) carried the same 35.1 mn ha. Gaps are gaps —
    do not interpolate.
  * upag.gov.in/dash-reports/progressivecropareasown exists but is a JS
    dashboard; not scraped here.

data/live/sowing.json is currently hand-seeded ("seed": true) from the PIB
releases listed in AUDIT.md. fetch() below re-scrapes PIB and can replace the
seed once scheduled.

Seasonal caveats: series is cumulative within each kharif season
(Jun->Sep, ~85 -> ~1120 lakh ha), then resets; the file spans the 2025 season
plus the in-progress (deficient) 2026 season, whose 26 Jun / 06 Jul prints run
23-21% below the 2025 corresponding weeks. Weekly numbers are compiled from
state reports and revise; compare YoY, not to the prior week.
"""
import json
import re
import time
from pathlib import Path

import requests

LIVE = Path(__file__).parent.parent.parent / "data" / "live"
PIB = "https://www.pib.gov.in"
ARCHIVE = f"{PIB}/allRel.aspx?reg=3&lang=1"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 Chrome/126 Safari/537.36"}
MINISTRY_AGRI = "27"
TITLE_RE = re.compile(r"kharif crops as on (\d{2})\.(\d{2})\.(\d{4})", re.I)


def _hidden(html):
    return dict(re.findall(
        r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"', html))


def _month_listing(s, month, year):
    """PRID -> title for every Agriculture release in a month."""
    r = s.get(ARCHIVE, timeout=60)
    data = _hidden(r.text)
    data.update({
        "ctl00$Bar1$ddlregion": "3", "ctl00$Bar1$ddlLang": "1",
        "ctl00$ContentPlaceHolder1$ddlday": "0",
        "ctl00$ContentPlaceHolder1$ddlMonth": str(month),
        "ctl00$ContentPlaceHolder1$ddlYear": str(year),
        "ctl00$ContentPlaceHolder1$ddlMinistry": MINISTRY_AGRI,
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlMinistry",
    })
    h = s.post(ARCHIVE, data=data, timeout=60).text
    out = {}
    for m in re.finditer(
            r'<a[^>]*href=[\'"][^\'"]*PRID=(\d+)[^\'"]*[\'"][^>]*>(.*?)</a>',
            h, re.S):
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if title:
            out.setdefault(m.group(1), title)
    return out


def _total_from_release(s, prid):
    """Parse the all-crops Total (lakh ha, current year) from a release."""
    h = s.get(f"{PIB}/PressReleasePage.aspx?PRID={prid}", timeout=60).text
    text = re.sub(r"&nbsp;?", " ", re.sub(r"<[^>]+>", " ", h))
    text = re.sub(r"\s+", " ", text)
    m = re.search(r"Total\s+((?:\d{1,4}\.\d{1,2}\s+){2,6})", text)
    if not m:
        return None
    cells = [float(x) for x in m.group(1).split()]
    # last two cells are (this year, last year); guard tiny diff columns
    vals = [c for c in cells if c > 40]
    return vals[-2] if len(vals) >= 2 else None


def fetch(months=None):
    """months: iterable of (month, year); defaults to Jun-Oct of this year."""
    import datetime as dt
    today = dt.date.today()
    months = months or [(m, today.year) for m in range(6, min(today.month, 10) + 1)]
    s = requests.Session()
    s.headers.update(H)
    f = LIVE / "sowing.json"
    obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
    for month, year in months:
        for prid, title in _month_listing(s, month, year).items():
            m = TITLE_RE.search(title)
            if not m:
                continue
            iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            total = _total_from_release(s, prid)
            time.sleep(0.5)
            if total:
                obs[iso] = total
    LIVE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"freq": "W", "obs": sorted(obs.items())}))
    print(f"  sowing: {len(obs)} weeks")


if __name__ == "__main__":
    fetch()
