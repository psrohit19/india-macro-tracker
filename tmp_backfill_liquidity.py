"""One-off backfill of data/live/liquidity.json to ~2 years of daily history.

Reuses the exact parsing from pipeline/fetchers/rbi_pr.py (F-line regex,
value = -F/1e5). Writes an incremental cache tmp_liq_cache.json so progress
survives interruption. Merge rule: existing obs ALWAYS win; only new dates
are added. Revised releases ("(Revised)" in title) win over the original
print among newly fetched data.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path("/home/claude/india-macro-tracker")
LIVE = ROOT / "data" / "live" / "liquidity.json"
CACHE = ROOT / "tmp_liq_cache.json"
LOG = ROOT / "tmp_liq_log.txt"

URL = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}

# months to walk, newest -> oldest: 2026-06 back to 2024-07 (24 months)
MONTHS_TO_DO = []
y, m = 2026, 6
for _ in range(24):
    MONTHS_TO_DO.append((y, m))
    m -= 1
    if m == 0:
        y, m = y - 1, 12

F_RE = re.compile(
    r"F\. Net liquidity injected .{0,120}?\]\s*\*?\s*"
    r"(-?[\d,]+(?:\.\d+)?)")
TITLE_RE = re.compile(
    r"Money Market Operations as on\s+(.+?)\s*(\((?:Revised|REVISED)\))?\s*$")


def log(msg):
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def month_listing(sess, year, month):
    """[(prid, title), ...] — same postback as rbi_pr._month_listing."""
    r = sess.get(URL, timeout=90)
    soup = BeautifulSoup(r.text, "lxml")
    data = {i["name"]: i.get("value", "") for i in soup.find_all("input")
            if i.get("name") and i.get("type") == "hidden"}
    data.update({"hdnYear": str(year), "hdnMonth": str(month),
                 "UsrFontCntr$btn": ""})
    r2 = sess.post(URL, data=data, timeout=120)
    out = []
    for a in BeautifulSoup(r2.text, "lxml").find_all("a", href=True):
        mm = re.search(r"prid=(\d+)", a["href"])
        if mm and a.get_text(strip=True):
            out.append((mm.group(1), a.get_text(" ", strip=True)))
    return out


def release_text(sess, prid):
    r = sess.get(f"{URL}?prid={prid}", timeout=90)
    return BeautifulSoup(r.text, "lxml").get_text(" ", strip=True)


def with_retry(fn, *a, what=""):
    try:
        return fn(*a)
    except Exception as e:
        log(f"  transient failure ({what}): {e!r} — retrying in 5s")
        time.sleep(5)
        return fn(*a)


def main():
    existing = json.loads(LIVE.read_text())
    existing_dates = {d for d, _ in existing["obs"]}
    # cache: {"done_months": ["2026-6", ...], "obs": {iso: [val, revised, prid]}}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
    else:
        cache = {"done_months": [], "obs": {}, "failures": []}

    sess = requests.Session()
    sess.headers.update(H)

    for yy, mm in MONTHS_TO_DO:
        key = f"{yy}-{mm}"
        if key in cache["done_months"]:
            continue
        try:
            listing = with_retry(month_listing, sess, yy, mm,
                                 what=f"listing {key}")
        except Exception as e:
            log(f"MONTH {key}: listing FAILED after retry: {e!r} — skipping")
            cache["failures"].append(f"listing {key}: {e!r}")
            CACHE.write_text(json.dumps(cache))
            continue
        n_mmo, n_new = 0, 0
        for prid, title in listing:
            tm = TITLE_RE.match(title)
            if not tm:
                continue
            revised = bool(tm.group(2))
            try:
                d = datetime.strptime(tm.group(1).strip(),
                                      "%B %d, %Y").date().isoformat()
            except ValueError:
                log(f"  unparseable MMO title prid={prid}: {title!r}")
                cache["failures"].append(f"title prid={prid}: {title}")
                continue
            n_mmo += 1
            if d in existing_dates:
                continue                      # existing obs always wins
            prev = cache["obs"].get(d)
            if prev is not None and (prev[1] or not revised):
                continue    # keep already-cached value unless this is Revised
            time.sleep(0.35)
            try:
                text = with_retry(release_text, sess, prid,
                                  what=f"prid={prid}")
            except Exception as e:
                log(f"  prid={prid} ({d}) fetch FAILED after retry: {e!r}")
                cache["failures"].append(f"fetch {d} prid={prid}: {e!r}")
                continue
            fm = F_RE.search(text)
            if not fm:
                log(f"  no F-line in prid={prid} ({title})")
                cache["failures"].append(f"no F-line {d} prid={prid}")
                continue
            val = round(-float(fm.group(1).replace(",", "")) / 1e5, 3)
            cache["obs"][d] = [val, revised, prid]
            n_new += 1
        cache["done_months"].append(key)
        CACHE.write_text(json.dumps(cache))
        log(f"MONTH {key}: {len(listing)} releases, {n_mmo} MMO, "
            f"{n_new} new obs (cache total {len(cache['obs'])})")

    log(f"DONE. cached obs={len(cache['obs'])}, "
        f"failures={len(cache['failures'])}")


if __name__ == "__main__":
    main()
