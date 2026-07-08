"""
RBI press-release fetcher — LIVE.
Populates: liquidity (D, ₹ lakh cr), walr (M, %), personal_loans (M, % YoY).

Source: https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx
The archive is an ASP.NET postback: POST the page's hidden fields plus
hdnYear=<YYYY>, hdnMonth=<1-12> and the hidden submit button
UsrFontCntr$btn — the response lists every release of that month as
BS_PressReleaseDisplay.aspx?prid=<id> links (verified Jul 2026).

Per-series parsing:
  liquidity — daily "Money Market Operations as on <date>" releases.
      Line "F. Net liquidity injected (outstanding including today's
      operations) [injection (+)/absorption (-)]" is the system net LAF in
      ₹ crore, injection positive. The dashboard convention is
      positive = SURPLUS (RBI absorbing), so value = -F / 1e5  (₹ lakh cr).
      The obs date is the "as on" date in the title.
  walr — monthly "Lending and Deposit Rates of Scheduled Commercial Banks –
      <Month YYYY>" releases. The body states "The weighted average lending
      rate (WALR) on fresh rupee loans of SCBs <verb> X per cent in
      <Month YYYY>" — the data month lags the release title month by one.
      We parse the first "<num> per cent in <Month YYYY>" after the phrase
      "fresh rupee loans".
  personal_loans — monthly "Sectoral Deployment of Bank Credit – <Month
      YYYY>" releases: "Credit to personal loans segment recorded a y-o-y
      growth of X per cent". Data month is in the title. NOTE: from Dec 2025
      the reporting fortnight is the calendar month-end (Banking Laws
      (Amendment) Act 2025), with the YoY base still on the old definition —
      RBI's printed growth is used as-is.

Quirk: titles use an en-dash (–); month names are full. Wording of the
highlight sentences drifts a little between months, so multiple fallback
patterns are tried and failures are logged, never guessed.
"""
import json
import re
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_IDS = ["liquidity", "walr", "personal_loans"]
URL = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
LIVE = Path(__file__).parent.parent.parent / "data" / "live"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MNUM = {m: i + 1 for i, m in enumerate(MONTHS)}


def _month_listing(sess, year, month):
    """[(prid, title), ...] for one archive month via the hdnYear postback."""
    r = sess.get(URL, timeout=90)
    soup = BeautifulSoup(r.text, "lxml")
    data = {i["name"]: i.get("value", "") for i in soup.find_all("input")
            if i.get("name") and i.get("type") == "hidden"}
    data.update({"hdnYear": str(year), "hdnMonth": str(month),
                 "UsrFontCntr$btn": ""})
    r2 = sess.post(URL, data=data, timeout=120)
    out = []
    # NB: hrefs are unquoted in the raw HTML — parse with BeautifulSoup.
    for a in BeautifulSoup(r2.text, "lxml").find_all("a", href=True):
        m = re.search(r"prid=(\d+)", a["href"])
        if m and a.get_text(strip=True):
            out.append((m.group(1), a.get_text(" ", strip=True)))
    return out


def _release_text(sess, prid):
    r = sess.get(f"{URL}?prid={prid}", timeout=90)
    return BeautifulSoup(r.text, "lxml").get_text(" ", strip=True)


def _num(s):
    return float(s.replace(",", ""))


def _write(sid, freq, obs, n_min=14):
    if len(obs) < n_min:
        print(f"  {sid}: only {len(obs)} obs — NOT writing (<{n_min})")
        return False
    LIVE.mkdir(parents=True, exist_ok=True)
    pairs = sorted(obs.items())
    (LIVE / f"{sid}.json").write_text(
        json.dumps({"freq": freq, "obs": [[d, v] for d, v in pairs]}))
    print(f"  {sid}: {len(pairs)} obs, latest {pairs[-1][0]} = {pairs[-1][1]}")
    return True


def _months_back(n, today=None):
    today = today or date.today()
    y, m = today.year, today.month
    for _ in range(n):
        yield y, m
        m -= 1
        if m == 0:
            y, m = y - 1, 12


def fetch_liquidity(want=24):
    sess = requests.Session()
    sess.headers.update(H)
    obs = {}
    for y, m in _months_back(3):
        if len(obs) >= want:
            break
        for prid, title in _month_listing(sess, y, m):
            if len(obs) >= want:
                break
            tm = re.match(r"Money Market Operations as on (.+)", title)
            if not tm:
                continue
            d = datetime.strptime(tm.group(1).strip(), "%B %d, %Y").date()
            if d.isoformat() in obs:
                continue
            text = _release_text(sess, prid)
            # The label ends with "[injection (+)/absorption (-)]*" — anchor
            # on the closing bracket, as the bracket itself contains +/-.
            fm = re.search(
                r"F\. Net liquidity injected .{0,120}?\]\s*\*?\s*"
                r"(-?[\d,]+(?:\.\d+)?)", text)
            if not fm:
                print(f"  liquidity: no F-line in prid={prid} ({title})")
                continue
            obs[d.isoformat()] = round(-_num(fm.group(1)) / 1e5, 3)
    _write("liquidity", "D", obs)


def fetch_walr(months=16):
    sess = requests.Session()
    sess.headers.update(H)
    obs = {}
    for y, m in _months_back(months):
        for prid, title in _month_listing(sess, y, m):
            if not re.match(r"Lending and Deposit Rates of Scheduled "
                            r"Commercial Banks", title):
                continue
            text = _release_text(sess, prid)
            i = text.find("fresh rupee loans")
            if i < 0:
                print(f"  walr: phrase missing in prid={prid}")
                continue
            wm = re.search(r"([\d.]+) per cent in (%s) (\d{4})"
                           % "|".join(MONTHS), text[i:i + 400])
            if not wm:
                print(f"  walr: value not parsed in prid={prid} ({title})")
                continue
            iso = date(int(wm.group(3)), MNUM[wm.group(2)], 1).isoformat()
            obs.setdefault(iso, float(wm.group(1)))
            break                     # one release per month
    _write("walr", "M", obs)


def fetch_personal_loans(months=16):
    sess = requests.Session()
    sess.headers.update(H)
    obs = {}
    for y, m in _months_back(months):
        for prid, title in _month_listing(sess, y, m):
            tm = re.match(r"Sectoral Deployment of Bank Credit\s*[–-]\s*"
                          r"(%s) (\d{4})" % "|".join(MONTHS), title)
            if not tm:
                continue
            iso = date(int(tm.group(2)), MNUM[tm.group(1)], 1).isoformat()
            text = _release_text(sess, prid)
            pm = (re.search(r"personal loans segment recorded a y-o-y growth"
                            r" of ([\d.]+) per cent", text) or
                  re.search(r"[Pp]ersonal loans[^.]{0,200}?growth of "
                            r"([\d.]+) per cent", text) or
                  re.search(r"[Pp]ersonal loans[^.]{0,200}?([\d.]+) per cent",
                            text))
            if not pm:
                print(f"  personal_loans: not parsed in prid={prid} ({title})")
                continue
            obs.setdefault(iso, float(pm.group(1)))
            break
    _write("personal_loans", "M", obs)


def fetch():
    fetch_liquidity()
    fetch_walr()
    fetch_personal_loans()


if __name__ == "__main__":
    fetch()
