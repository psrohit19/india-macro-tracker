"""
MoSPI eSankhyiki API fetcher — LIVE. Populates: cpi, cfpi, wpi, iip.

Verified behaviour (Jul 2026, unauthenticated):
  * /api/cpi/getCPIIndex   — needs year+month+state="All India"; 'inflation'
    field gives YoY directly. Combined/General = headline; Consumer Food
    Price/Combined = CFPI. 2026 (new 2024=100 base) not yet exposed — latest
    live print is Dec 2025. Token auth raises row caps but isn't required
    for these filtered calls.
  * /api/wpi/getWpiRecords — year+month; first 'Wholesale price index' row is
    the headline index level; YoY computed here from same-month prior year.
  * /api/iip/getIIPMonthly — financial_year + type=General; 'growth_rate' is
    the YoY print (base 2022-23 from FY26).

Writes data/live/{id}.json:  {"freq": "M", "obs": [["YYYY-MM-01", value], ...]}
Incremental: cached months are not refetched except the trailing 3 (revisions).
"""
import json
import time
from datetime import date
from pathlib import Path

import requests

BASE = "https://api.mospi.gov.in"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
SERIES_IDS = ["cpi", "cfpi", "wpi", "iip"]
START_YEAR = 2015          # ~10y of history for the long-term average


def _get(path, params, tries=3):
    for i in range(tries):
        try:
            r = requests.get(f"{BASE}{path}", params=params, timeout=45, headers=H)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def _load(sid):
    f = LIVE / f"{sid}.json"
    if f.exists():
        return {d: v for d, v in json.loads(f.read_text())["obs"]}
    return {}


def _save(sid, obs_map):
    LIVE.mkdir(parents=True, exist_ok=True)
    obs = sorted(obs_map.items())
    (LIVE / f"{sid}.json").write_text(json.dumps({"freq": "M", "obs": obs}))
    print(f"  {sid}: {len(obs)} months, latest {obs[-1][0]} = {obs[-1][1]}")


def _stale(iso, cached, keep_recent=3):
    """Refetch if not cached, or within the trailing revision window."""
    recent = sorted(cached)[-keep_recent:] if cached else []
    return iso not in cached or iso in recent


def fetch_cpi():
    """IMPORTANT (verified): the API IGNORES month/state filters — it returns
    latest-month rows regardless. Only year + limit + page behave. So: paginate
    each year's full row set and filter client-side by each row's own labels."""
    cpi, cfpi = _load("cpi"), _load("cfpi")
    today = date.today()
    for y in range(START_YEAR, today.year + 1):
        # cached full years (12 months) outside the revision window: skip
        have = [d for d in cpi if d.startswith(str(y))]
        if len(have) == 12 and y < today.year - 1:
            continue
        for page in range(1, 8):
            rows = _get("/api/cpi/getCPIIndex",
                        {"base_year": "2012", "year": y, "limit": 5000, "page": page})
            time.sleep(0.4)
            for x in rows:
                if (x.get("state") != "All India" or x.get("sector") != "Combined"
                        or x.get("inflation") is None):
                    continue
                iso = f"{y}-{MONTHS.index(x['month']) + 1:02d}-01"
                if x.get("group") == "General":
                    cpi[iso] = float(x["inflation"])
                elif (x.get("group") == "Consumer Food Price"
                      and "Overall" in (x.get("subgroup") or "")):
                    cfpi[iso] = float(x["inflation"])
            if len(rows) < 5000:
                break
    _save("cpi", cpi)
    _save("cfpi", cfpi)


def fetch_wpi():
    """Same API quirk: month param ignored. One big year query returns all
    month-labelled rows; headline = majorgroup 'Wholesale price index'."""
    idx = {}
    today = date.today()
    for y in range(START_YEAR - 1, today.year + 1):
        rows = _get("/api/wpi/getWpiRecords", {"year": y, "limit": 10000})
        time.sleep(0.4)
        for x in rows:
            if x.get("majorgroup") == "Wholesale price index" and x.get("index_value"):
                idx[(y, MONTHS.index(x["month"]) + 1)] = float(x["index_value"])
    out = {}
    for (y, m), v in idx.items():
        prev = idx.get((y - 1, m))
        if prev and 0.8 < v / prev < 1.25:    # guard base-change jumps
            out[f"{y}-{m:02d}-01"] = round((v / prev - 1) * 100, 2)
    _save("wpi", out)


def fetch_iip():
    out = _load("iip")
    today = date.today()
    fy_end = today.year + 1 if today.month >= 4 else today.year
    for fy in range(START_YEAR, fy_end):
        rows = _get("/api/iip/getIIPMonthly",
                    {"financial_year": f"{fy}-{fy + 1}", "type": "General", "limit": 100})
        time.sleep(0.25)
        for x in rows:
            if x.get("category") != "General" or not x.get("growth_rate"):
                continue
            y, mname = int(x["year"]), x["month"]
            m = MONTHS.index(mname) + 1
            out[f"{y}-{m:02d}-01"] = float(x["growth_rate"])
    _save("iip", out)


def fetch():
    print("eSankhyiki live pull:")
    fetch_iip()
    fetch_wpi()
    fetch_cpi()


if __name__ == "__main__":
    fetch()
