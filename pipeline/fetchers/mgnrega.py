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

SEED NOTES (2026-07-08) — data/live/mgnrega.json was OVERWRITTEN with a manual
seed ("seed": true); this fetcher's output (incremental-households-worked
proxy) does NOT match the catalog definition and produced 4 tiny values.
Do not re-enable without rework.

  * Seed definition: households that DEMANDED work in the month (nrega.nic.in
    MIS "work demand" metric, as compiled monthly by CMIE Economic Outlook).
  * Seed source: monthly series (Apr 2013-May 2026) embedded in the Next.js
    flight payload of
    https://indiamacroindicators.co.in/economic-indicators/mgnrega-work-demanded
    ("Source: CMIE Economic Outlook, 1 Finance Research"), fetched 2026-07-08.
    Values are that aggregator's snapshot; MIS back-revises upward, so early
    press prints can be a shade lower (e.g. May 2025: 28.32-28.39 mn in
    Jun/Jul-2025 press vs 28.4 mn here).
  * Cross-verified against independent press (10+ points, values and/or %YoY):
    BS 125050100784 (Apr'25 20.1mn -6.6%), Wire (May'25 28.39/May'24 27.18),
    BS 125070101054 (Jun'25 27.59, Jun'24 26.39), Swarajya (Jun'24 26.42),
    Drishti/ET (Jul'24 18.90 -19.5%), BS 125090101225 (Aug'25 -26%),
    BS 125110100027 (Oct'25 -35.3%), BS 125120101167 (Nov'25 ~-32%, "May &
    June only FY26 upticks"), BS 125010201127 (Dec'24 21.58), BS 125030300938
    (Feb'25 21.8 +~3%), BS 126033100997 (Mar'26 14.3 -23.2%), BS 126050100812
    (Apr'26 13.0 -35.3%), DEA MER May-2026 (Apr FY27 1.7 cr PERSONS -35.8%),
    Livemint 2026-03-25 (Feb'26 21.9 mn persons; FY26 six-year low).
  * Series ends Apr 2026: MGNREGA was REPEALED and replaced by VB-G RAM G
    w.e.f. 1 Jul 2026 (PIB PRID 2259703; Down To Earth). No press print exists
    for May/Jun 2026 monthly demand; CMIE has May 2026 = 2.05 cr (single
    source, could not be independently verified, therefore excluded). Jun 2026
    is the scheme's final month; treat the series as TERMINAL — future
    refreshes should track the VB-G RAM G successor metric instead.
  * MIS portals (mnregaweb4/nreganarep) still 401/timeout from this box;
    nrega.dord.gov.in + nregarep2.nic.in respond but report pages are gated.
    data.gov.in resource ee03643a has NO demand field (only worked/provided,
    verified 2026-07-08), so it cannot back this series at all.
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
    raise NotImplementedError(
        "DISABLED: data.gov.in resource ee03643a has NO work-demand field — this "
        "fetcher once overwrote the verified CMIE/press seed with wrong data. "
        "Series is terminal anyway (scheme repealed 1 Jul 2026)." )

def _old_fetch():
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
