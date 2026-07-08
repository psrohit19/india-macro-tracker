"""
Policy repo rate — SEEDED (data/live/repo.json, "seed": true), stub fetcher.

The seed is a 10-year monthly month-end series (Jul 2016 - Jun 2026) built
from the public MPC decision history:
  6.50 (Apr'16) -> 6.25 (4 Oct'16) -> 6.00 (2 Aug'17) -> 6.25 (6 Jun'18)
  -> 6.50 (1 Aug'18) -> 6.25 (7 Feb'19) -> 6.00 (4 Apr'19) -> 5.75 (6 Jun'19)
  -> 5.40 (7 Aug'19) -> 5.15 (4 Oct'19) -> 4.40 (27 Mar'20) -> 4.00 (22 May'20)
  -> 4.40 (4 May'22) -> 4.90 (8 Jun'22) -> 5.40 (5 Aug'22) -> 5.90 (30 Sep'22)
  -> 6.25 (7 Dec'22) -> 6.50 (8 Feb'23) -> 6.25 (7 Feb'25) -> 6.00 (9 Apr'25)
  -> 5.50 (6 Jun'25) -> 5.25 (5 Dec'25, held through Jul 2026).
The Feb 2025 - Jul 2026 leg was verified week-by-week against the RBI WSS
"Ratios and Rates" table (Policy Repo Rate row), and the current 5.25% level
against the daily Money Market Operations release (SDF 5.00 / MSF 5.50
corridor).

TO AUTOMATE LATER: parse the latest WSS 'Ratios and Rates' table
(https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=4,
helpers already in rbi_wss.py: _section_entries(4, n) + _table_cells) — the
"Policy Repo Rate" row carries five recent weekly values; append the current
month's month-end level after each MPC week. Rate changes only happen at
six scheduled MPC meetings a year (plus rare off-cycle moves), so a weekly
check is ample.
"""

SERIES_IDS = ["repo"]


def fetch():
    print("  repo: seeded series (data/live/repo.json) — see docstring "
          "for the automation plan; not fetching.")


if __name__ == "__main__":
    fetch()
