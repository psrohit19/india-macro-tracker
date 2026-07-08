"""
World Gold Council Gold Demand Trends fetcher — LIVE. Populates: gold
(quarterly, tonnes — India CONSUMER demand = jewellery + bar & coin).

WGC's /download/file/ endpoints (PDF + xlsx tables) are Cloudflare-blocked
for non-browser clients, but the GDT web edition exposes the same
"demand in selected countries" tables as plain HTML on section subpages:

  https://www.gold.org/goldhub/research/gold-demand-trends/{report}/jewellery
  https://www.gold.org/goldhub/research/gold-demand-trends/{report}/investment

Each quarterly report carries either a [year-ago, current] pair or a
5-quarter trailing table with Q-labelled headers (e.g. Q1'25 ... Q1'26).
This fetcher walks the known quarterly report slugs oldest→newest, reads the
India row of every table whose header cells are quarter labels, and lets
newer reports overwrite older ones — WGC back-revisions (which can be large,
e.g. Q1'25 jewellery 71.4t → 81.6t) are absorbed automatically.
gold = jewellery tonnes + bar & coin tonnes for the same quarter.

New quarters: append the new report slug to REPORTS when GDT is published
(~1 month after quarter-end); slug pattern gold-demand-trends-qN-YYYY
(Q4 comes inside gold-demand-trends-full-year-YYYY, whose table layout is
misaligned/annual — skipped; Q4 is picked up from the next Q1 report's
5-quarter table instead).

KNOWN GAP: Q4'2022 (2022-10-01) — the only quarter not present in any
quarterly-report HTML table (full-year-2022 shows annual columns only).
"""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["gold"]
BASE = "https://www.gold.org/goldhub/research/gold-demand-trends/{}/{}"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

REPORTS = [                       # oldest → newest (newest wins on revision)
    "gold-demand-trends-q1-2023",
    "gold-demand-trends-q2-2023",
    "gold-demand-trends-q3-2023",
    "gold-demand-trends-q1-2024",
    "gold-demand-trends-q2-2024",
    "gold-demand-trends-q3-2024",
    "gold-demand-trends-q1-2025",
    "gold-demand-trends-q2-2025",
    "gold-demand-trends-q3-2025",
    "gold-demand-trends-q1-2026",
]
QLABEL = re.compile(r"^Q([1-4])'?\s?(\d{2})$")


def _india_quarters(html):
    """{iso_quarter_start: tonnes} for every Q-labelled India cell."""
    out = {}
    for tab in BeautifulSoup(html, "lxml").find_all("table"):
        if "India" not in tab.get_text():
            continue
        hdr = None
        for tr in tab.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if hdr is None and any(QLABEL.match(c) for c in cells):
                hdr = cells
            elif hdr and cells and cells[0] == "India" and len(cells) == len(hdr):
                for h_, v in zip(hdr, cells):
                    m = QLABEL.match(h_)
                    if m and re.match(r"^\d[\d.,]*$", v):
                        q, yy = int(m.group(1)), 2000 + int(m.group(2))
                        out[f"{yy}-{(q - 1) * 3 + 1:02d}-01"] = float(v.replace(",", ""))
    return out


def fetch():
    s = requests.Session()
    s.headers.update(H)
    jew, inv = {}, {}
    for rep in REPORTS:
        for sec, store in (("jewellery", jew), ("investment", inv)):
            try:
                store.update(_india_quarters(
                    s.get(BASE.format(rep, sec), timeout=60).text))
            except Exception as e:
                print(f"  gold: {rep}/{sec} FAILED ({e})")

    obs = {q: round(jew[q] + inv[q], 1) for q in jew if q in inv}
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / "gold.json").write_text(
        json.dumps({"freq": "Q", "obs": sorted(obs.items())}))
    last = sorted(obs)[-1]
    print(f"  gold: {len(obs)} obs, latest {last} = {obs[last]}t "
          f"(jew {jew[last]} + inv {inv[last]})")
    return obs


if __name__ == "__main__":
    fetch()
