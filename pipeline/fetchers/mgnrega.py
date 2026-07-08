"""
MGNREGA work-demand fetcher — LIVE. Populates: mgnrega (unit: cr households, M).

Source: data.gov.in resource ee03643a-ee4c-48c2-ac30-9f2ff26ab722
("District-wise MGNREGA Data at a Glance", Ministry of Rural Development;
mirrors nrega.nic.in R1 'at a glance' MIS data).

Verified behaviour (Jul 2026):
  * Field `Total_Households_Worked` is FY-CUMULATIVE (resets each April):
    e.g. PUNE FY2024-25 Oct 13,747 -> Dec 15,852 -> Jan ~17,912 -> Feb 20,265
    (monotonically rising within the FY). We therefore DIFFERENCE consecutive
    months within a fiscal year; April = the April level itself.
  * The dataset holds MULTIPLE SNAPSHOT ROWS per (fin_year, month, district) —
    re-uploads taken at different dates, values rising as MIS data completes
    (April 2025 for one district: 0, 0, 788, 5869). We take the MAX per
    (month, district) as the most complete snapshot.
  * Month labels are inconsistent across years ("April"/"May"/"June" vs
    "Jan"/"Feb"/"Sept") — normalized via prefix match.
  * `filters[fin_year]` + `fields=` both work; limit up to 10000/page.
    Full-FY row volume ~100-170k rows -> field-restricted pagination.
  * The API key is the public data.gov.in sample key.

CAVEAT (documented in AUDIT.md): differencing cumulative *unique* households
worked FYTD gives "incremental households worked in the month", which
understates gross monthly work demand (a household working in two months is
counted only in the first). Trend/seasonality remain informative; values are
lower than the nrega.nic.in "households demanded work in month" press figure.

Writes data/live/mgnrega.json: {"freq": "M", "obs": [["YYYY-MM-01", cr], ...]}
"""
import json
import time
from datetime import date
from pathlib import Path

import requests

RES = "ee03643a-ee4c-48c2-ac30-9f2ff26ab722"
KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
BASE = f"https://api.data.gov.in/resource/{RES}"
FIELDS = "fin_year,month,district_code,Total_Households_Worked"
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}

MONTH_NUM = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
             "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
START_FY = 2023            # dataset begins FY2023-24


def _month_num(label):
    l = (label or "").strip().lower()[:3]
    return MONTH_NUM.get(l)


def _rows(fin_year):
    """Paginate all field-restricted rows for one fiscal year."""
    out, offset, limit = [], 0, 10000
    while True:
        for attempt in range(4):
            try:
                r = requests.get(BASE, timeout=90, headers=H, params={
                    "api-key": KEY, "format": "json", "limit": limit,
                    "offset": offset, "fields": FIELDS,
                    "filters[fin_year]": fin_year})
                r.raise_for_status()
                d = r.json()
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))
        recs = d.get("records", [])
        out.extend(recs)
        offset += limit
        if len(recs) < limit or offset >= int(d.get("total") or 0):
            break
        time.sleep(0.3)
    return out


def fetch():
    print("MGNREGA live pull (data.gov.in):")
    today = date.today()
    cur_fy = today.year if today.month >= 4 else today.year - 1
    obs = {}
    for fy in range(START_FY, cur_fy + 1):
        fy_label = f"{fy}-{fy + 1}"
        rows = _rows(fy_label)
        if not rows:
            continue
        # max snapshot per (month, district)
        best = {}
        for x in rows:
            m = _month_num(x.get("month"))
            v = x.get("Total_Households_Worked")
            if m is None or v in (None, ""):
                continue
            k = (m, x.get("district_code"))
            v = int(float(v))
            if v > best.get(k, -1):
                best[k] = v
        # all-India cumulative per month, in FY order Apr..Mar
        cum = {}
        for (m, _), v in best.items():
            cum[m] = cum.get(m, 0) + v
        fy_months = [m for m in list(range(4, 13)) + list(range(1, 4)) if m in cum]
        prev = 0
        for m in fy_months:
            y = fy if m >= 4 else fy + 1
            iso = f"{y}-{m:02d}-01"
            monthly = cum[m] - prev
            prev = cum[m]
            if monthly <= 0:
                continue          # snapshot artefact; drop rather than mislead
            obs[iso] = round(monthly / 1e7, 3)   # households -> crore
        print(f"  {fy_label}: {len(fy_months)} months, "
              f"FY cum {prev / 1e7:.2f} cr households")
    # drop the in-progress month (data-entry lag badly understates it)
    cur_iso = f"{today.year}-{today.month:02d}-01"
    obs.pop(cur_iso, None)
    out = sorted(obs.items())
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / "mgnrega.json").write_text(
        json.dumps({"freq": "M", "obs": out}))
    print(f"  mgnrega: {len(out)} months, latest {out[-1][0]} = {out[-1][1]}")
    return out


if __name__ == "__main__":
    fetch()
