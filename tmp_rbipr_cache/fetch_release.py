"""Fetch and cache one release's HTML: python3 fetch_release.py PRID [PRID...]"""
import sys, time
from pathlib import Path
import requests

URL = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
CACHE = Path(__file__).parent / "releases"

s = requests.Session(); s.headers.update(H)
for prid in sys.argv[1:]:
    f = CACHE / f"{prid}.html"
    if f.exists() and f.stat().st_size > 1000:
        print(prid, "cached"); continue
    for t in range(4):
        try:
            r = s.get(URL, params={"prid": prid}, timeout=90)
            r.raise_for_status()
            f.write_text(r.text)
            print(prid, len(r.text), flush=True)
            break
        except Exception as e:
            if t == 3: print(prid, "FAILED", e, flush=True)
            else: time.sleep(4 * (t + 1))
    time.sleep(0.5)
