"""
IMD rainfall fetcher — SEEDED, with a working ERF-bulletin parser.
Populates: rainfall.

Series: cumulative southwest-monsoon (1 Jun onward) all-India rainfall as
% of LPA. IMD reports a cumulative *departure* (%); we store 100 + departure,
so departure -12% -> 88.0. LPA base period 1971-2020.

Source landscape (verified Jul 2026):
  * BEST MACHINE SOURCE — IMD weekly Extended Range Forecast bulletin PDFs:
      https://mausam.imd.gov.in/Forecast/marquee_data/ERF%20DD.MM.YY.pdf
    (filename literally contains a space, e.g. "ERF 18.06.26.pdf"; published
    Thursdays). Page 2 carries, verbatim:
      "All India Seasonal cumulative rainfall % departure during this year's
       Monsoon Season Rainfall (01.06.YYYY to DD.MM.YYYY) is -N%"
    plus the week-ending cumulative. Availability is spotty — of Jun-Jul 2026
    only 11.06, 18.06 and 02.07 editions resolve (25.06 and all 2025
    editions 404). parse_erf() below handles one PDF.
  * https://mausam.imd.gov.in/responsive/rainfallinformation.php — current
    cumulative rainfall MAPS only (JPGs under /Rainfall/); no data.
  * IITM Monsoon OnLine (https://mol.tropmet.res.in/?page_id=6) — sidebar
    widget has season-to-date actual/normal mm and departure as
    server-rendered text (sheetmirror <td> cells). 2026-07-07 it read
    01 Jun-07 Jul: 183.3 mm vs 221.6 mm, -17.28%. Runs on the 08:30 IST data
    cutoff and can trail the figure IMD briefs to government by ~1 day
    (govt figure "till 7 Jul" was -12%) — don't mix the two conventions.
  * Season history: IMD end-of-season report
    https://mausam.imd.gov.in/imd_latest/monsoon_report_2025_2.pdf — Fig 1.7
    "WHOLE INDIA" panel carries printed data labels of cumulative weekly %
    departure for every week ending 4 Jun ... 30 Sep 2025 (season closed at
    108% of LPA; Jun 109/Jul 105/Aug 105/Sep 115).
  * Wire fallback: Business Standard capital-market items ("All India
    seasonal monsoon rainfall sees deficit of ..%") reprint the ERF sentence
    weekly; ICRA monthly monsoon updates (icra.in) are a good cross-check.
  * Dead ends from this box: hydro.imd.gov.in (now FFGS dashboards only),
    web.archive.org (egress-blocked), desagri/agricoop CWWG (403/denied).

data/live/rainfall.json is hand-seeded ("seed": true) from the above; see
AUDIT.md. Seasonal caveats: obs exist only for Jun-Sep weeks; the file mixes
the strong 2025 season (100-125% of LPA) with the deficient-so-far 2026
season (58-88%); the 2025-06-04 print (125.0) is a 3-day-old season — early
June cumulative departures are structurally noisy.
"""
import re

import requests

ERF = "https://mausam.imd.gov.in/Forecast/marquee_data/ERF%20{d}.pdf"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}

SEASON_RE = re.compile(
    r"Monsoon\s*Season.{0,80}?Rainfall\s*\((01\.06\.\d{4})\s*to\s*"
    r"(\d\d\.\d\d\.\d{4})\)\s*is\s*(-?\d+)\s*%", re.S)


def parse_erf(pdf_bytes):
    """-> (week_end_iso, pct_of_lpa) from one ERF bulletin, or None."""
    import io
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:4]:
            m = SEASON_RE.search(page.extract_text() or "")
            if m:
                d, mth, y = m.group(2).split(".")
                return f"{y}-{mth}-{d}", 100.0 + float(m.group(3))
    return None


def fetch_erf(ddmmyy):
    """ddmmyy like '18.06.26'. Returns (iso, value) or None (404s common)."""
    r = requests.get(ERF.format(d=ddmmyy), timeout=60, headers=H)
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return None
    return parse_erf(r.content)


def fetch():
    print("imd: rainfall is hand-seeded (data/live/rainfall.json); "
          "use fetch_erf('DD.MM.YY') to pull a weekly ERF bulletin")


if __name__ == "__main__":
    fetch()
