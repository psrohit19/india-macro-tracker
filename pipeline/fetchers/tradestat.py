"""
Commerce Ministry TRADESTAT (DGCI&S) fetcher — LIVE.
Populates: exports, imports, trade_def (merchandise, US$ bn, monthly).

Verified behaviour (Jul 2026):

  * https://tradestat.commerce.gov.in is a Laravel app; the root 302s to
    /eidb/commodity_wise_export. Monthly data lives under /meidb/ ("Monthly
    Export Import Data Bank").
  * /meidb/commoditywise_export and /meidb/commoditywise_import are POST
    forms. Quirks that cost time to discover:
      - CSRF: GET the form first, read the hidden `_token` input, POST it
        back WITH the same cookie jar (laravel_session). Tokens rotate per
        page load.
      - The export form fields are ddMonth/ddYear/ddCommodityLevel/
        ddReportVal/ddReportYear; the IMPORT form prefixes them `imdd`
        (imddMonth, ...). Both need the radio `comlev=all` or the server
        500s with a "Not Found" error page.
      - ddReportVal=1 => US$ Million; ddReportYear=2 => calendar year.
      - The response is an HTML table whose <tfoot> holds "India's Total
        Export/Import" with 6 numeric cells: [same month prior year (R),
        requested month (F), %growth, Jan-cum prior year, Jan-cum, %growth].
        So one request yields TWO monthly observations, and the prior-year
        figure is the REVISED one — later-year requests overwrite earlier.
      - Months not yet published return 0.00 in the current-year cell (the
        prior-year cell is still populated). As of 08 Jul 2026 the MEIDB is
        populated through April 2026; May 2026 exists only in the PIB press
        release (see PIB_PATCH below).
  * PIB "India's Foreign Trade" monthly press release (~15th) carries the
    quick estimates one month ahead of MEIDB. It is fetched live from
    pib.gov.in and parsed for "Merchandise exports/imports during <Month>
    <Year> were US$ X Billion". PRIDs cannot be discovered without a search
    backend, so known PRIDs are pinned in PIB_PATCH; once MEIDB catches up,
    the MEIDB (revised) figure silently supersedes the PIB quick estimate.
    Cross-checks done at pin time (May 2026 release, PRID 2273044):
      MEIDB Apr-2026 exports 43,727.16 vs PIB cumulative-implied 43.71 bn;
      MEIDB May-2025 exports 38,303.59 vs PIB "US$ 38.30 Billion". Match.

trade_def = imports - exports (positive number = deficit), only for months
where both legs exist.

Writes data/live/{exports,imports,trade_def}.json:
  {"freq": "M", "obs": [["YYYY-MM-01", value], ...]}   # US$ bn, 2dp
"""
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

BASE = "https://tradestat.commerce.gov.in"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) macro-tracker/1.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"
START_YEAR = 2024          # earliest calendar year of observations kept

# (path, form-field prefix, tfoot label)
FLOWS = {
    "exports": ("/meidb/commoditywise_export", "dd", "Total Export"),
    "imports": ("/meidb/commoditywise_import", "imdd", "Total Import"),
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# PIB "India's Foreign Trade" releases for months MEIDB hasn't loaded yet.
# {(year, month): press-release URL}. Update when a new month's release
# lands (search pib.gov.in for "India's Foreign Trade"); prune once MEIDB
# has the month (harmless to leave — MEIDB values overwrite these).
PIB_PATCH = {
    (2026, 5): "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2273044",
}


def _month_pair(s, flow, month, year, tries=3):
    """One MEIDB request -> ((year-1, month, US$mn revised), (year, month, US$mn))
    Either value may be None (0.00 = not yet published)."""
    path, pfx, label = FLOWS[flow]
    for i in range(tries):
        try:
            r = s.get(f"{BASE}{path}", timeout=60, headers=H)
            r.raise_for_status()
            tok = re.search(r'name="_token" value="([^"]+)"', r.text).group(1)
            r = s.post(f"{BASE}{path}", timeout=180, headers={
                **H, "Referer": f"{BASE}{path}"}, data={
                "_token": tok, f"{pfx}Month": month, f"{pfx}Year": year,
                "comlev": "all", f"{pfx}CommodityLevel": "2",
                f"{pfx}ReportVal": "1", f"{pfx}ReportYear": "2"})
            r.raise_for_status()
            i0 = r.text.find(label)
            if i0 < 0:
                raise ValueError(f"no '{label}' row for {month}/{year}")
            nums = re.findall(r"<b>\s*([\d,]+\.?\d*)\s*</b>",
                              r.text[i0:i0 + 1200])
            prev, cur = (float(nums[0].replace(",", "")),
                         float(nums[1].replace(",", "")))
            return (prev or None), (cur or None)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _pib_patch(obs_x, obs_m):
    """Best-effort: parse pinned PIB releases for months MEIDB lacks."""
    for (y, m), url in sorted(PIB_PATCH.items()):
        iso = f"{y}-{m:02d}-01"
        if iso in obs_x and iso in obs_m:
            continue                       # MEIDB caught up
        try:
            t = re.sub(r"<[^>]+>", " ", requests.get(
                url, timeout=60, headers=H).text)
            t = re.sub(r"\s+", " ", t)
            for flow, obs in (("exports", obs_x), ("imports", obs_m)):
                pat = (rf"Merchandise {flow} during {MONTHS[m - 1]} {y}\s*"
                       rf"were US\$\s*([\d,]+\.?\d*)\s*Billion")
                g = re.search(pat, t, re.I)
                if g and iso not in obs:
                    obs[iso] = float(g.group(1).replace(",", "")) * 1000
                    print(f"  PIB patch {flow} {iso}: {obs[iso]/1000:.2f} bn")
        except Exception as e:
            print(f"  PIB patch failed for {iso}: {e}")


def _save(sid, obs_mn):
    LIVE.mkdir(parents=True, exist_ok=True)
    obs = [[d, round(v / 1000, 2)] for d, v in sorted(obs_mn.items())]
    (LIVE / f"{sid}.json").write_text(json.dumps({"freq": "M", "obs": obs}))
    print(f"  {sid}: {len(obs)} months, latest {obs[-1][0]} = {obs[-1][1]}")


def fetch():
    print("TRADESTAT MEIDB pull (merchandise trade):")
    today = date.today()
    out = {}
    for flow in FLOWS:
        s = requests.Session()
        obs = {}
        # Request years START_YEAR+1 .. current, ascending: each (month, Y)
        # request also returns (month, Y-1) *revised*, which overwrites the
        # first-print value picked up by the earlier year's pass.
        for y in range(START_YEAR + 1, today.year + 1):
            for m in range(1, 13):
                if (y, m) > (today.year, today.month):
                    break
                prev, cur = _month_pair(s, flow, m, y)
                if prev:
                    obs[f"{y - 1}-{m:02d}-01"] = prev
                if cur:
                    obs[f"{y}-{m:02d}-01"] = cur
                time.sleep(1.0)
        out[flow] = obs
    _pib_patch(out["exports"], out["imports"])
    _save("exports", out["exports"])
    _save("imports", out["imports"])
    deficit = {d: out["imports"][d] - out["exports"][d]
               for d in out["exports"] if d in out["imports"]}
    _save("trade_def", deficit)


if __name__ == "__main__":
    fetch()
