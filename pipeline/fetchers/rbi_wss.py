"""
RBI Weekly Statistical Supplement (WSS) fetcher — LIVE.
Populates: fx_reserves (W, US$ bn), m3 (F, % YoY), credit (F, % YoY),
           deposits (F, % YoY).

Source structure (verified Jul 2026):
  Section index:  https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=<n>
      PARAM1=2  Foreign Exchange Reserves          (weekly table)
      PARAM1=3  Scheduled Commercial Banks - Business in India (fortnightly)
      PARAM1=4  Ratios and Rates (used by repo verification, not fetched here)
      PARAM1=7  Money Stock: Components and Sources (fortnightly)
  The section page lists every historical issue newest-first as
  <th colspan=4>DD Mon YYYY</th> (release date) header rows followed by rows
  linking WSSView.aspx?Id=<table_id>. Each table page carries the actual
  "as on" reference date inside the table header.

Parsing quirks:
  * fx table: row "1 Total Reserves"; columns are ₹ Cr. then US$ Mn. — we
    take the 2nd number (US$ Mn) and convert to US$ bn. Reference date from
    "As on Mon. DD, YYYY" in the header.
  * Sec 3 (SCB business): rows "2.1a Growth (Per cent)" (aggregate deposits)
    and "7.1a Growth (Per cent)" (bank credit); the LAST number in each row
    is the current-year YoY %. Reference date from "Outstanding as on
    Mon. DD, YYYY".
  * Sec 7 (money stock): row "M3"; the LAST number is the YoY % for the
    current year. The header holds date cells like "Mar. 31 | Jun. 15" with
    the year printed separately, so the reference date is composed from the
    last month-day cell + the release year (minus 1 if the month is ahead of
    the release month, for Dec fortnights released in Jan).
  * Sec 3/7 tables are fortnightly but re-listed in some weekly issues —
    observations are deduped on the "as on" date.
  * Each issue also links an XLSX on rbidocs.rbi.org.in (random hash in the
    filename) — the HTML table is parsed instead as it needs no extra deps.

Growth rates are recorded exactly as RBI prints them (merger-inclusive).
"""
import json
import re
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["fx_reserves", "m3", "credit", "deposits"]
BASE = "https://www.rbi.org.in/Scripts/"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MON = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def _get(url):
    r = requests.get(url, headers=H, timeout=90)
    r.raise_for_status()
    return r.text


def _section_entries(param1, limit):
    """Newest-first [(release_date, table_id), ...] for a WSS section."""
    html = _get(f"{BASE}WSSViewDetail.aspx?TYPE=Section&PARAM1={param1}")
    out, cur = [], None
    for m in re.finditer(
            r"<th[^>]*>(\d{2} \w{3} \d{4})</th>|WSSView\.aspx\?Id=(\d+)", html):
        if m.group(1):
            cur = datetime.strptime(m.group(1), "%d %b %Y").date()
        elif cur is not None:
            out.append((cur, m.group(2)))
        if len(out) >= limit:
            break
    return out


def _table_cells(table_id):
    """Rows of the main data table as lists of cell strings."""
    soup = BeautifulSoup(_get(f"{BASE}WSSView.aspx?Id={table_id}"), "lxml")
    best = max(soup.find_all("table"), key=lambda t: len(t.get_text()))
    return ([ [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
              for tr in best.find_all("tr") ], best.get_text(" ", strip=True))


def _nums(cells):
    out = []
    for c in cells:
        c = c.replace(",", "").strip()
        if re.fullmatch(r"-?\d+(\.\d+)?", c):
            out.append(float(c))
    return out


def _ason_date(text):
    m = re.search(r"as on\s+(\w{3})\.?\s*(\d{1,2}),\s*(\d{4})", text, re.I)
    if not m:
        return None
    return date(int(m.group(3)), MON[m.group(1)[:3].title()], int(m.group(2)))


def _write(sid, freq, obs, n_min=14):
    if len(obs) < n_min:
        print(f"  {sid}: only {len(obs)} obs — NOT writing (<{n_min})")
        return False
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / f"{sid}.json").write_text(
        json.dumps({"freq": freq, "obs": [[d, v] for d, v in pairs]}))
    print(f"  {sid}: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")
    return True


def fetch_fx_reserves(weeks=34):
    obs = {}
    for rel, tid in _section_entries(2, weeks):
        try:
            rows, text = _table_cells(tid)
        except Exception as e:
            print(f"  fx_reserves: skip Id={tid}: {e}")
            continue
        d = _ason_date(text)
        if d is None:
            continue
        for cells in rows:
            if cells and cells[0].startswith("1 Total Reserves"):
                vals = _nums(cells[1:])
                if len(vals) >= 2:
                    obs[d.isoformat()] = round(vals[1] / 1000.0, 2)  # US$ bn
                break
    _write("fx_reserves", "W", obs)


def fetch_money_stock(issues=40, want=16):
    obs = {}
    for rel, tid in _section_entries(7, issues):
        if len(obs) >= want:
            break
        try:
            rows, text = _table_cells(tid)
        except Exception as e:
            print(f"  m3: skip Id={tid}: {e}")
            continue
        # compose the fortnight-end date from header date cells
        # Header prints the FY-start and fortnight-end date cells right before
        # the first "Amount" label: "... Mar. 31 Jun. 15 Amount % ...".
        # (Months May/Jun/Jul print WITHOUT a trailing dot, the rest with one;
        # a footnote lower down also contains dates, so anchor on "Amount".)
        # Provisional dates carry a trailing asterisk ("Mar. 31* Apr. 30").
        m = re.search(r"([A-Z][a-z]{2})\.?\s*(\d{1,2})\*?\s+([A-Z][a-z]{2})\.?"
                      r"\s*(\d{1,2})\*?\s+Amount", text)
        if not m or m.group(3) not in MON:
            continue
        mon, day = m.group(3), int(m.group(4))
        yr = rel.year if MON[mon] <= rel.month else rel.year - 1
        iso = date(yr, MON[mon], day).isoformat()
        for cells in rows:
            if cells and cells[0].strip() == "M3":
                vals = _nums(cells[1:])
                if vals:
                    obs[iso] = vals[-1]          # YoY % as printed
                break
    _write("m3", "F", obs)


def fetch_scb_business(issues=40, want=16):
    cred, dep = {}, {}
    for rel, tid in _section_entries(3, issues):
        if len(cred) >= want and len(dep) >= want:
            break
        try:
            rows, text = _table_cells(tid)
        except Exception as e:
            print(f"  credit/deposits: skip Id={tid}: {e}")
            continue
        d = _ason_date(text)
        if d is None:
            continue
        for cells in rows:
            if not cells:
                continue
            head = cells[0].strip()
            if head.startswith("2.1a"):
                vals = _nums(cells[1:])
                if vals:
                    dep[d.isoformat()] = vals[-1]
            elif head.startswith("7.1a"):
                vals = _nums(cells[1:])
                if vals:
                    cred[d.isoformat()] = vals[-1]
    _write("credit", "F", cred)
    _write("deposits", "F", dep)


def fetch():
    fetch_fx_reserves()
    fetch_money_stock()
    fetch_scb_business()


if __name__ == "__main__":
    fetch()
