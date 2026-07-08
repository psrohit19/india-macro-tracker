"""
Data + analytics layer for the India Macro Tracker.

In production, each series' history comes from its fetcher (pipeline/fetchers/).
Until those are wired to live sources, this module generates realistic SAMPLE
history so the dashboard, rollups, composites and comparison math are fully
exercised. Everything analytic below (rollups, z-scores, composites, bullets)
is production logic — only gen_history() is sample scaffolding.

Output: data/data.json
  series[]  — one record per catalog series AND per composite index:
      id, name, category, unit, freq, source, url, access, release, info,
      up_is_good, kind, headline, seasonal, revision_prone,
      latest / prev / yoy / avg12 / avg_lt, spark, spark_labels,
      rows[]    — display-ready comparison rows (ordered; seasonal-aware)
      history   — {dates: [...], values: [...]} full native history (drill-down/CSV)
  bullets[]   — auto-generated "What changed" narrative (top 12-period z-moves)

Comparison framework (per tracker spec):
  1. vs most recent previous period
  2. vs same period last year
  3. vs trailing 12-period average (native frequency)
  4. vs trailing 10-year average — EXCEPT structurally trending series
     (lt_mode == "trend"), where the long-term row becomes
     "YoY growth vs 3-yr trend CAGR" so the row stays informative.
  Seasonal monthly/quarterly series lead with YoY; MoM is de-emphasized.
"""
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from catalog import SERIES, CATEGORIES, COMPOSITES

TODAY = date.today()
LT_WINDOW = {"D": 2500, "W": 520, "F": 260, "M": 120, "B": 60, "Q": 40, "H": 20}
PPY = {"D": 250, "W": 52, "F": 26, "M": 12, "B": 6, "Q": 4, "H": 2}  # periods/yr
OUT = Path(__file__).parent.parent / "data" / "data.json"
LIVE = Path(__file__).parent.parent / "data" / "live"


def live_obs(sid):
    """Return (obs, seeded) if live data exists for sid; else None.
    obs = [(iso, value), ...]; seeded=True means hand-verified transcription
    from the official source rather than an automated fetcher."""
    f = LIVE / f"{sid}.json"
    if not f.exists():
        return None
    payload = json.loads(f.read_text())
    obs = sorted(payload["obs"])
    if len(obs) < 14:                     # need enough for YoY + 12-period avg
        return None
    return obs, bool(payload.get("seed"))


def iso_label(freq, iso):
    d = date.fromisoformat(iso)
    if freq == "D":
        return d.strftime("%d %b %y")
    if freq in ("W",):
        return "wk to " + d.strftime("%d %b %y")
    if freq in ("F",):
        return "fn to " + d.strftime("%d %b %y")
    if freq in ("M", "B", "H"):
        return d.strftime("%b %y")
    if freq == "Q":
        q = (d.month - 1) // 3 + 1
        fy = d.year + 1 if q >= 2 else d.year
        return f"{ {2:'Q1',3:'Q2',4:'Q3',1:'Q4'}[q] } FY{str(fy)[2:]}".replace(" ", "")
    return iso


def n_periods(freq):
    return LT_WINDOW[freq] + 3


# ---------------------------------------------------------------- periods ---
def period_labels(freq, n):
    """(label, iso_date) for the last n periods, oldest first."""
    out = []
    if freq == "D":
        d = TODAY - timedelta(days=1)
        while len(out) < n:
            if d.weekday() < 5:
                out.append((d.strftime("%d %b %y"), d.isoformat()))
            d -= timedelta(days=1)
        out.reverse()
    elif freq == "W":
        d = TODAY - timedelta(days=(TODAY.weekday() - 4) % 7 or 7)
        for _ in range(n):
            out.append(("wk to " + d.strftime("%d %b %y"), d.isoformat()))
            d -= timedelta(days=7)
        out.reverse()
    elif freq == "F":
        d = TODAY - timedelta(days=11)
        for _ in range(n):
            out.append(("fn to " + d.strftime("%d %b %y"), d.isoformat()))
            d -= timedelta(days=14)
        out.reverse()
    elif freq in ("M", "B"):
        step = 1 if freq == "M" else 2
        y, m = TODAY.year, TODAY.month - 1 or 12
        if TODAY.month == 1:
            y -= 1
        if freq == "B" and m % 2 != 0:       # align to MPC even months
            m -= 1
            if m == 0:
                m, y = 12, y - 1
        for _ in range(n):
            out.append((date(y, m, 1).strftime("%b %y"), date(y, m, 1).isoformat()))
            m -= step
            if m <= 0:
                m, y = m + 12, y - 1
        out.reverse()
    elif freq == "Q":
        y, q = 2026, 1
        for _ in range(n):
            fy = y + 1 if q >= 2 else y
            fq = {2: "Q1", 3: "Q2", 4: "Q3", 1: "Q4"}[q]
            out.append((f"{fq} FY{str(fy)[2:]}", date(y, 3 * q - 2, 1).isoformat()))
            q -= 1
            if q == 0:
                q, y = 4, y - 1
        out.reverse()
    elif freq == "H":
        y, m = (TODAY.year, 3) if TODAY.month < 10 else (TODAY.year, 9)
        for _ in range(n):
            out.append((date(y, m, 1).strftime("%b %y"), date(y, m, 1).isoformat()))
            m -= 6
            if m <= 0:
                m, y = m + 12, y - 1
        out.reverse()
    return out


