"""
FADA vehicle-retail fetcher — LIVE. Populates: pv, tw, cv (monthly), tractors.

FADA press releases live at hashed URLs under fada.in/images/press-release/;
the listing page https://www.fada.in/press-release-list.php?page=N (N=1..6)
is crawled for links whose filename contains "Vehicle Retail Data".

Each monthly PDF carries (verified Jan'25 → Jun'26 releases):

  * "All India Vehicle Retail Data for <Mon>'YY" table —
        2W  18,28,458  18,44,947  15,08,378  -0.89%  21.22%
        (category, current month, previous month, year-ago month, MoM, YoY)
    so every release yields THREE dated observations per category; releases
    are processed oldest→newest and later releases overwrite earlier ones,
    which bakes in FADA/Vahan back-revisions automatically.
  * "Tractor OEM <Mon>'YY <Mon>'YY-1" market-share table whose
        Total  1,00,818  100%  80,456  100%
    row yields current + year-ago tractor retails.

Unit conversions to catalog units: pv & tw → lakh units (/1e5),
cv & tractors → '000 units (/1e3).

KNOWN GAP: FADA's listing page omits the Nov'25, Dec'25, Jan'26 and Feb'26
monthly releases (checked Jul 2026) even though the PDFs exist at hashed
URLs — those are pinned in EXTRA_URLS (found via web search of fada.in).
"""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["pv", "tw", "cv", "tractors"]
LIST_URL = "https://www.fada.in/press-release-list.php?page={}"
BASE = "https://fada.in/"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}
CAT_TO_SERIES = {"PV": "pv", "2W": "tw", "CV": "cv", "TRAC": "tractors"}
HDR_RE = re.compile(
    r"All India Vehicle Retail Data for ([A-Za-z]+)[’'](\d{2})\b(?![^\n]*YTD)")
ROW_RE = re.compile(
    r"^(2W|3W|PV|CV|TRAC|Total) ([\d,]+) ([\d,]+) ([\d,]+) (-?[\d.]+)% (-?[\d.]+)%")
FLOOR = "2024-01-01"   # older releases mix CY/festive tables — not worth parsing

# Monthly-release PDFs missing from press-release-list.php. They exist on the
# CDN (Google-indexed) but the CDN 404s requests from this environment, so the
# category-table values were hand-transcribed from the PDFs (Jul 2026) and are
# pinned here in RAW UNITS; used only when the month is absent from parsing.
# Nov'25 uses the revised prints from the Dec'25 release's Nov column.
#   1693661428b2e7...November 2025... / 1695cc82c07602...CY 2025 and December
#   2025... / 1698aa6afacdf0...January 2026...
PINNED = {
    "pv":       {"2025-11-01": 396_483, "2025-12-01": 379_671, "2026-01-01": 513_475},
    "tw":       {"2025-11-01": 2_546_184, "2025-12-01": 1_316_891, "2026-01-01": 1_852_870},
    "cv":       {"2025-11-01": 92_604, "2025-12-01": 83_666, "2026-01-01": 107_486},
    "tractors": {"2025-11-01": 126_033, "2025-12-01": 115_001, "2026-01-01": 114_759},
}
TRAC_TOTAL_RE = re.compile(r"Total ([\d,]+) 100% ([\d,]+) 100%")


def _n(s):
    return float(s.replace(",", ""))


def _shift(y, m, k):
    """(year, month) shifted by k months."""
    idx = y * 12 + (m - 1) + k
    return idx // 12, idx % 12 + 1


def _iso(y, m):
    return f"{y:04d}-{m:02d}-01"


def _pdf_text(content):
    import io
    import pdfplumber
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def _parse_release(txt):
    """-> {series_id: {iso: units}} from one press-release PDF's text.

    Iterates over every "All India Vehicle Retail Data for X'YY" header and
    parses only those where X is a calendar month (skips FY'26 / CY'24 /
    42-day-festive tables, whose rows also don't fit the 5-column regex).
    """
    out = {s: {} for s in SERIES_IDS}
    cur = None
    for m in HDR_RE.finditer(txt):
        mon = MONTHS.get(m.group(1)[:3].lower())
        if not mon:
            continue
        y = 2000 + int(m.group(2))
        cur, prev, ago = (y, mon), _shift(y, mon, -1), (y - 1, mon)
        for line in txt[m.end():m.end() + 1800].splitlines():
            r = ROW_RE.match(line.strip())
            if r and r.group(1) in CAT_TO_SERIES:
                sid = CAT_TO_SERIES[r.group(1)]
                for (yy, mm), v in zip((cur, prev, ago), r.groups()[1:4]):
                    out[sid][_iso(yy, mm)] = _n(v)

    t = re.search(r"Tractor OEM", txt)
    if t and cur:
        tt = TRAC_TOTAL_RE.search(txt[t.end():t.end() + 2500])
        if tt:
            y, mon = cur
            out["tractors"].setdefault(_iso(y, mon), _n(tt.group(1)))
            out["tractors"].setdefault(_iso(y - 1, mon), _n(tt.group(2)))
    for sid in out:
        out[sid] = {d: v for d, v in out[sid].items() if d >= FLOOR}
    return out


def fetch(pages=3):
    s = requests.Session()
    s.headers.update(H)
    links = {}
    for p in range(1, pages + 1):
        soup = BeautifulSoup(s.get(LIST_URL.format(p), timeout=60).text, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf") and "vehicle retail data" in href.lower():
                links[href if href.startswith("http") else BASE + href.lstrip("/")] = None

    per_series = {sid: {} for sid in SERIES_IDS}
    for url in sorted(links):        # hashed prefixes sort oldest→newest
        try:
            parsed = _parse_release(_pdf_text(s.get(url, timeout=120).content))
        except Exception as e:
            print(f"  fada: FAILED {url[-60:]} ({e})")
            continue
        for sid, d in parsed.items():
            per_series[sid].update(d)   # later releases overwrite (revisions)
    for sid, d in PINNED.items():       # fill listing-page gaps, never overwrite
        for iso, v in d.items():
            per_series[sid].setdefault(iso, v)

    scale = {"pv": 1e5, "tw": 1e5, "cv": 1e3, "tractors": 1e3}
    LIVE.mkdir(parents=True, exist_ok=True)
    for sid, d in per_series.items():
        if not d:
            continue
        f = LIVE / f"{sid}.json"
        obs = {dd: v for dd, v in json.loads(f.read_text())["obs"]} if f.exists() else {}
        seeded = json.loads(f.read_text()).get("seed") if f.exists() else False
        for iso, units in d.items():
            obs[iso] = round(units / scale[sid], 3)
        payload = {"freq": "M", "obs": sorted(obs.items())}
        if seeded:
            payload["seed"] = True      # keep flag if file still holds seeds
        f.write_text(json.dumps(payload))
        last = sorted(obs)[-1]
        print(f"  {sid}: {len(obs)} obs, latest {last} = {obs[last]}")


if __name__ == "__main__":
    fetch()
