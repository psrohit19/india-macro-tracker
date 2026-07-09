"""Backfill 2016-01..2023-12 merchandise exports/imports from MEIDB.

Uses tradestat._month_pair. For each flow, requests years 2017..2024 x months
1..12. Each request returns (year-1 REVISED, year first-print). We keep both:
  revised[(y-1,m)]  <- prev cell   (preferred)
  first[(y,m)]      <- cur cell    (fallback + cross-check)
Raw results dumped to tmp_trade_raw.json for merge/verification in a second step.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pipeline" / "fetchers"))
from tradestat import _month_pair, FLOWS  # noqa: E402

import requests  # noqa: E402

OUT = Path(__file__).parent / "tmp_trade_raw.json"

raw = {"exports": {"revised": {}, "first": {}}, "imports": {"revised": {}, "first": {}}}
if OUT.exists():
    raw = json.loads(OUT.read_text())

for flow in FLOWS:
    s = requests.Session()
    for y in range(2017, 2025):
        for m in range(1, 13):
            k_prev = f"{y-1}-{m:02d}"
            k_cur = f"{y}-{m:02d}"
            if k_prev in raw[flow]["revised"] and k_cur in raw[flow]["first"]:
                continue  # resume support
            try:
                prev, cur = _month_pair(s, flow, m, y)
            except Exception as e:
                print(f"FAIL {flow} {m}/{y}: {e}", flush=True)
                raw[flow]["first"].setdefault(k_cur, None)
                raw[flow]["revised"].setdefault(k_prev, None)
                s = requests.Session()
                time.sleep(5)
                continue
            raw[flow]["revised"][k_prev] = prev
            raw[flow]["first"][k_cur] = cur
            print(f"{flow} req {m:02d}/{y}: prev({k_prev})={prev} cur({k_cur})={cur}",
                  flush=True)
            OUT.write_text(json.dumps(raw))
            time.sleep(1.0)
OUT.write_text(json.dumps(raw))
print("DONE", flush=True)
