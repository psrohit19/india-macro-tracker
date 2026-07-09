"""Merge tmp_liq_cache.json into data/live/liquidity.json.
Existing obs win on overlap; new dates added; sort ascending; compact dump.
"""
import json
from pathlib import Path

ROOT = Path("/home/claude/india-macro-tracker")
LIVE = ROOT / "data" / "live" / "liquidity.json"
CACHE = ROOT / "tmp_liq_cache.json"

live = json.loads(LIVE.read_text())
cache = json.loads(CACHE.read_text())

merged = {d: v for d, [v, _rev, _prid] in cache["obs"].items()}
n_new_candidates = len(merged)
for d, v in live["obs"]:          # existing wins
    merged[d] = v

out = dict(live)                  # preserve all top-level keys
out["obs"] = [[d, merged[d]] for d in sorted(merged)]

LIVE.write_text(json.dumps(out))
print(f"existing={len(live['obs'])} cached_new={n_new_candidates} "
      f"merged_total={len(out['obs'])}")
print(f"range {out['obs'][0][0]} .. {out['obs'][-1][0]}")
print(f"failures logged: {len(cache.get('failures', []))}")
for f in cache.get("failures", []):
    print("  FAIL:", f)
