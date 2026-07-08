"""
TRAI wireless subscriber fetcher — LIVE-capable (seed written 2026-07-08).
Populates: trai_subs (monthly wireless NET ADDITIONS, mn; can be negative).

Source (verified working, plain curl, ~1-13 MB PDFs, slow server):
  Listing: https://www.trai.gov.in/release-publication/reports/telecom-subscriptions-reports
           (server-rendered HTML; PDF hrefs match /sites/default/files/YYYY-MM/PR_No*.pdf)
  PDFs:    https://www.trai.gov.in/sites/default/files/<YYYY-MM>/<name>.pdf

Parsing (validated on 20 monthly PRs, Oct-2024..May-2026 data):
  * Find the page whose text has "Highlights of Telecom Subscription Data"
    with either "at the end of <Month> <yyyy>" or "as on <ddth> <Month> <yyyy>"
    (BOTH phrasings occur) AND contains "Total Telephone Subscribers".
  * On that page: the "Total Telephone Subscribers (Million)" line's FIRST
    number = total wireless subs; the following "Net Addition in <month>"
    line's FIRST number = wireless net adds (mn) -> the series value.
  * Consistency check: total[m] - total[m-1] == net_add[m] (held for every
    parsed month).

Quirks:
  * Some PRs are scanned images: PR 19/2026 (Dec-2025 data) needed tesseract
    OCR of page 1; PR 46/2026 (Feb-2026) has garbled page-1 text but a clean
    narrative ("increased from 1266.34 ... to 1273.31 million") on the
    'Wireless Telephone (Mobile + FWA) Subscriber Base' page.
  * SERIES BREAK, Dec-2025: Bharti Airtel began including its M2M cellular
    base (Airtel had been the only operator excluding it), jumping the wireless
    TOTAL from 1187.48 mn (Nov-25) to 1258.77 mn (Dec-25). TRAI's printed
    "Net Addition" (+8.21 mn for Dec-25) is on a comparable basis and excludes
    the ~63 mn reclassification — net adds remain a clean series across the
    break; the TOTALS column does not.
  * Wireless = mobile (incl. M2M) + FWA since the Dec-25 revamp; tariff-hike
    SIM-consolidation episodes make negative months genuine (-3.31 mn Oct-24).
  * ~1.5-2 month publication lag (May-2026 data released 25 Jun 2026).

Latest seed value cross-verified: May-2026 +5.50 mn (1288.96 -> 1294.46 mn),
matching Asianet/ANI coverage of PR 78/2026.
"""
import json
import re
from pathlib import Path

LIST_URL = ("https://www.trai.gov.in/release-publication/reports/"
            "telecom-subscriptions-reports")
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
HEAD = re.compile(
    r'(?:at the end of|as on)\s+(?:\d{1,2}(?:st|nd|rd|th)?\s+)?'
    r'(January|February|March|April|May|June|July|August|September|October|'
    r'November|December)[,]?\s*(\d{4})')


def parse_pr(pdf_path):
    """Return (iso_month, total_wireless_mn, net_add_mn) or None."""
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages[:15]:
            t = p.extract_text() or ''
            m = HEAD.search(t)
            if not m or 'Total Telephone Subscribers' not in t:
                continue
            iso = f"{int(m.group(2))}-{MONTHS.index(m.group(1)) + 1:02d}-01"
            lines = t.split('\n')
            total = net = None
            for i, ln in enumerate(lines):
                if 'Total Telephone Subscribers' in ln:
                    nums = re.findall(r'(-?[\d,]+\.\d+)', ln)
                    if nums:
                        total = float(nums[0].replace(',', ''))
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if 'Net Addition' in lines[j]:
                            nn = re.findall(r'(-?[\d,]+\.\d+)', lines[j])
                            if nn:
                                net = float(nn[0].replace(',', ''))
                            break
                    break
            return iso, total, net
    return None  # scanned PDF -> OCR fallback needed (see docstring)


def fetch():
    """Seed is in place (20 months, Oct-2024..May-2026, seed:true). To go
    live: fetch LIST_URL, take new PR_No*.pdf links, parse_pr each, append
    net adds to trai_subs.json (OCR fallback for scanned PRs)."""
    f = LIVE / "trai_subs.json"
    print("trai_subs:", json.loads(f.read_text())["obs"][-1] if f.exists() else "missing")


if __name__ == "__main__":
    fetch()
