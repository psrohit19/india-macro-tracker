"""
EPFO net payroll additions fetcher — SEEDED (stub). Populates: epfo.

Unit: lakh net members/month (new enrolments − exits + rejoins), first
provisional prints. data/live/epfo.json hand-seeded Jun-2024..Jul-2025
(14 obs) from PIB press releases + AIR/News-on-AIR coverage (Jul 2026).

IMPORTANT — series suspended (verified Jul 2026):
  The last monthly payroll release is JULY 2025 data (21.04 lakh, PIB
  PRID=2169975, released 23-Sep-2025). No Aug-2025..May-2026 release exists
  anywhere (PIB, news, Google News). The gap coincides with the EPFO 3.0 /
  revamped-ECR migration (new ECR from wage-month Sep-2025; even member
  passbooks weren't updating for Sep-Oct 2025). Do not expect fresh prints
  until EPFO resumes publication; when it does, expect a backlog dump and
  heavy restatement of earlier months.

Sources & access quirks:
  * epfindia.gov.in and epfo.gov.in are UNREACHABLE from this box
    (TCP reset / CloudFront 403 geo-block on non-India egress). The
    machine-readable master file lives at
    https://www.epfindia.gov.in/site_docs/exmpted_est/Payroll_Data_EPFO_{Mon}_{Year}.pdf
    (month-wise table incl. revisions) behind
    https://www.epfindia.gov.in/site_en/Estimate_of_Payroll.php — use it if
    egress ever gets an India-friendly route.
  * PIB releases (fetchable) are titled "EPFO Adds/Records ... Lakh Net
    Members during {Month} {Year}", ~20th of M+2. Known PRIDs:
    2057831 (Jul-24) 2066506 (Aug-24) 2075169 (Sep-24) 2087834 (Oct-24)
    2095007 (Nov-24) 2106143 (Dec-24) 2113232 (Jan-25) 2123129 (Feb-25)
    2130161 (Mar-25) 2138675 (Apr-25) 2146353 (May-25) 2158341 (Jun-25)
    2169975 (Jul-25). PIB's allRel.aspx archive form is an ASP.NET postback
    maze that ignores replayed viewstate — discover PRIDs via search or the
    newsonair.gov.in WordPress API
    (https://newsonair.gov.in/wp-json/wp/v2/posts?search=EPFO+net+members),
    which mirrors every release with the exact figure.
  * Accuracy: first prints revise HEAVILY (sometimes >10% over later
    releases). This seed is the as-first-published series; a live fetcher
    should prefer the Payroll_Data_EPFO_*.pdf month-wise table (latest
    revision) over press-release headlines.
"""

LIVE_IDS = ["epfo"]


def fetch():
    print("epfo: SEEDED Jun-2024..Jul-2025 (first prints). Monthly payroll "
          "releases are suspended since the Jul-2025 data (EPFO 3.0/ECR "
          "migration) — see module docstring. Re-check PIB / newsonair for "
          "resumption before wiring this up.")


if __name__ == "__main__":
    fetch()
