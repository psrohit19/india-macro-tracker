"""
IMD rainfall fetcher — SEEDED (stub). Populates: rainfall.

Series: cumulative southwest-monsoon (1 Jun onward) all-India rainfall as
% of LPA. IMD reports a cumulative *departure* (%); we store 100 + departure,
so departure -12% -> 88.0. LPA base period 1971-2020.

Source landscape (verified Jul 2026):
  * https://mausam.imd.gov.in/responsive/rainfallinformation.php — current
    cumulative rainfall MAPS only (JPGs under /Rainfall/, e.g.
    COUNTRY_INDIA_c.JPG); no machine-readable history. The linked
    "All India Rainfall Time Series" is likewise a GIF.
  * IITM Monsoon OnLine (https://mol.tropmet.res.in/, page_id=6 "All India
    Daily Rainfall") — sidebar widget carries the season-to-date actual/normal
    (mm) and % departure as *server-rendered text* (sheetmirror plugin):
    scrapeable for the current value.  On 2026-07-07 it read:
    01 Jun–07 Jul: actual 183.3 mm, normal 221.6 mm, departure -17.28%.
    Note: runs ~1 day behind the figure IMD briefs to government (8:30 am
    IST data cutoff), so it can differ 3-6 pp from same-day press quotes
    during fast-moving spells.
  * Season history: IMD end-of-season report
    https://mausam.imd.gov.in/imd_latest/monsoon_report_2025_2.pdf — Fig 1.7
    ("WHOLE INDIA" panel, printed data labels) gives cumulative weekly %
    departure for every week ending 4 Jun ... 30 Sep 2025. 2025 season closed
    at 108% of LPA (Jun 109 / Jul 105 / Aug 105 / Sep 115, same report).
  * In-season weekly prints reach the wires via IMD statements, e.g.
    Business Standard capital-market items titled "All India seasonal monsoon
    rainfall sees deficit of ..%" (weekly, Wednesday-ended cumulative).
  * hydro.imd.gov.in now hosts FFGS flood dashboards only (no hydromet
    rainfall statistics).  cwc/desagri CWWG mirrors are 401/403 from
    datacenter IPs.  web.archive.org is blocked by egress policy.

Because no single machine endpoint exposes the weekly cumulative series,
data/live/rainfall.json is hand-seeded ("seed": true) from the sources above.
A future live fetcher should scrape the MOL sidebar (regex the three
sheetmirror <td> cells after "Monsoon <year> All-India Summer Monsoon
Rainfall") and append 100+departure on the report date.

Seasonal caveat: obs exist only for Jun-Sep weeks. The file mixes the
completed 2025 season (Jun-Sep 2025) with the in-progress 2026 season
(deficient: 58-88% of LPA to date) — YoY deltas across seasons are
meaningful, week-to-week deltas across the Oct-May gap are not.
"""

# Stub: series is seeded. See docstring for the target endpoints.

def fetch():
    print("imd: rainfall is hand-seeded (see data/live/rainfall.json); "
          "no live endpoint wired yet")


if __name__ == "__main__":
    fetch()