def yoy_offset(freq):
    return {"D": 250, "W": 52, "F": 26, "M": 12, "B": 6, "Q": 4, "H": 2}[freq]


# ----------------------------------------------------------------- values ---
def gen_history(s, n):
    """Seeded random walk around the series' base. SAMPLE data only."""
    rng = random.Random(s["id"])
    vals = []
    v = s["base"]
    trend = s.get("trend", 0.0) / max(n, 1)
    for i in range(n):
        if s["kind"] == "flow":
            v = s["base"] + rng.gauss(0, s["vol"])
        else:
            v = v + rng.gauss(0, s["vol"] * 0.6) + trend
            v += (s["base"] - v) * 0.15
        vals.append(v)
    if s["category"] in ("Consumption & Demand", "Energy & Infrastructure") and s["freq"] == "M":
        vals = [x * (1 + 0.05 * math.sin((i / 12) * 2 * math.pi)) for i, x in enumerate(vals)]
    return vals


# ------------------------------------------------------------- formatting ---
def fmt_val(v, unit):
    if unit == "σ":
        return f"{v:+.2f}σ"
    if unit == "bps":
        return f"{v:,.0f}"
    if unit == "x":
        return f"{v:,.1f}x"
    if unit == "index" and abs(v) >= 1000:
        return f"{v:,.0f}"
    if unit == "₹ cr":
        return f"{v:,.0f}"
    if unit in ("crore", "₹ lakh cr", "lakh units", "cr households"):
        return f"{v:,.2f}"
    if unit in ("US$ bn", "US$/bbl", "MMT", "BU", "GW", "MT", "'000 units",
                "lakh", "lakh MT", "lakh ha", "tonnes", "mn"):
        return f"{v:,.1f}"
    if unit in ("%", "% YoY", "index", "% of LPA", "% of capacity", "% of BE", "₹"):
        return f"{v:,.1f}" if unit != "%" or v >= 10 else f"{v:,.2f}"
    return f"{v:,.2f}"


def delta(latest, ref, kind, unit):
    if ref is None or (kind != "flow" and ref == 0):
        return None
    d = latest - ref
    if unit == "σ":
        return dict(text=f"{d:+.2f}σ", dir=(0 if abs(d) < 0.01 else (1 if d > 0 else -1)))
    if unit == "bps":
        return dict(text=f"{d:+.0f} bps", dir=(0 if abs(d) < 0.5 else (1 if d > 0 else -1)))
    if kind == "rate":
        txt = f"{d:+.2f} pp" if "%" in unit and unit != "%" else f"{d * 100:+.0f} bps"
        if unit not in ("%",) and "%" in unit:
            txt = f"{d:+.2f} pp"
        neutral = abs(d) < 0.005
        return dict(text=txt, dir=(0 if neutral else (1 if d > 0 else -1)))
    if kind == "flow":
        return dict(text=f"{d:+,.0f}",
                    dir=(0 if (ref and abs(d) < abs(ref) * 0.02) else (1 if d > 0 else -1)))
    pct = d / abs(ref) * 100
    return dict(text=f"{pct:+.1f}%", dir=(0 if abs(pct) < 0.05 else (1 if pct > 0 else -1)))


def round_hist(v):
    return round(v, 3) if abs(v) < 1000 else round(v, 1)


