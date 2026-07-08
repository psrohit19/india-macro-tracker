"""
Grid India (POSOCO) daily Power Supply Position fetcher — LIVE (via mirror).
Populates: power_gen (daily energy met, BU), peak_demand (daily max demand met, GW).

Primary source (verified UNREACHABLE from this box, Jul 2026):
  * https://report.grid-india.in/  — daily PSP PDFs. DNS/CONNECT fails through
    the agent proxy (gateway 502 on CONNECT), as do webcontrol.grid-india.in,
    grid-india.in, posoco.in, vidyutpravah.in and meritindia.in.
  * NPP (npp.gov.in/publishedReports) mirrors the CEA Daily Generation Report
    (dgr1..dgr17) but NOT the PSP: the DGR "actual generation" excludes RES
    (~4,400 MU/day vs true all-India energy met ~5,500 MU/day) and carries no
    peak-demand figure — do not use it for these two series.

Working source (used here):
  * https://robbieandrew.github.io/india/data/POSOCO_data.csv — CICERO's
    long-running machine-readable transcription of Grid India's daily PSP
    report Tables A/B (metadata: POSOCO_metadata.json on the same host).
    Columns used: "India: EnergyMet" (GWh == MU) and "India: MaximumDemand"
    (MW, max instantaneous demand met during the day). Updated daily with a
    1-2 day lag; history from Jan 2013.

Verification performed (Jul 2026):
  * Sum of daily "India: EnergyMet" for Jun 2026 = 166,464 MU = 166.46 BU —
    exactly the official June power-consumption print reported from government
    data (Business Standard, 01-Jul-2026). Max "India: MaximumDemand" for
    Jun 2026 = 264,768 MW, matching the reported 264.76 GW June peak; the
    19-May-2026 row (260,457 MW) matches the reported 260.45 GW record and
    May's 270,820 MW matches the 270.8 GW all-time high.

UNITS / CATALOG NOTE: catalog unit for power_gen is "BU" with agg="sum", but
its sample base is 156.0 — a MONTHLY total (~30 x 5.2). True daily energy met
is ~5.0-6.0 BU/day, which is what this fetcher writes (MU / 1000). The daily
"sum" rollup then reproduces the ~155-165 BU monthly level.

Writes data/live/power_gen.json and data/live/peak_demand.json:
    {"freq": "D", "obs": [["YYYY-MM-DD", value], ...]}
peak_demand only starts when the PSP "MaximumDemand" column exists (Oct 2014);
earlier evening-peak "DemandMet" values are a different definition and skipped.
"""
import csv
import io
import json
from pathlib import Path

import requests

MIRROR = "https://robbieandrew.github.io/india/data/POSOCO_data.csv"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

COL_ENERGY = "India: EnergyMet"       # GWh (= MU) per day
COL_PEAK = "India: MaximumDemand"     # MW, max demand met during the day


def _save(sid, obs):
    LIVE.mkdir(parents=True, exist_ok=True)
    obs = sorted(obs)
    (LIVE / f"{sid}.json").write_text(json.dumps({"freq": "D", "obs": obs}))
    print(f"  {sid}: {len(obs)} days, latest {obs[-1][0]} = {obs[-1][1]}")


def fetch():
    print("Grid India PSP (POSOCO mirror) pull:")
    r = requests.get(MIRROR, headers=H, timeout=120)
    r.raise_for_status()
    rows = csv.DictReader(io.StringIO(r.text))
    power, peak = [], []
    for row in rows:
        d = row["yyyymmdd"]
        iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        e = row.get(COL_ENERGY) or ""
        p = row.get(COL_PEAK) or ""
        try:
            if e.strip():
                v = float(e)
                if 1000 < v < 9000:            # MU/day sanity band
                    power.append([iso, round(v / 1000, 3)])   # -> BU/day
        except ValueError:
            pass
        try:
            if p.strip():
                v = float(p)
                if 50_000 < v < 400_000:       # MW sanity band
                    peak.append([iso, round(v / 1000, 2)])    # -> GW
        except ValueError:
            pass
    _save("power_gen", power)
    _save("peak_demand", peak)


if __name__ == "__main__":
    fetch()
