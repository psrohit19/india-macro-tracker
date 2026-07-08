"""
MoSPI monthly PLFS bulletin fetcher — SEEDED (stub). Populates: plfs_ur, lfpr.

Series: all-India (rural+urban), age 15+, Current Weekly Status (CWS).
Monthly bulletins exist only from April 2025 (first-ever monthly PLFS print,
released May 2025). data/live/{plfs_ur,lfpr}.json currently hand-seeded from
the sources below (verified Jul 2026); 14 obs Apr-2025..May-2026.

Sources & verified quirks (Jul 2026):
  * Press notes (PDF): https://www.mospi.gov.in/uploads/latestReleases/
    latest_release_{timestamp}_{uuid}_Monthly_Press_note_{Month}_{Year}.pdf
    - timestamp+uuid are NOT guessable; discover via the mospi.gov.in
      press-release page (JS-rendered — the raw HTML has no links; use a
      search engine or a headless browser) or via PIB.
    - Each note carries line charts of LFPR/WPR/UR covering EVERY month since
      Apr-2025 with data labels. pdfplumber extract_text() scrambles the
      label order, but extract_words() x0/top coordinates reconstruct the
      series exactly: labels cluster into 12 x-columns (one per month tick)
      and 3 y-bands (rural top, overall middle, urban bottom for LFPR;
      urban/overall/rural for UR). This is how the seed was transcribed —
      values cross-checked between the Jan-2026 and Mar-2026 notes (identical
      overlap) and against PIB releases for Apr/May-2026.
  * PIB mirror (fetchable, has headline numbers only):
    e.g. May-2026: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2272969
         Apr-2026: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2261386
  * Release cadence: ~15th-16th of the following month (Jun-2026 bulletin due
    ~mid-Jul 2026).
  * Gotcha: quote the CWS 15+ all-India "overall person" rate; the bulletin
    also carries rural/urban and male/female splits, and quarterly urban-only
    bulletins use a different (smaller) sample — do not mix.

TODO to go live: resolve the latest press-note PDF URL (search engine or the
mospi press-release JSON the site's JS calls), download, run the positional
chart-label extraction above, and rewrite the full history each month (charts
restate all months, catching revisions).
"""

LIVE_IDS = ["plfs_ur", "lfpr"]


def fetch():
    print("plfs: SEEDED — monthly PLFS press-note PDF URLs are not guessable "
          "(timestamped uploads); see module docstring for the extraction "
          "recipe. data/live/plfs_ur.json + lfpr.json hand-seeded "
          "Apr-2025..May-2026.")


if __name__ == "__main__":
    fetch()
