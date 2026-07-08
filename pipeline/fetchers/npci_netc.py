"""
NPCI NETC FASTag fetcher — SEEDED (data/live/fastag.json hand-assembled on
2026-07-08). Populates: fastag (monthly NETC toll VALUE, ₹ cr).

Access status (verified Jul 2026):
  * www.npci.org.in is Akamai geo/IP-blocked from this environment — every
    path (incl. robots.txt) returns 403 "Access Denied" regardless of headers.
  * The site moved to a React SPA ~Oct 2025; the stats page relocated from
    /what-we-do/netc-fastag/product-statistics to
    /product/netc/product-statistics and the table now loads client-side from
      /api/product-statistic/tab/detail?product_name=netc
        &tab_name=netc-fas-tag-statistics&year_range=2025-26
        &excel_type=monthly&page_no=1&page_size=12&locale=en
    (tab slug discovered from the archived /api/product-statistic/tabs
    response; year_range values: 2024-25, 2025-26, 2026-27).
  * Workarounds used for the seed (all official-NPCI numbers):
      - Wayback capture 20250907100503 of the OLD page: full monthly table
        (Banks live / Tag issuance / Volume Mn / Amount Cr) through Jul-2025.
      - NPCI "Retail Payments Statistics" PDFs (uploads/RETAIL_PAYMENTS_
        STATISTICS_*.pdf), Wayback captures: Sep-2025 edition gives Jul/Aug/
        Sep-25 monthly; 08_04_2026 edition gives Jan/Feb/Mar-26 monthly plus
        FY quarterly totals. NETC row values are in ₹ Bn (x100 = ₹ cr).
      - Cross-checks: FY25-26 Q1 total 206.82 Bn == Apr+May+Jun-25 page values
        to the rupee, and == "Rs 20,682 cr in Q1 FY26" (Deccan Herald, NETC
        data). IHMCL VC-wise NH-plaza PDFs are only ~46-50% of NETC value —
        NOT usable as a substitute level.

Known gaps in the seed:
  * Oct/Nov/Dec-2025 monthly values are OMITTED — only the Q3 FY26 total
    (219.95 Bn) is published in the archived RPS PDFs and no per-month source
    could be verified. Sum of any future backfill must equal ₹21,995 cr.
  * Apr/May/Jun-2026 not yet obtainable (no Wayback capture of a newer RPS
    edition; SPN capture attempts returned 520). Latest seeded month: Mar-2026.
  * Since 15 Aug 2025, NETC data EXCLUDES FASTag Annual Pass and Maharashtra
    EV-exempt trips (per NPCI's own disclaimer) — small level drag on
    post-Aug-2025 values vs before.

Definition: value of toll transactions processed on NETC in the month, all
issuer banks, national + state highways. Release: early following month.
"""

API = ("https://www.npci.org.in/api/product-statistic/tab/detail"
       "?product_name=netc&tab_name=netc-fas-tag-statistics"
       "&year_range={fy}&excel_type=monthly&page_no=1&page_size=12&locale=en")
LEGACY_PAGE = "https://www.npci.org.in/product/netc/product-statistics"


def fetch():
    """Stub — fastag.json is a hand-verified seed (33 months, Apr-2023..
    Mar-2026, with an Oct-Dec-2025 hole). A live implementation needs an
    India-egress or browser-grade client for the API above, or should watch
    web.archive.org for fresh captures of the NPCI Retail Payments Statistics
    PDF (uploads/RETAIL_PAYMENTS_STATISTICS_*.pdf)."""
    raise NotImplementedError("fastag.json is seeded; see module docstring")


if __name__ == "__main__":
    fetch()
