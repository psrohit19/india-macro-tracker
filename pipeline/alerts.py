"""
Threshold alerts — evaluated after every refresh.

Rules fire on the freshly computed data.json. Delivery: Slack incoming-webhook
(set SLACK_WEBHOOK_URL) and/or SMTP email (set ALERT_EMAIL_* vars). In GitHub
Actions, add the webhook as a secret and call this from refresh.py.

Rule grammar (kept deliberately simple — a rule is a dict):
  series   catalog id
  when     "above" | "below" | "z_above" | "z_below" | "streak_neg" | "changed"
  value    threshold (level, z-score, or streak length in periods)
  note     human context appended to the alert
"""
import json
import os
import urllib.request
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "data.json"

RULES = [
    dict(series="cpi", when="above", value=5.0,
         note="CPI above 5% — outside the RBI comfort band; rate-path assumptions need review."),
    dict(series="cpi", when="below", value=2.0,
         note="CPI below 2% — undershooting the band; easing runway extends."),
    dict(series="fii", when="streak_neg", value=7,
         note="FII selling streak ≥ 7 sessions — risk-off regime signal."),
    dict(series="gnpa", when="changed", value=0,
         note="New FSR print — refresh credit-cycle view."),
    dict(series="repo", when="changed", value=0,
         note="MPC moved the policy rate."),
    dict(series="brent", when="above", value=90.0,
         note="Brent above $90 — CAD/inflation stress scenario activates."),
    dict(series="vix", when="above", value=20.0,
         note="India VIX above 20 — IPO/exit windows typically shut."),
    dict(series="cmp_fci", when="below", value=-1.0,
         note="Financial conditions >1σ tighter than norm — financing risk for live deals."),
    dict(series="cmp_rural", when="below", value=-1.0,
         note="Rural demand >1σ below norm — check rural-exposed portfolio names."),
]


def evaluate():
    data = json.loads(DATA.read_text())
    by_id = {s["id"]: s for s in data["series"]}
    fired = []
    for r in RULES:
        s = by_id.get(r["series"])
        if not s:
            continue
        v = s["latest"]["raw"]
        hist = s["history"]["values"]
        hit = False
        if r["when"] == "above":
            hit = v > r["value"]
        elif r["when"] == "below":
            hit = v < r["value"]
        elif r["when"] == "z_above":
            hit = s.get("z12", 0) > r["value"]
        elif r["when"] == "z_below":
            hit = s.get("z12", 0) < r["value"]
        elif r["when"] == "streak_neg":
            n = int(r["value"])
            hit = len(hist) >= n and all(x < 0 for x in hist[-n:])
        elif r["when"] == "changed":
            hit = len(hist) >= 2 and hist[-1] != hist[-2]
        if hit:
            unit = "" if s["unit"] == "σ" else " " + s["unit"]
            fired.append(f"⚠ {s['name']}: {s['latest']['value']}{unit} "
                         f"({s['latest']['period']}) — {r['note']}")
    return fired


def deliver(messages):
    if not messages:
        return
    text = "*India Macro Tracker alerts*\n" + "\n".join(messages)
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    if hook:
        req = urllib.request.Request(
            hook, data=json.dumps({"text": text}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15)
    else:
        print(text)


if __name__ == "__main__":
    deliver(evaluate())
