"""
RBI bank-wise ATM/POS/Card statistics fetcher — LIVE.
Populates: cards (M, ₹ lakh cr credit-card spend per month).

Source: https://www.rbi.org.in/Scripts/ATMView.aspx — monthly listing with an
XLSX per month hosted on rbidocs.rbi.org.in. Earlier years are reachable via
the ASP.NET postback (hdnYear=<YYYY>, hdnMonth=0, hidden submit
UsrFontCntr$btn), same mechanism as the press-release archive.

Quirks (verified Jul 2026):
  * rbidocs.rbi.org.in sits behind F5/TSPD bot protection: a bare
    requests.get returns a captcha HTML page. Using a requests.Session with
    browser-ish User-Agent/Accept/Referer headers passes; verify the payload
    starts with b"PK" before parsing and retry once otherwise.
  * XLSX filenames are too irregular to trust (ATMMAY2026<hash>.XLSX, but
    also ATM122025<hash>, ATMAPRIL25<hash>, ATMMAY23062025<hash>...) — the
    month is taken from the listing-row TITLE text ("Bank-wise ATM/POS/Card
    Statistics - May 2026") instead.
  * Months get a "(Revised)" re-upload; when a month appears twice the row
    whose title contains "Revised" wins.
  * Workbook (post-2023 revamped format), single sheet: bank rows have a
    numeric Sr.No in col B and bank name in col C. Credit-card VALUE columns
    (in ₹ '000): col M (index 12) = at PoS, col O (index 14) = Online
    (e-com), col Q (16) = Others. The dashboard series = PoS + e-com summed
    across all banks, converted to ₹ lakh crore (divide ₹'000 by 1e9).
    The sheet's own "Total" row holds uncomputed =SUM() formulas, so the
    bank rows are summed directly.
"""
import json
import re
from datetime import date
from pathlib import Path
from io import BytesIO

import openpyxl
import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["cards"]
URL = "https://www.rbi.org.in/Scripts/ATMView.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 "
                   "Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Referer": URL}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MNUM = {m: i + 1 for i, m in enumerate(MONTHS)}
_TITLE_RE = re.compile(r"Statistics\s*[-–]\s*(%s)\s+(\d{4})" % "|".join(MONTHS))


def _listing_urls(sess, year=None):
    """XLSX urls from the ATMView listing (optionally a specific year)."""
    if year is None:
        r = sess.get(URL, timeout=90)
    else:
        r0 = sess.get(URL, timeout=90)
        soup = BeautifulSoup(r0.text, "lxml")
        data = {i["name"]: i.get("value", "") for i in soup.find_all("input")
                if i.get("name") and i.get("type") == "hidden"}
        data.update({"hdnYear": str(year), "hdnMonth": "0",
                     "UsrFontCntr$btn": ""})
        r = sess.post(URL, data=data, timeout=120)
    out = []                       # (month_date, url, is_revised)
    soup = BeautifulSoup(r.text, "lxml")
    for tr in soup.find_all("tr"):
        text = tr.get_text(" ", strip=True)
        m = _TITLE_RE.search(text)
        if not m:
            continue
        d = date(int(m.group(2)), MNUM[m.group(1)], 1)
        for a in tr.find_all("a", href=True):
            if a["href"].upper().endswith(".XLSX"):
                out.append((d, a["href"], "Revised" in text))
    return out


def _cc_spend_lakh_cr(content):
    """Credit-card PoS + e-com value (₹ lakh cr) summed over bank rows."""
    ws = openpyxl.load_workbook(BytesIO(content)).worksheets[0]
    tot = 0.0
    n = 0
    for r in ws.iter_rows(values_only=True):
        if len(r) < 15:
            continue
        sr, name = r[1], r[2]
        if isinstance(sr, (int, float)) and isinstance(name, str) and name.strip():
            try:
                tot += float(r[12] or 0) + float(r[14] or 0)   # ₹ '000
                n += 1
            except (TypeError, ValueError):
                continue
    if n < 20:
        raise ValueError(f"only {n} bank rows parsed — format changed?")
    return round(tot / 1e9, 3)


def _download(sess, url, tries=3):
    for _ in range(tries):
        r = sess.get(url, timeout=120)
        if r.content[:2] == b"PK":
            return r.content
    raise ValueError(f"TSPD challenge not cleared for {url}")


def fetch(min_months=15):
    sess = requests.Session()
    sess.headers.update(H)
    by_month = {}                       # date -> (url, is_revised)
    entries = []
    for year in (None, date.today().year - 1, date.today().year - 2):
        if year is not None and len(by_month) >= min_months:
            break
        entries = _listing_urls(sess, year)
        for d, u, rev in entries:
            cur = by_month.get(d)
            if cur is None or (rev and not cur[1]):
                by_month[d] = (u, rev)
    obs = {}
    for d, (u, _) in sorted(by_month.items(), reverse=True)[:min_months + 4]:
        try:
            obs[d.isoformat()] = _cc_spend_lakh_cr(_download(sess, u))
        except Exception as e:
            print(f"  cards: {d} failed: {e}")
    if len(obs) < 14:
        print(f"  cards: only {len(obs)} obs — NOT writing")
        return
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / "cards.json").write_text(
        json.dumps({"freq": "M", "obs": [[d, v] for d, v in pairs]}))
    print(f"  cards: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")


if __name__ == "__main__":
    fetch()
