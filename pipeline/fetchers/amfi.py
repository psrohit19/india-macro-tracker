"""
AMFI monthly-note fetcher — LIVE. Populates: sip (monthly, ₹ crore).

AMFI's structured SIP xls has no stable public URL, but every AMFI Monthly
Note PDF states that month's SIP contribution. This fetcher:

  1. GETs https://www.amfiindia.com/otherdata/amfi-monthlynote and collects
     the note PDF links (e.g. /uploads/AMFI_Monthly_Note_May2026_<hash>.pdf,
     older /Themes/Theme1/downloads/AMFIMonthlyNote_August2025.pdf).
  2. Parses the note's month/year out of the filename.
  3. Downloads each PDF and pulls the SIP contribution via anchored regexes
     (verified against Jun-2024 → May-2026 notes):
        "SIP monthly contribution (crore) 30,954 ..."   <- first col = note month
        "amounting to Rs 30,954 crore"
        "SIP contribution ... Rs 23,332 crore"
  4. Sanity-gates each value to ₹10,000–60,000 cr and writes data/live/sip.json.

Latest month lands ~8th-12th of the following month (note publishes a few
days after the AMFI data release).
"""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["sip"]
LISTING = "https://www.amfiindia.com/otherdata/amfi-monthlynote"
BASE = "https://www.amfiindia.com"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}
_M_ABBR = {k[:3]: v for k, v in MONTHS.items()}

PATTERNS = [
    # trailing-months table row: first number = the note's own month
    re.compile(r"SIP monthly contributions? \((?:in )?crore\)\s+([\d,]+)"),
    # "...(SIP) flows/contributions ... Rs 26,400 crore" narrative bullets
    re.compile(r"\(SIP\)[^\n]*?Rs\.?\s*([\d,]+)\s*crore", re.I),
    re.compile(r"SIP contributions?[^\n]*?Rs\.?\s*([\d,]+)\s*crore", re.I),
    re.compile(r"amounting to Rs\.?\s*([\d,]+)\s*crore", re.I),
]


def _month_from_name(href):
    """'AMFI_Monthly_Note_May2026_9b75.pdf' -> '2026-05-01' (period start)."""
    m = re.search(r"Note_?([A-Za-z]+)_?(\d{4})", href)
    if not m:
        return None
    mon = _M_ABBR.get(m.group(1)[:3].lower())
    return f"{m.group(2)}-{mon:02d}-01" if mon else None


def _extract_sip(pdf_bytes):
    import io
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        txt = "\n".join((p.extract_text() or "") for p in pdf.pages)
    for pat in PATTERNS:
        m = pat.search(txt)
        if m:
            v = float(m.group(1).replace(",", ""))
            if 10_000 <= v <= 60_000:
                return v
    return None


def fetch(max_notes=30):
    s = requests.Session()
    s.headers.update(H)
    soup = BeautifulSoup(s.get(LISTING, timeout=60).text, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        if ".pdf" in a["href"].lower() and "Note" in a["href"]:
            iso = _month_from_name(a["href"])
            if iso:
                url = a["href"] if a["href"].startswith("http") else BASE + a["href"]
                links.append((iso, url))
    links = sorted(dict(links).items(), reverse=True)[:max_notes]

    f = LIVE / "sip.json"
    obs = {d: v for d, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
    for iso, url in links:
        if iso in obs:
            continue                       # already have this month
        try:
            v = _extract_sip(s.get(url, timeout=90).content)
        except Exception as e:
            print(f"  sip: {iso} FAILED ({e})")
            continue
        if v is not None:
            obs[iso] = v
            print(f"  sip: {iso} = {v:,.0f} cr")
    LIVE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"freq": "M", "obs": sorted(obs.items())}))
    print(f"  sip: {len(obs)} obs total")
    return obs


if __name__ == "__main__":
    fetch()
