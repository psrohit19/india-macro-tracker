"""
GSTN monthly collections fetcher — SEEDED (data/live/gst.json hand-assembled
from official PDFs on 2026-07-08). Populates: gst (GROSS monthly GST, ₹ lakh cr).

Verified behaviour (Jul 2026):
  * https://www.gst.gov.in/newsandupdates is behind an F5/TSPD JavaScript
    challenge — plain HTTP clients get an anti-bot page, NOT the news list.
    Do not scrape it directly.
  * The monthly release PDFs live on https://tutorial.gst.gov.in/downloads/news/
    and ARE directly fetchable (no challenge) — but the directory listing 404s
    and the filename pattern has changed several times:
      Jun–Oct 2024 : revenue_report_{mon}{yy}.pdf            (e.g. revenue_report_oct24.pdf)
      Jul 2024     : approved_monthly_gst_data_for_publishing_july_2024.pdf
      Nov 24–Sep 25: approved_monthly_gst_data_for_publishing_{mon}_{yyyy}.pdf
                     (month token inconsistent: dec_2024 but june_2025/july_2025)
      Nov 2025     : approved_monthly_gst_revenue_data_for_publishing_nov_2025_final.pdf
      Dec 2025     : monthly_gst_data_for_publishing_dec_2025_final_01jan2026.pdf
      Jan 2026     : final_approved_monthly_gst_data_for_publishing_jan_2026_01022026.pdf
                     (suffix = publication date; NOT guessable for other months)
    In practice: resolve each month's filename via a web search for
    "tutorial.gst.gov.in <month>" or via taxguru.in's monthly article
    ("gross-net-gst-revenue-collections-month-{mon}-{yyyy}.html"), which
    reprints the official table verbatim.
  * Parse: page 1 line "Total Gross GST Revenue <yr-ago> <month> <%> <ytd...>"
    — take the SECOND number (current month, ₹ crore); divide by 1e5 for
    ₹ lakh cr. Digits are sometimes space-split by the PDF ("1 ,82,075").

Series basis — IMPORTANT:
  * Values are GROSS (pre-refund), as printed in each month's own release.
  * GST 2.0 rate rationalisation (22 Sep 2025) abolished compensation cess on
    most goods. From the Nov-2025 release the headline gross excludes most
    cess (~₹13k cr/month) and the release restates its year-ago base ex-cess
    (e.g. Jun-2025: ₹1,84,597 cr as printed in Jul-2025 vs ₹1,71,105 cr as
    restated in the Jun-2026 release). This series keeps AS-PRINTED values, so
    there is a structural level break at Nov-2025; official YoY %s from 2026
    releases will not match a naive YoY computed off this series for
    Oct-2025..Sep-2026.

Release timing: ~1st of the following month on the GST portal (detailed PIB
press release discontinued Aug 2024).
"""

# Filename map discovered 2026-07-08 (all verified fetchable, HTTP 200):
BASE = "https://tutorial.gst.gov.in/downloads/news/"
KNOWN_PDFS = {
    "2024-06": "revenue_report_jun24.pdf",
    "2024-07": "approved_monthly_gst_data_for_publishing_july_2024.pdf",
    "2024-08": "revenue_report_aug24.pdf",
    "2024-09": "revenue_report_sep24.pdf",
    "2024-10": "revenue_report_oct24.pdf",
    "2024-11": "approved_monthly_gst_data_for_publishing_nov_2024.pdf",
    "2024-12": "approved_monthly_gst_data_for_publishing_dec_2024.pdf",
    "2025-01": "approved_monthly_gst_data_for_publishing_jan_2025.pdf",
    # 2025-02: no official PDF found; value from taxguru reprint (see docstring)
    "2025-03": "approved_monthly_gst_data_for_publishing_mar_2025.pdf",
    "2025-04": "approved_monthly_gst_data_for_publishing_apr_2025.pdf",
    "2025-05": "approved_monthly_gst_data_for_publishing_may_2025.pdf",
    "2025-06": "approved_monthly_gst_data_for_publishing_june_2025.pdf",
    "2025-07": "approved_monthly_gst_data_for_publishing_july_2025.pdf",
    "2025-08": "approved_monthly_gst_data_for_publishing_aug_2025.pdf",
    "2025-09": "approved_monthly_gst_data_for_publishing_sep_2025.pdf",
    # 2025-10: value from taxguru reprint of the official release
    "2025-11": "approved_monthly_gst_revenue_data_for_publishing_nov_2025_final.pdf",
    "2025-12": "monthly_gst_data_for_publishing_dec_2025_final_01jan2026.pdf",
    "2026-01": "final_approved_monthly_gst_data_for_publishing_jan_2026_01022026.pdf",
    # 2026-02..2026-06: values from taxguru/taxo reprints, cross-checked with
    # ANI/saginfotech/IBEF coverage (Jun-2026: ₹1,94,812 cr gross).
}


def fetch():
    """Stub — gst.json is currently a hand-verified seed (25 months,
    Jun-2024..Jun-2026). A live implementation should: (1) resolve the new
    month's PDF filename (search/taxguru), (2) download from BASE, (3) parse
    the 'Total Gross GST Revenue' row, (4) append month/1e5 to the JSON."""
    raise NotImplementedError("gst.json is seeded; see module docstring")


if __name__ == "__main__":
    fetch()
