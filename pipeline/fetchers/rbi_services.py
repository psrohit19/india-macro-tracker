"""
RBI "Monthly Data on India's International Trade in Services" fetcher — LIVE.
Populates: svc_exports (services export receipts, US$ bn, monthly).

Verified behaviour (Jul 2026):

  * Discovery, two complementary routes:
      1. https://www.rbi.org.in/Scripts/Pr_DataRelease.aspx?SectionID=352
         &DateFilter=Year — the "Data Releases" section for services trade;
         plain HTML anchors to BS_PressReleaseDisplay.aspx?prid=NNNNN. Only
         carries the LATEST ~10 releases (DateFilter=All returns the same).
      2. The press-release month archive: BS_PressReleaseDisplay.aspx is an
         ASP.NET page whose year/month tree does GetYearMonth(y, m) ->
         hidden fields + postback. Replicate with: GET the page, lift
         __VIEWSTATE/__VIEWSTATEGENERATOR/__EVENTVALIDATION, POST them back
         with hdnYear=<y>, hdnMonth=<m>, UsrFontCntr$btn=''. The response
         lists that month's releases; filter titles on "Trade in Services".
         Data month M is released ~45 days later, so it appears in the
         archive listing of calendar month M+1 (occasionally M+2).
  * Each release contains one table: rows "<Month> – <Year>", then
    Receipts (Exports), (growth %), Payments (Imports), (growth %), in
    US$ million. The window is quarter-anchored and rolls: e.g. the
    Nov-2025 release shows Jul–Nov 2025; the Dec-2025 release drops back to
    Oct–Dec; the May-2026 release shows Jan–May 2026. Numbers for the same
    data month are REVISED across releases (pro-rata to quarterly BoP), so
    releases are parsed in ascending prid order and later prints win.
  * Monthly values are provisional until reconciled with the quarterly BoP
    — meaningful revisions are normal (documented in catalog info).
  * The Commerce/PIB monthly trade release also quotes a services number,
    but for the newest month it is a Commerce Ministry ESTIMATE ahead of
    RBI data (e.g. PIB estimated May-2026 services exports at US$36.76bn;
    RBI's actual May-2026 print is US$33.36bn). This fetcher uses RBI only.

Writes data/live/svc_exports.json:
  {"freq": "M", "obs": [["YYYY-MM-01", value], ...]}   # US$ bn, 2dp
"""
import json
import re
import time
from datetime import date
from html import unescape
from pathlib import Path

import requests

RBI = "https://www.rbi.org.in/Scripts"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
START = (2024, 8)   # earliest archive listing walked (data from ~Jun 2024)
TITLE = "Trade in Services"


def _get(s, url, tries=3, **kw):
    for i in range(tries):
        try:
            r = s.get(url, timeout=60, headers=H, **kw)
            r.raise_for_status()
            return r.text
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _archive_listing(s, year, month, tries=3):
    """Replicate the year/month tree postback; return that month's HTML."""
    for i in range(tries):
        try:
            h = _get(s, f"{RBI}/BS_PressReleaseDisplay.aspx")
            def hid(n):
                m = re.search(r'name="%s"[^>]*value="([^"]*)"' % n, h)
                return m.group(1) if m else ""
            r = s.post(f"{RBI}/BS_PressReleaseDisplay.aspx", timeout=90,
                       headers=H, data={
                           "__VIEWSTATE": hid("__VIEWSTATE"),
                           "__VIEWSTATEGENERATOR": hid("__VIEWSTATEGENERATOR"),
                           "__EVENTVALIDATION": hid("__EVENTVALIDATION"),
                           "__EVENTTARGET": "", "__EVENTARGUMENT": "",
                           "hdnYear": str(year), "hdnMonth": str(month),
                           "UsrFontCntr$btn": ""})
            r.raise_for_status()
            return r.text
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _prids_in(html):
    out = {}
    for m in re.finditer(r'<a[^>]*prid=(\d+)[^>]*>(.*?)</a>', html,
                         re.S | re.I):
        t = re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()
        if TITLE in t:
            out[int(m.group(1))] = t
    return out


def _parse_release(html):
    """-> {iso_date: receipts_us$mn} from the release's month table."""
    text = unescape(re.sub(r"<[^>]+>", "\n", re.sub(
        r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)))
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    obs, i = {}, 0
    while i < len(lines):
        g = re.fullmatch(r"(%s)\s*[–-]\s*(\d{4})" % "|".join(MONTHS),
                         lines[i])
        if g:
            for j in range(i + 1, min(i + 4, len(lines))):
                if re.fullmatch(r"[\d,]+", lines[j]):     # receipts cell
                    iso = (f"{g.group(2)}-"
                           f"{MONTHS.index(g.group(1)) + 1:02d}-01")
                    obs[iso] = float(lines[j].replace(",", ""))
                    break
        i += 1
    return obs


def fetch():
    print("RBI services-trade pull:")
    s = requests.Session()
    prids = {}
    # 1) walk month archive listings START -> now
    today = date.today()
    y, m = START
    while (y, m) <= (today.year, today.month):
        try:
            prids.update(_prids_in(_archive_listing(s, y, m)))
        except Exception as e:
            print(f"  archive {y}-{m:02d} failed: {e}")
        time.sleep(0.5)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    # 2) the data-release section (catches anything the walk missed)
    try:
        prids.update(_prids_in(_get(
            s, f"{RBI}/Pr_DataRelease.aspx",
            params={"SectionID": 352, "DateFilter": "Year"})))
    except Exception as e:
        print(f"  Pr_DataRelease listing failed: {e}")
    print(f"  {len(prids)} releases found")
    # 3) parse ascending so later releases' revised prints win
    obs = {}
    for prid in sorted(prids):
        try:
            got = _parse_release(_get(
                s, f"{RBI}/BS_PressReleaseDisplay.aspx",
                params={"prid": prid}))
            obs.update(got)
            print(f"  prid {prid}: {len(got)} months "
                  f"({prids[prid][-14:]})")
        except Exception as e:
            print(f"  prid {prid} failed: {e}")
        time.sleep(0.5)
    LIVE.mkdir(parents=True, exist_ok=True)
    rows = [[d, round(v / 1000, 2)] for d, v in sorted(obs.items())]
    (LIVE / "svc_exports.json").write_text(
        json.dumps({"freq": "M", "obs": rows}))
    print(f"  svc_exports: {len(rows)} months, "
          f"latest {rows[-1][0]} = {rows[-1][1]}")


if __name__ == "__main__":
    fetch()
