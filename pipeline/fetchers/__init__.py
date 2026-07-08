"""
Fetcher registry.

Each fetcher module exposes:  fetch() -> list[dict(series_id, period_iso, value)]
and declares SERIES_IDS (the catalog ids it populates).

refresh.py calls every registered fetcher, upserts observations into
data/history.parquet (or Postgres in production), recomputes rollups and
comparisons, and rebuilds dashboard.html. A fetcher that raises is skipped —
the dashboard keeps the last good values and the freshness table shows staleness.

Wiring order (easiest first — see BLUEPRINT.md §5):
  1. esankhyiki   CPI / WPI / IIP / GDP / PFCE   (official MoSPI API, token)
  2. datagovin    power gen, air pax, MGNREGA    (data.gov.in keyed API)
  3. rbi_files    card spends, UPI (PSI xlsx), sectoral credit (Excel downloads)
  4. nsdl_fii     FPI daily flows                (ASP.NET page parse)
  5. nse_dii      DII daily flows                (cookie-primed JSON, use nsepython)
  6. pdf_pack     GST, trade, EPFO, PLFS, core-8 (PDF table extraction)
  7. scrape_pack  FADA, TMA, IMD, CWC, WSS...    (HTML parsing)
"""
REGISTRY = []


def register(mod):
    REGISTRY.append(mod)
    return mod
