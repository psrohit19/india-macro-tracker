"""
Ministry of Coal monthly production fetcher — LIVE. Populates: coal (MT, monthly).

Source (verified working, Jul 2026):
  * https://coal.gov.in/public-information/monthly-statistics-at-glance —
    Drupal page listing "Monthly Coal Statistics for <Mon>'<YYYY> (Provisional)"
    PDFs (msg-*.pdf under /sites/default/files/YYYY-MM/). NOTE: the /en/...
    prefixed paths 404; use the bare paths. Filenames are irregular
    (msg-setp25.pdf, msg-march26.pdf...), so the month is read from the PDF
    title line, not the filename.
  * Each PDF's "Coal Production" table ends with a Grand Total row:
        Grand Total <monthly target> <this-month actual> <achievement %>
                    <same month prior year> ...
    The 2nd number is the all-India production (CIL + SCCL + captive/others)
    for the report month in MT — that is what this fetcher writes.
    (pdfplumber text extraction; the row spills onto page 2 of the PDF.)

Quirks:
  * The MSG PDF lags the month by ~4-5 weeks; the PIB releases that appear in
    the first week (e.g. PRID 2280284 for Jun 2026) cover CAPTIVE/COMMERCIAL
    mines only (~18 MT) — never use those as the all-India figure (~75-120 MT).
  * Prior-year columns revise slightly between editions (May'25: 86.34 own
    print vs 86.36 as shown in the May'26 edition).

Verification performed (Jul 2026):
  * May 2026 Grand Total 78.13 MT decomposes as CIL 56.13 + SCCL 4.51 +
    captives/others 17.49; the CIL 56.1 MT / -11.6% YoY figure matches the
    independent PSU Watch / Business Standard reports of 01-Jun-2026.
  * Each edition's prior-year column matches the year-ago edition's own print.

Writes data/live/coal.json: {"freq": "M", "obs": [["YYYY-MM-01", MT], ...]}
"""
import json
import re
import time
from pathlib import Path

import pdfplumber
import requests

BASE = "https://coal.gov.in"
LISTING = f"{BASE}/public-information/monthly-statistics-at-glance"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
CACHE = Path("/tmp/coal_msg")
START = "2024-01"          # earliest report month to parse

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def _month_from_title(text):
    """'Monthly Coal Statistics for May'2026 (Provisional)' -> '2026-05'.
    Apostrophe may be straight or curly, spaces optional (Aug'25 edition has
    "forAug'2025" with no space); month names appear as Jan/June/Sept etc."""
    m = re.search(r"Monthly Coal Statistics for\s*([A-Za-z]+)\s*[’']?\s*(\d{4})",
                  text)
    if not m:
        return None
    mon = MONTHS.get(m.group(1).strip().lower()[:3])
    return f"{m.group(2)}-{mon:02d}" if mon else None


def _grand_total(text):
    """First 'Grand Total' row after the Coal Production table; 2nd numeric
    field is the month's all-India production in MT."""
    m = re.search(r"Grand Total\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
                  text)
    return float(m.group(2)) if m else None


def fetch():
    print("Ministry of Coal MSG pull:")
    CACHE.mkdir(parents=True, exist_ok=True)
    r = requests.get(LISTING, headers=H, timeout=60)
    r.raise_for_status()
    pdfs = sorted(set(re.findall(
        r'href="(/sites/default/files/(\d{4}-\d{2})/msg-[^"]+\.pdf)"', r.text)))
    obs = {}
    for path, posted in pdfs:
        if posted < START:      # posted month trails report month by ~1
            continue
        f = CACHE / path.rsplit("/", 1)[-1]
        if not f.exists() or f.stat().st_size < 10000:
            rr = requests.get(BASE + path, headers=H, timeout=90)
            rr.raise_for_status()
            f.write_bytes(rr.content)
            time.sleep(0.5)
        try:
            with pdfplumber.open(f) as pdf:
                text = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])
        except Exception as e:
            print(f"  ! {f.name}: unreadable ({e})")
            continue
        month, mt = _month_from_title(text), _grand_total(text)
        if month and mt and 40 < mt < 200:
            obs[f"{month}-01"] = mt
        else:
            print(f"  ! {f.name}: parse miss (month={month}, mt={mt})")
    LIVE.mkdir(parents=True, exist_ok=True)
    out = sorted(obs.items())
    (LIVE / "coal.json").write_text(
        json.dumps({"freq": "M", "obs": [[d, v] for d, v in out]}))
    print(f"  coal: {len(out)} months, latest {out[-1][0]} = {out[-1][1]}")


if __name__ == "__main__":
    fetch()