# --------------------------------------------------- per-series analytics ---
def build_record(s, vals, labels):
    freq, unit, kind = s["freq"], s["unit"], s["kind"]
    latest_v, latest_l = vals[-1], labels[-1][0]
    prev_v, prev_l = vals[-2], labels[-2][0]

    off = yoy_offset(freq)
    if len(vals) > off:
        yoy_v, yoy_l, yoy_key = vals[-1 - off], labels[-1 - off][0], "vs LY"
    else:  # history shorter than a year — compare vs oldest, labeled honestly
        yoy_v, yoy_l, yoy_key = vals[0], labels[0][0], "vs start"

    w12 = vals[-13:-1]
    avg12 = sum(w12) / len(w12)
    ltn = min(LT_WINDOW.get(freq, 120), len(vals) - 1)
    ltw = vals[-(ltn + 1):-1]
    avg_lt = sum(ltw) / len(ltw)

    freq_word = {"D": "day", "W": "wk", "F": "fn", "M": "mo",
                 "B": "round", "Q": "qtr", "H": "half-yr"}[freq]

    # long-term row: 10-yr average, or growth-vs-trend for trending series
    if s.get("lt_mode") == "trend" and yoy_v > 0 and latest_v > 0:
        ppy = PPY[freq]
        yoyg = (latest_v / yoy_v - 1) * 100
        i3 = -1 - 3 * ppy
        base3 = vals[i3] if len(vals) >= 3 * ppy + 1 else vals[0]
        cagr = ((latest_v / base3) ** (1 / 3) - 1) * 100 if base3 > 0 else 0.0
        gap = yoyg - cagr
        lt_row = ["growth vs 3-yr trend", f"{cagr:+.1f}%/yr",
                  dict(text=f"{gap:+.1f} pp", dir=(0 if abs(gap) < 0.05 else (1 if gap > 0 else -1)))]
    else:
        lt_key = "vs 10-yr avg" if ltn >= LT_WINDOW.get(freq, 120) else "vs full-history avg"
        lt_row = [lt_key, fmt_val(avg_lt, unit), delta(latest_v, avg_lt, kind, unit)]

    prev_row = [f"vs prev ({prev_l})", fmt_val(prev_v, unit), delta(latest_v, prev_v, kind, unit)]
    yoy_row = [f"{yoy_key} ({yoy_l})", fmt_val(yoy_v, unit), delta(latest_v, yoy_v, kind, unit)]
    avg_row = [f"vs 12-{freq_word} avg", fmt_val(avg12, unit), delta(latest_v, avg12, kind, unit)]

    # seasonal series lead with YoY; MoM is demoted (rendered muted by the page)
    if s.get("seasonal"):
        rows = [yoy_row, prev_row + ["muted"], avg_row, lt_row]
    else:
        rows = [prev_row, yoy_row, avg_row, lt_row]
    rows = [r + [""] if len(r) == 3 else r for r in rows]

    # z vs 12-period norm (for bullets & pulse board)
    mean12 = avg12
    var12 = sum((x - mean12) ** 2 for x in w12) / len(w12)
    std12 = var12 ** 0.5
    z12 = (latest_v - mean12) / std12 if std12 > 1e-9 else 0.0

    rec = {k: s[k] for k in ("id", "name", "category", "unit", "freq", "source",
                             "url", "info", "access", "release", "up_is_good",
                             "kind", "headline", "seasonal", "revision_prone",
                             "display")}
    rec.update(
        latest=dict(period=latest_l, value=fmt_val(latest_v, unit), raw=round(latest_v, 4)),
        prev=dict(period=prev_l, value=fmt_val(prev_v, unit)),
        yoy=dict(period=yoy_l, value=fmt_val(yoy_v, unit)),
        avg12=fmt_val(avg12, unit),
        avg_lt=fmt_val(avg_lt, unit),
        rows=rows,
        z12=round(z12, 2),
        spark=[round(v, 3) for v in vals[-12:]],
        spark_labels=[l.replace("wk to ", "").replace("fn to ", "")[:7].strip()
                      for l, _ in labels[-12:]],
        history=dict(dates=[iso for _, iso in labels],
                     values=[round_hist(v) for v in vals]),
    )
    return rec


