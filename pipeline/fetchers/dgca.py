"""
DGCA domestic air traffic fetcher — LIVE-capable (seed written 2026-07-08).
Populates: airpax (domestic scheduled-airline passengers carried, lakh).

Source (verified working, no auth, direct S3):
  https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/dataReports/
      aviationDataStatistics/airTransport/domestic/airTraffic/<FILENAME>.pdf

  The dgca.gov.in digigov portal itself is a JS shell (content via an opaque
  'scan?...' XHR) — skip it and hit the S3 objects. Bucket listing is denied;
  filenames must be known/guessed. Naming DRIFTS by month:
      2022-23 era : April2023.pdf, Sept2022.pdf
      2024-25     : "traffic Data September 24.pdf", "Traffic report Feb 24.pdf"
      2025-26     : "traffic Data Nov 25.pdf", "traffic Data Dec 25.pdf",
                    "traffic Data May 26.pdf"   (all URL-encoded spaces, %20)
  Probe a handful of variants (traffic Data / traffic report / Traffic Data x
  "Mon YY" / "Month YY") — wrong guesses 403 (not 404).

Parsing (validated on Dec-25 and May-26 reports):
  * Page 1 headline: "Passengers carried ... during January - <Month> <year>
    were X lakhs against Y lakhs ..." plus a MoM chart.
  * Page 3 "MARKET SHARE OF SCHEDULED DOMESTIC AIRLINES (YEAR yyyy)" table:
    per-month "Pax Carried" rows (airline-wise, lakh). Sum of the row ==
    monthly total. Validated: 2025 rows sum to 1669.49 vs headline 1669.46;
    Jan-May-26 sum 729.41 vs headline 729.40; May-26 row 153.89 vs 153.90.
  * pdfplumber text: month label ('Jan'..'Dec') sits on the line before/after
    the 'Pax Carried' line; skip IstQtr/IIndQtr/.../TOTAL rows.
  * The December report carries all 12 months of the calendar year, so
    December + latest-month reports reconstruct the full series.

Revision quirk: DGCA back-revises. The Dec-25 report's own page-1 chart shows
Nov-25 = 149.28 but its table (and the Nov-25 report headline) says 152.38/9;
the table is consistent with cumulative totals — trust the newest report's
TABLE, not charts. Cross-vintage check: Jan-May-25 sum is identical (715.70/1)
in both the Dec-25 and May-26 reports.

Release: ~3rd week of the following month. Seeded Jan-2025..May-2026 from the
"traffic Data Dec 25.pdf" and "traffic Data May 26.pdf" reports; May-2026
(153.89 lakh = 1.53 cr) cross-verified against travelbizmonitor.com coverage.
"""
import json
import re
from pathlib import Path

BASE = ("https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/"
        "dataReports/aviationDataStatistics/airTransport/domestic/airTraffic/")
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def parse_market_share_months(pdf_path):
    """Return {(year, month): pax_lakh} from a DGCA monthly traffic report."""
    import pdfplumber
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            t = p.extract_text() or ''
            if 'MARKET SHARE OF SCHEDULED DOMESTIC AIRLINES' not in t.upper():
                continue
            m = re.search(r'YEAR\s+(\d{4})', t.upper())
            if not m:
                continue
            year = int(m.group(1))
            lines = t.split('\n')
            for i, ln in enumerate(lines):
                if not ln.strip().startswith('Pax Carried'):
                    continue
                nums = [float(x) for x in re.findall(r'\d+\.\d+', ln)]
                if not nums:
                    continue
                for j in (i - 1, i + 1):
                    if 0 <= j < len(lines) and lines[j].strip() in MON:
                        out[(year, MON.index(lines[j].strip()) + 1)] = \
                            round(sum(nums), 2)
                        break
    return out


def fetch():
    """Seed is in place (17 months, Jan-2025..May-2026, seed:true). To go
    fully live: guess the newest month's filename (see naming notes), download
    from BASE, run parse_market_share_months, merge into airpax.json."""
    f = LIVE / "airpax.json"
    print("airpax:", json.loads(f.read_text())["obs"][-1] if f.exists() else "missing")


if __name__ == "__main__":
    fetch()
