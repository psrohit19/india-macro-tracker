"""
MoSPI eSankhyiki National Accounts (NAS) fetcher — LIVE. Populates: gdp, pfce.

Verified behaviour (Jul 2026, unauthenticated):
  * GET https://api.mospi.gov.in/api/nas/getNASData with params
        series=Current, frequency=Quarterly, financial_year=..., indicator_code=N
    — like the CPI API, the frequency/financial_year filters are IGNORED:
    every call returns the full annual+quarterly panel for that indicator.
    Filter client-side on row['quarter'] not None. Paginate with page=/limit=
    (meta_data.totalPages).
  * indicator_code map (probed 1-22):
        1 GVA, 2 net taxes, 3 taxes, 4 subsidies, 5 GDP, 6 CFC, 7 NDP,
        8 GCF by industry, 9 GFCF, 10 PFCE, 11 GFCE, 12 change in stock,
        13 valuables, 14 exports, 15 imports, 16 primary income, 17 GNI,
        18 transfers, 19 GNDI, 20 gross saving, 21 GVA growth, 22 GDP growth.
    Codes 21/22 (growth) return NULL current/constant_price on quarterly rows,
    so YoY is computed here from indicator 5/10 constant_price levels (₹ crore).
  * Two bases coexist in the payload: base_year '2011-12'
    (2011-12 Q1 .. 2025-26 Q2, the pre-rebasing series) and '2022-23'
    (2022-23 Q1 .. latest, first published 27 Feb 2026). YoY is computed
    strictly WITHIN a base; the spliced output uses the new 2022-23-base YoY
    from 2023-24 Q1 onward and the old-base YoY before that.

Fiscal quarters map to calendar-quarter starts per SEEDING.md:
    Q1 (Apr-Jun) -> YYYY-04-01, Q2 -> YYYY-07-01, Q3 -> YYYY-10-01,
    Q4 (Jan-Mar) -> (YYYY+1)-01-01.

Writes data/live/{gdp,pfce}.json: {"freq": "Q", "obs": [[date, %YoY], ...]}
"""
import json
from pathlib import Path

import requests

BASE = "https://api.mospi.gov.in"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

INDICATORS = {"gdp": "5", "pfce": "10"}
NEW_BASE, OLD_BASE = "2022-23", "2011-12"
SPLICE_FROM = ("2023-24", "Q1")  # first quarter where new-base YoY exists


def _get_all(code):
    rows, page = [], 1
    while True:
        r = requests.get(f"{BASE}/api/nas/getNASData", headers=H, timeout=60,
                         params={"series": "Current", "frequency": "Quarterly",
                                 "financial_year": "2025-26",
                                 "indicator_code": code, "limit": 500,
                                 "page": page})
        r.raise_for_status()
        d = r.json()
        rows += d.get("data", [])
        if page >= d["meta_data"]["totalPages"]:
            break
        page += 1
    return rows


def _qdate(fy, q):
    """'2025-26','Q4' -> '2026-01-01' (calendar-quarter start)."""
    y = int(fy[:4])
    return {"Q1": f"{y}-04-01", "Q2": f"{y}-07-01",
            "Q3": f"{y}-10-01", "Q4": f"{y+1}-01-01"}[q]


def _yoy_within_base(rows, base):
    lvl = {(r["year"], r["quarter"]): float(r["constant_price"])
           for r in rows if r["quarter"] and r["base_year"] == base
           and r["constant_price"] is not None}
    out = {}
    for (fy, q), v in lvl.items():
        y = int(fy[:4])
        prev = (f"{y-1}-{str(y % 100).zfill(2)}", q)
        if prev in lvl:
            out[(fy, q)] = round((v / lvl[prev] - 1) * 100, 1)
    return out


def fetch():
    for sid, code in INDICATORS.items():
        rows = _get_all(code)
        new = _yoy_within_base(rows, NEW_BASE)
        old = _yoy_within_base(rows, OLD_BASE)
        merged = {}
        for k, v in old.items():
            if k < SPLICE_FROM:
                merged[k] = v
        merged.update(new)  # new base wins from 2023-24 Q1
        obs = sorted([_qdate(fy, q), v] for (fy, q), v in merged.items())
        (LIVE / f"{sid}.json").write_text(
            json.dumps({"freq": "Q", "obs": obs}))
        print(sid, len(obs), "obs; last4:", obs[-4:])


if __name__ == "__main__":
    fetch()
