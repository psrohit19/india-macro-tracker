"""
CWC reservoir-storage fetcher — SEEDED (stub). Populates: reservoirs.

Series: live storage in the CWC-monitored major reservoirs as % of their
total live storage capacity, from the Central Water Commission's weekly
(Thursday) Reservoir Storage Bulletin.

Monitored set / denominator (changes over time — a key caveat):
  * 2025 bulletins: 161 reservoirs, total live capacity 182.375 BCM.
  * 2026 bulletins: 166 reservoirs, total live capacity 183.565 BCM.
  Percent-of-capacity is comparable across the change; BCM levels are not.

Source landscape (verified Jul 2026):
  * cwc.gov.in (http and https, with and without /en/, including the bulletin
    pages /reservoir-level-storage-bulletin, /reservoirs-storage-bulletin and
    /en/file/<id>/download?token=... PDF links) returns a JSON
    {"code":"401","message":"Unauthorized"} to datacenter IPs — an API
    gateway/WAF, not basic auth. Browser headers don't help.
  * ffs.india-water.gov.in and indiawris.gov.in/arms.indiawris.gov.in —
    connection refused / egress-denied from this box.
  * PIB's Jal Shakti feed (ministry code 1336 on /allRel.aspx) does NOT carry
    the weekly bulletin (checked Jun-Sep 2025 and Jun-Jul 2026 listings).
  * What works: weekly press coverage of each bulletin, which reprints the
    all-India live storage (BCM) and % of capacity, plus last-year and
    10-year-average comparisons. Reliable repeaters: Down To Earth
    (downtoearth.org.in/water), ChiniMandi, Businessworld, Odisha Connect,
    ETV Bharat, Business Standard. Cross-checking two outlets per bulletin
    is straightforward (they quote the same CWC BCM figures to 3 decimals).
  * The bulletins' "corresponding period last year" BCM figures are for the
    *current* reservoir set, so LY%-of-capacity can be derived against the
    current capacity — used (and flagged in AUDIT.md) for 2025 weeks whose
    own coverage wasn't independently found.

data/live/reservoirs.json is hand-seeded ("seed": true) from that coverage;
see AUDIT.md for the article URL behind each anchor point.

Seasonal caveats: storage troughs in Jun (~25-35%) and peaks post-monsoon
(Sep-Oct, 2025 season ~85%+). The file mixes the strong-monsoon 2025 season
with the deficient 2026 one (26-28% through early Jul 2026, ~39% below the
2025 corresponding weeks). Compare % of capacity and YoY, never BCM across
the 161->166 reservoir-set expansion.
"""

# Stub: series is seeded. A live fetcher needs either an India-hosted proxy
# for cwc.gov.in or a stable news wire; neither is wired yet.

def fetch():
    print("cwc: reservoirs is hand-seeded (see data/live/reservoirs.json); "
          "cwc.gov.in is WAF-gated from this box")


if __name__ == "__main__":
    fetch()