# -------------------------------------------------------------- composites ---
def monthlyize(vals, freq, n=120):
    """Approximate a monthly grid of the last n months from a native series.
    Production uses the proper monthly rollup table; strides are fine for sample."""
    if freq in ("M",):
        src = vals
        pick = lambda k: src[-1 - k] if k < len(src) else src[0]
    elif freq in ("Q", "B", "H"):
        mpp = {"Q": 3, "B": 2, "H": 6}[freq]
        pick = lambda k: vals[-1 - k // mpp] if k // mpp < len(vals) else vals[0]
    else:
        ppm = {"D": 21, "W": 4, "F": 2}[freq]
        pick = lambda k: vals[-1 - k * ppm] if k * ppm < len(vals) else vals[0]
    return [pick(k) for k in range(n)][::-1]      # oldest first


def build_composites(hist_by_id):
    out = []
    mlabels = period_labels("M", 123)[-120:]
    for c in COMPOSITES:
        zs = []
        for sid, sign in c["components"]:
            s = next(x for x in SERIES if x["id"] == sid)
            grid = monthlyize(hist_by_id[sid], s["freq"])
            mean = sum(grid) / len(grid)
            std = (sum((x - mean) ** 2 for x in grid) / len(grid)) ** 0.5 or 1.0
            zs.append([sign * (x - mean) / std for x in grid])
        comp = [sum(col) / len(col) for col in zip(*zs)]
        comps = dict(
            id=c["id"], name=c["name"], category="Composite Signals",
            unit="σ", freq="M", agg="last", up_is_good=True, kind="level",
            base=0, vol=0, source="Derived — z-score composite",
            url=None, access="derived", release="Recomputed each refresh",
            info=c["info"], headline=False, seasonal=False,
            lt_mode="avg", revision_prone=False, display="std",
        )
        labels = [(l, iso) for l, iso in mlabels]
        rec = build_record(comps, comp, labels)
        rec["components"] = [sid for sid, _ in c["components"]]
        rec["sample"] = True
        out.append(rec)
    return out


# ---------------------------------------------------------------- bullets ---
def build_bullets(records):
    scored = []
    for r in records:
        if r["category"] in ("Composite Signals",) or abs(r["z12"]) < 0.1:
            continue
        if r.get("sample"):          # never narrate dummy data
            continue
        scored.append(r)
    scored.sort(key=lambda r: -abs(r["z12"]))
    bullets, seen_cat = [], set()
    for r in scored:
        if len(bullets) >= 5:
            break
        if r["category"] in seen_cat and len(scored) - len(bullets) > 5:
            continue
        seen_cat.add(r["category"])
        z = r["z12"]
        good = None if r["up_is_good"] is None else ((z > 0) == r["up_is_good"])
        word = "above" if z > 0 else "below"
        bullets.append(dict(
            text=f"{r['name']} at {r['latest']['value']} {r['unit']} — "
                 f"{abs(z):.1f}σ {word} its 12-period norm ({r['latest']['period']})",
            sentiment=("neut" if good is None else ("good" if good else "bad")),
            id=r["id"]))
    return bullets


# ------------------------------------------------------------------ build ---
def derive_monthly_sum(vals, labels):
    """Bucket a daily flow series into calendar-month sums (latest = MTD)."""
    buckets = {}
    for (_, iso), v in zip(labels, vals):
        buckets.setdefault(iso[:7], 0.0)
        buckets[iso[:7]] += v
    keys = sorted(buckets)
    mlabels = [(iso_label("M", k + "-01"), k + "-01") for k in keys]
    return [buckets[k] for k in keys], mlabels


def derive_fytd_sum(vals, labels):
    """Cumulative fiscal-year-to-date sum of a daily flow, one obs per month.
    Resets every 1 April; latest month = FYTD through the latest print."""
    mvals, mlabels = derive_monthly_sum(vals, labels)
    out, running, fy = [], 0.0, None
    for v, (_, iso) in zip(mvals, mlabels):
        y, m = int(iso[:4]), int(iso[5:7])
        this_fy = y if m >= 4 else y - 1
        if this_fy != fy:
            fy, running = this_fy, 0.0
        running += v
        out.append(running)
    return out, mlabels


def build():
    records, hist_by_id, labels_by_id, live_ids = [], {}, {}, set()
    derived = [s for s in SERIES if s.get("derive_sum_from") or s.get("derive_fytd_from")]
    seeded_ids = set()
    for s in SERIES:
        if s.get("derive_sum_from") or s.get("derive_fytd_from"):
            continue
        hit = live_obs(s["id"])
        if hit:
            obs, seeded = hit
            labels = [(iso_label(s["freq"], iso), iso) for iso, _ in obs]
            vals = [v for _, v in obs]
            live_ids.add(s["id"])
            if seeded:
                seeded_ids.add(s["id"])
        else:
            n = n_periods(s["freq"])
            labels = period_labels(s["freq"], n)
            vals = gen_history(s, n)
        hist_by_id[s["id"]], labels_by_id[s["id"]] = vals, labels
        rec = build_record(s, vals, labels)
        rec["sample"] = s["id"] not in live_ids
        rec["seeded"] = s["id"] in seeded_ids
        records.append(rec)

    for s in derived:
        src = s.get("derive_sum_from") or s.get("derive_fytd_from")
        fn = derive_monthly_sum if s.get("derive_sum_from") else derive_fytd_sum
        vals, labels = fn(hist_by_id[src], labels_by_id[src])
        rec = build_record(s, vals, labels)
        rec["sample"] = src not in live_ids
        rec["seeded"] = src in seeded_ids
        # insert after its source (or an explicit anchor) for grid adjacency
        anchor = s.get("insert_after", src)
        idx = next((i for i, r in enumerate(records) if r["id"] == anchor), len(records) - 1)
        records.insert(idx + 1, rec)

    composites = build_composites(hist_by_id)
    payload = dict(
        as_of=TODAY.isoformat(),
        generated="sample-v2",
        categories=CATEGORIES,
        series=composites + records,
        bullets=build_bullets(records),
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    kb = OUT.stat().st_size // 1024
    print(f"wrote {OUT} — {len(records)} series + {len(composites)} composites ({kb} KB)")


if __name__ == "__main__":
    build()
