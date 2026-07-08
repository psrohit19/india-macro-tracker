"""
FRED fetcher — Global Context block: brent, dxy, ust10y, fedfunds, us_cpi.

Uses the keyless CSV endpoint (no API key required):
    https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}

NOTE: fred.stlouisfed.org is blocked from some sandboxed build environments
(times out). It works from normal cloud/on-prem egress — no code change needed.

Writes data/live/{id}.json in the standard {"freq": ..., "obs": [[iso, v], ...]}
shape consumed by generate_data.py.
"""
import csv
import io
import json
import time
from pathlib import Path

import requests

LIVE = Path(__file__).parent.parent.parent / "data" / "live"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}

# tracker id -> (FRED series, native freq, transform)
MAP = {
    "brent":    ("DCOILBRENTEU", "D", None),
    "dxy":      ("DTWEXBGS",     "D", None),
    "ust10y":   ("DGS10",        "D", None),
    "fedfunds": ("DFEDTARU",     "M", "month_end"),   # daily target -> month-end
    "us_cpi":   ("CPIAUCSL",     "M", "yoy"),         # index -> % YoY
}
SERIES_IDS = list(MAP)


def _csv(series):
    r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}",
                     timeout=60, headers=H)
    r.raise_for_status()
    out = []
    for row in csv.DictReader(io.StringIO(r.text)):
        d, v = row["observation_date"], row[series]
        if v not in (".", "", None):
            out.append((d, float(v)))
    return out


def fetch():
    LIVE.mkdir(parents=True, exist_ok=True)
    for sid, (fred_id, freq, transform) in MAP.items():
        obs = _csv(fred_id)
        time.sleep(0.5)
        if transform == "month_end":
            monthly = {}
            for d, v in obs:                      # last obs per month wins
                monthly[d[:7]] = v
            obs = [(k + "-01", v) for k, v in sorted(monthly.items())]
        elif transform == "yoy":
            idx = dict(obs)
            obs = []
            for d, v in sorted(idx.items()):
                prev = idx.get(f"{int(d[:4]) - 1}{d[4:]}")
                if prev:
                    obs.append((d, round((v / prev - 1) * 100, 2)))
        obs = obs[-2600:]                          # ~10y of daily
        (LIVE / f"{sid}.json").write_text(json.dumps({"freq": freq, "obs": obs}))
        print(f"  {sid}: {len(obs)} obs, latest {obs[-1][0]} = {obs[-1][1]}")


if __name__ == "__main__":
    fetch()
