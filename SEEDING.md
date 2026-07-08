# Live-data file contract (for fetchers AND manual seeds)

Every series goes live by writing data/live/{series_id}.json:

    {"freq": "M", "obs": [["YYYY-MM-01", value], ...], "seed": true}

- freq: the catalog frequency of that series (D/W/F/M/B/Q/H)
- obs: sorted [iso_date, float] pairs, oldest->newest. Dates use period START
  (monthly = 1st of month; quarterly = 1st month of the CALENDAR quarter;
  daily/weekly = the actual date).
- "seed": true  -> values hand-transcribed from official sources (no fetcher yet)
  omit for fetcher-written data.
- MINIMUM 14 observations or the series stays SAMPLE (need YoY + 12-period avg).
  Prefer 24-40+ where available.
- Units MUST match the catalog unit exactly (pipeline/catalog.py) — e.g. gst is
  "₹ lakh cr" (2.01), not crore; fx_reserves is US$ bn; upi is ₹ lakh cr.
- Rates in % YoY as printed. Values already YoY-transformed where the catalog
  unit says "% YoY".

Every seeded/fetched series MUST append one line to AUDIT.md:
    | series_id | latest period | value | source URL | how verified |
