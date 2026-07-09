"""Merge parsed backfill into data/live JSONs. Existing obs ALWAYS win.
svc: US$ mn -> US$ bn 2dp. walr: % 2dp (xlsx era + narrative era).
pl: % YoY 1dp.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
LIVE = HERE.parent / "data" / "live"

def merge(sid, new_obs):
    f = LIVE / f"{sid}.json"
    doc = json.loads(f.read_text())
    existing = {d: v for d, v in doc["obs"]}
    added = {d: v for d, v in new_obs.items() if d not in existing}
    combined = {**added, **existing}
    doc["obs"] = [[d, v] for d, v in sorted(combined.items())]
    f.write_text(json.dumps(doc))
    print(f"{sid}: existing {len(existing)}, new added {len(added)}, "
          f"total {len(combined)}, range {doc['obs'][0][0]}..{doc['obs'][-1][0]}")
    return added

svc_mn = json.load(open(HERE / "parsed_svc.json"))
svc = {d: round(v / 1000, 2) for d, v in svc_mn.items()}
merge("svc_exports", svc)

walr_x = json.load(open(HERE / "walr_xlsx_53943.json"))   # 2014-09..2022-05
walr_n = json.load(open(HERE / "parsed_walr.json"))       # 2022-05.. narrative
walr = {**walr_x, **walr_n}                               # narrative wins on 2022-05
walr = {d: round(v, 2) for d, v in walr.items()}
merge("walr", walr)

pl = {d: round(v, 1) for d, v in json.load(open(HERE / "parsed_pl.json")).items()}
merge("personal_loans", pl)
