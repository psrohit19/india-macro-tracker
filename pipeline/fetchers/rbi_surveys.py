"""RBI forward-looking survey series (seed-only fetcher stub).

Covers four survey series seeded in data/live/ from official RBI releases:

1. obicus_cu  -- OBICUS (Quarterly Order Books, Inventories and Capacity
   Utilisation Survey): headline (non-seasonally-adjusted) capacity
   utilisation (%) of the manufacturing sector. Quarterly. Each round
   reports CU for a reference quarter roughly 1-2 quarters before the
   release date. Seed dating: first month of the CALENDAR quarter the CU
   number refers to (e.g. CU for Q2:2025-26, i.e. Jul-Sep 2025 ->
   "2025-07-01").

2. ccs -- Consumer Confidence Survey, Current Situation Index (CSI).
   Bi-monthly rounds timed to the MPC cycle (Jan/Mar/May/Jul/Sep/Nov),
   released on policy day. Since late 2024 the urban survey is published
   as the "Urban Consumer Confidence Survey" (UCCS); the seeded series is
   the continuous urban CSI. Seed dating: first day of the month RBI
   names the round after (e.g. "May 2026 round" -> "2026-05-01").

3. ies -- Inflation Expectations Survey of Households (IESH): MEDIAN
   one-year-ahead inflation expectation (%). Bi-monthly, same round
   naming and dating convention as ccs.

4. ios -- Industrial Outlook Survey of the Manufacturing Sector:
   Business Expectations Index (BEI, >100 = expansion expected) for the
   quarter AHEAD. Quarterly rounds. Seed dating: first month of the
   calendar quarter in which the SURVEY ROUND was conducted (one quarter
   before the quarter the expectation refers to). E.g. round 113,
   conducted Jan-Mar 2026, reports BEI 118.8 for Q1:2026-27 -> dated
   "2026-01-01".

Publication mechanics / why this is a stub:
    RBI publishes these surveys as press releases ("RBI releases the
    results of Forward Looking Surveys") accompanying each bi-monthly MPC
    policy announcement, each linking to per-survey pages at
    https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=NNNNN with
    HTML tables plus xlsx/PDF attachments on rbidocs.rbi.org.in. There is
    NO stable API, no stable URL scheme (press-release ids and
    publication ids are opaque sequential integers), and the xlsx CDN
    (rbidocs.rbi.org.in) rejects non-browser clients. Automating this
    reliably requires scraping the press-release index around each MPC
    date; not implemented yet. Seed data in data/live/{obicus_cu,ccs,
    ies,ios}.json was hand-collected from the releases listed there.
"""


def fetch(series_id: str):
    """Placeholder. RBI survey series are seed-only for now (see module
    docstring). Raises NotImplementedError unconditionally."""
    raise NotImplementedError(
        "RBI survey series (obicus_cu, ccs, ies, ios) are seed-only: RBI "
        "publishes them as per-MPC press releases with no stable API. "
        "Refresh the seed JSONs manually from the latest 'RBI releases "
        "the results of Forward Looking Surveys' press release."
    )
