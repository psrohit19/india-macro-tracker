"""Merge MEIDB backfill (tmp_trade_raw.json) into data/live trade JSONs.

Rules: existing obs win on any overlap; new months = 2016-01..2023-12 only;
prefer MEIDB revised (prior-year cell of the following year's request) over
first print; trade_def computed in US$ mn then rounded (matches fetcher).
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
LIVE = ROOT / "data" / "live"
raw = json.loads((ROOT / "tmp_trade_raw.json").read_text())

new_mn = {}   # flow -> {iso: US$ mn}
for flow in ("exports", "imports"):
    vals = {}
    for y in range(2016, 2024):
        for m in range(1, 13):
            k = f"{y}-{m:02d}"
            rev = raw[flow]["revised"].get(k)
            fp = raw[flow]["first"].get(k)
            v = rev if rev is not None else fp
            if v is None:
                print(f"GAP {flow} {k} (revised={rev}, first={fp})")
                continue
            vals[f"{k}-01"] = v
            if rev is not None and fp is not None:
                d = rev - fp
                if abs(d) > 0.005:
                    pct = 100 * d / fp
                    if abs(pct) > 1.0:
                        print(f"  revision>1% {flow} {k}: first {fp:.2f} -> "
                              f"revised {rev:.2f} ({pct:+.2f}%)")
    new_mn[flow] = vals

summary = {}
for flow in ("exports", "imports"):
    p = LIVE / f"{flow}.json"
    doc = json.loads(p.read_text())
    existing = {d: v for d, v in doc["obs"]}
    added = 0
    for iso, mn in sorted(new_mn[flow].items()):
        if iso not in existing:
            existing[iso] = round(mn / 1000, 2)
            added += 1
    doc["obs"] = [[d, existing[d]] for d in sorted(existing)]
    p.write_text(json.dumps(doc))
    summary[flow] = doc["obs"]
    print(f"{flow}: +{added} -> {len(doc['obs'])} obs, "
          f"{doc['obs'][0][0]}..{doc['obs'][-1][0]}")

# trade_def: keep existing rows; add new months where both legs exist in raw mn
p = LIVE / "trade_def.json"
doc = json.loads(p.read_text())
existing = {d: v for d, v in doc["obs"]}
added = 0
for iso in sorted(new_mn["exports"]):
    if iso in existing or iso not in new_mn["imports"]:
        continue
    existing[iso] = round((new_mn["imports"][iso] - new_mn["exports"][iso]) / 1000, 2)
    added += 1
doc["obs"] = [[d, existing[d]] for d in sorted(existing)]
p.write_text(json.dumps(doc))
print(f"trade_def: +{added} -> {len(doc['obs'])} obs, "
      f"{doc['obs'][0][0]}..{doc['obs'][-1][0]}")

# continuity check: no missing months within each series' range
for sid in ("exports", "imports", "trade_def"):
    obs = json.loads((LIVE / f"{sid}.json").read_text())["obs"]
    dates = [d for d, _ in obs]
    y0, m0 = int(dates[0][:4]), int(dates[0][5:7])
    y1, m1 = int(dates[-1][:4]), int(dates[-1][5:7])
    want = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        want.append(f"{y}-{m:02d}-01")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    miss = sorted(set(want) - set(dates))
    print(f"{sid}: missing months in range: {miss if miss else 'none'}")

# spot values for verification
for sid in ("exports", "imports"):
    obs = dict(json.loads((LIVE / f"{sid}.json").read_text())["obs"])
    for k in ("2016-11-01", "2017-11-01", "2017-12-01", "2018-12-01",
              "2022-11-01", "2023-03-01", "2024-01-01"):
        print(f"  {sid} {k}: {obs.get(k)}")
