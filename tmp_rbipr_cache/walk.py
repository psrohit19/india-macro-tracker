"""Cached walker for the RBI press-release month archive.
Usage: python3 walk.py Y1-M1 Y2-M2   (inclusive range, ascending)
Caches each month listing as listings/YYYY-MM.json = [[prid, title], ...]
Filters nothing — full listing cached; series filtering happens later.
"""
import json, re, sys, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
CACHE = Path(__file__).parent / "listings"

def month_listing(sess, year, month, tries=4):
    for t in range(tries):
        try:
            r = sess.get(URL, timeout=90)
            soup = BeautifulSoup(r.text, "lxml")
            data = {i["name"]: i.get("value", "") for i in soup.find_all("input")
                    if i.get("name") and i.get("type") == "hidden"}
            data.update({"hdnYear": str(year), "hdnMonth": str(month),
                         "UsrFontCntr$btn": ""})
            r2 = sess.post(URL, data=data, timeout=120)
            r2.raise_for_status()
            out = []
            for a in BeautifulSoup(r2.text, "lxml").find_all("a", href=True):
                m = re.search(r"prid=(\d+)", a["href"])
                if m and a.get_text(strip=True):
                    out.append((m.group(1), a.get_text(" ", strip=True)))
            return out
        except Exception as e:
            if t == tries - 1:
                raise
            time.sleep(4 * (t + 1))

def main():
    y1, m1 = map(int, sys.argv[1].split("-"))
    y2, m2 = map(int, sys.argv[2].split("-"))
    sess = requests.Session(); sess.headers.update(H)
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        f = CACHE / f"{y}-{m:02d}.json"
        if not f.exists() or f.stat().st_size < 10:
            try:
                out = month_listing(sess, y, m)
                f.write_text(json.dumps(out))
                print(f"{y}-{m:02d}: {len(out)} releases", flush=True)
            except Exception as e:
                print(f"{y}-{m:02d}: FAILED {e}", flush=True)
            time.sleep(0.6)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    print("DONE", flush=True)

main()
