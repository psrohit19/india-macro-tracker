"""
RBI Payment System Indicators (PSI) fetcher — LIVE.
Populates: upi (M, ₹ lakh cr).

NPCI's own product-statistics page (npci.org.in) hard-403s non-browser
clients, so this uses RBI's machine-readable mirror instead:
  https://www.rbi.org.in/Scripts/PSIUserView.aspx
lists one "Payment System Indicators - <Month YYYY>" XLSX per month
(hosted on rbidocs.rbi.org.in, same F5/TSPD bot wall as the card stats —
browser-ish session headers + a b"PK" magic check handle it).

Workbook layout (single sheet named "<Month YYYY>"): row "2.6 UPI @" under
PART I; the last four columns are Value (₹ crore):
  [FY cumulative, same month last year, previous month, current month].
Rather than parsing the two-row header, the month labels are derived from
the sheet name: current = sheet month, prev = -1 month, yoy = -12 months.
So each monthly file yields three dated observations and the ~12 files on
the landing page give a continuous ~24-month series. ₹ crore / 1e5 =
₹ lakh crore.

Cross-check bonus: the same sheet's credit-card rows (4.1.1 PoS + 4.1.2
Others) reconcile with the cards series from rbi_files.py to ~0.2%.
"""
import json
import re
from datetime import date
from io import BytesIO
from pathlib import Path

import openpyxl
import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["upi"]
URL = "https://www.rbi.org.in/Scripts/PSIUserView.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 "
                   "Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Referer": URL}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MNUM = {m: i + 1 for i, m in enumerate(MONTHS)}


def _shift(d, months):
    m = d.month - 1 + months
    return date(d.year + m // 12, m % 12 + 1, 1)


def _listing(sess):
    """[(month_date, xlsx_url), ...] newest first."""
    r = sess.get(URL, timeout=90)
    out = []
    for a in BeautifulSoup(r.text, "lxml").find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        m = re.match(r"Payment System Indicators\s*[-–]\s*(%s)\s+(\d{4})"
                     % "|".join(MONTHS), t)
        if m:
            tr = a.find_parent("tr")
            for x in (tr.find_all("a", href=True) if tr else []):
                if x["href"].upper().endswith(".XLSX"):
                    out.append((date(int(m.group(2)), MNUM[m.group(1)], 1),
                                x["href"]))
    return out


def _download(sess, url, tries=3):
    for _ in range(tries):
        r = sess.get(url, timeout=120)
        if r.content[:2] == b"PK":
            return r.content
    raise ValueError(f"TSPD challenge not cleared for {url}")


def _upi_values(content, month):
    """{iso_date: ₹ lakh cr} for current / prev / year-ago month."""
    ws = openpyxl.load_workbook(BytesIO(content)).worksheets[0]
    for r in ws.iter_rows(values_only=True):
        label = next((c for c in r if isinstance(c, str) and c.strip()), "")
        if re.match(r"2\.6\s+UPI", label.strip()):
            nums = [c for c in r if isinstance(c, (int, float))]
            # 8 numerics: 4 volume cols then 4 value cols (₹ crore)
            if len(nums) < 8:
                raise ValueError("UPI row has too few numeric cells")
            val = nums[4:8]      # [FY cum, yoy month, prev month, current]
            return {
                _shift(month, -12).isoformat(): round(val[1] / 1e5, 2),
                _shift(month, -1).isoformat(): round(val[2] / 1e5, 2),
                month.isoformat(): round(val[3] / 1e5, 2),
            }
    raise ValueError("UPI row not found")


def fetch():
    sess = requests.Session()
    sess.headers.update(H)
    obs = {}
    # oldest first, so the newest file's (revised) figures win on overlap
    for month, url in reversed(_listing(sess)):
        try:
            obs.update(_upi_values(_download(sess, url), month))
        except Exception as e:
            print(f"  upi: {month} failed: {e}")
    if len(obs) < 14:
        print(f"  upi: only {len(obs)} obs — NOT writing")
        return
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / "upi.json").write_text(
        json.dumps({"freq": "M", "obs": [[d, v] for d, v in pairs]}))
    print(f"  upi: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")


if __name__ == "__main__":
    fetch()
