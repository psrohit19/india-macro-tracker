"""Scan cached listings, classify prids per series, print coverage."""
import json, re
from pathlib import Path

HERE = Path(__file__).parent
listings = sorted((HERE / "listings").glob("*.json"))
svc, walr, pl = {}, {}, {}
for f in listings:
    ym = f.stem
    for prid, title in json.loads(f.read_text()):
        t = title.strip()
        if "Trade in Services" in t:
            svc[int(prid)] = (ym, t)
        elif re.match(r"Lending and Deposit Rates of Scheduled Commercial Banks", t):
            walr[int(prid)] = (ym, t)
        elif re.match(r"Sectoral Deployment of Bank Credit", t):
            pl[int(prid)] = (ym, t)

for name, d in [("svc", svc), ("walr", walr), ("pl", pl)]:
    yrs = {}
    for prid, (ym, t) in d.items():
        yrs.setdefault(ym[:4], 0)
        yrs[ym[:4]] += 1
    print(name, len(d), "first:", min(d.items())[1] if d else None)
    print("  per-year:", dict(sorted(yrs.items())))
(HERE / "prids.json").write_text(json.dumps(
    {"svc": {k: v for k, v in sorted(svc.items())},
     "walr": {k: v for k, v in sorted(walr.items())},
     "pl": {k: v for k, v in sorted(pl.items())}}, indent=1))
print("wrote prids.json")
