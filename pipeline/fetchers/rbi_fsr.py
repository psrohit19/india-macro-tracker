"""
GNPA ratio (SCBs, half-yearly) — SEEDED (data/live/gnpa.json, "seed": true),
stub fetcher.

The RBI Financial Stability Report is a ~11 MB half-yearly PDF (Jun & Dec)
— not worth automating for two data points a year. The seed covers Mar 2019
- Mar 2026 (15 half-years, reference dates = the Mar/Sep month the ratio is
measured at):

  Mar-19 9.3  Sep-19 9.3  Mar-20 8.5  Sep-20 7.5  Mar-21 7.5  Sep-21 6.9
  Mar-22 5.9  Sep-22 5.0  Mar-23 3.9  Sep-23 3.2  Mar-24 2.8  Sep-24 2.6
  Mar-25 2.3  Sep-25 2.2  Mar-26 1.8

Provenance: Mar-23/Sep-23/Mar-24 confirmed from the FSR release press
notes (prid 55943 / 57005 / 58169); Mar-25 (2.3), Sep-25 (2.2) and Mar-26
(1.8, "multi-decadal low") read directly out of the FSR Jun-2025 / Dec-2025
/ Jun-2026 PDFs (pdftotext on the full-report PDF linked from
https://www.rbi.org.in/Scripts/FsReports.aspx via each release's
PublicationReportDetails page). Older points are the figures printed in the
corresponding half-year's FSR (public record).

TO AUTOMATE LATER (twice-yearly): from FsReports.aspx take the newest
"RBI releases the Financial Stability Report" press release, follow
PublicationReportDetails.aspx -> the 0FSR*.PDF full report (note: the host
rbidocs.rbi.org.in needs the browser-header session trick in rbi_files.py),
pdftotext it and regex
    r"GNPA\\s+ratio[^.]*?(?:low|declin|stood)[^.]*?(\\d\\.\\d)\\s*per cent"
around the "II.1.2 Asset Quality" section. Values are also announced in
most (not all) FSR press releases as "multi-year low of X.X per cent".
"""

SERIES_IDS = ["gnpa"]


def fetch():
    print("  gnpa: seeded series (data/live/gnpa.json) — see docstring "
          "for the automation plan; not fetching.")


if __name__ == "__main__":
    fetch()
