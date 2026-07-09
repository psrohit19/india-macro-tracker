"""One-off backfill: CGA monthly accounts 2016-04..2024-03 -> tmp_cga_raw.json.

Reuses cga.py's raw-regex cell extraction (bs4 sees zero <td> on these pages).
Captures BE + actuals + pct + prior-year paren pct for cross-checking.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent / "pipeline" / "fetchers"))
import cga  # noqa: E402

OUT = Path(__file__).parent / "tmp_cga_raw.json"
CACHE = Path(__file__).parent / "tmp_cga_cache"
CACHE.mkdir(exist_ok=True)


def get(y, m):
    fy = cga._fy(y, m)
    f = CACHE / f"{y}-{m:02d}.html"
    if f.exists():
        return f.read_text(errors="replace")
    url = cga.BASE.format(m=m, fy=fy)
    r = requests.get(url, timeout=60, headers=cga.H)
    if r.status_code == 200 and "Fiscal Deficit" in r.text:
        f.write_text(r.text)
        time.sleep(0.4)
        return r.text
    return None


def num_join(s):
    """Single-number cell; spaces inside the number are rendering noise
    ('18753 7' -> 187537)."""
    s = s.replace(",", "").replace(" ", "").strip()
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def num_first(s):
    """First numeric token of a merged two-number cell ('100642 882')."""
    s = s.replace(",", "")
    mt = re.match(r"\s*(-?\d+(?:\.\d+)?)", s)
    return float(mt.group(1)) if mt else None


def pct_pair(cells):
    """(pct, paren_pct) from a row's trailing cells like '79.3 %', '( 74.0 %)'."""
    pct = paren = None
    for c in cells:
        c2 = c.replace(" ", "")
        m1 = re.match(r"^(-?\d+(?:\.\d+)?)%", c2)
        m2 = re.match(r"^\((-?\d+(?:\.\d+)?)%\)", c2)
        if m1 and pct is None:
            pct = float(m1.group(1))
        elif m2 and paren is None:
            paren = float(m2.group(1))
        if pct is not None and paren is not None:
            break
    return pct, paren


def row_vals(cells, i, first_token=False):
    """After label at i: skip blanks/'(Details)', return (BE, actuals, pct, paren).

    first_token=True for FY16-17 rows whose cells merge two numbers
    (capital + loans); otherwise cells hold ONE number, possibly with
    stray internal spaces."""
    fn = num_first if first_token else num_join
    nums, rest = [], []
    for c in cells[i + 1:i + 8]:
        cs = c.strip()
        if not cs or cs.lower() == "(details)":
            continue
        if "%" in cs:
            rest.append(cs)
            if len(rest) >= 2:
                break
            continue
        if len(nums) < 2:
            v = fn(cs)
            if v is not None:
                nums.append(v)
    pct, paren = pct_pair(rest)
    be = nums[0] if len(nums) >= 1 else None
    act = nums[1] if len(nums) >= 2 else None
    return be, act, pct, paren


def find(cells, label):
    for i, c in enumerate(cells):
        if re.sub(r"\(.*?\)", "", c).strip().lower().startswith(label.lower()):
            return i
    return None


def parse(html, fy_start_year):
    cells = cga._cells(html)
    rec = {}
    i = find(cells, "Fiscal Deficit")
    if i is not None:
        be, act, pct, paren = row_vals(cells, i)
        rec["fd"] = {"be": be, "act": act, "pct": pct, "paren": paren}
    if fy_start_year >= 2017:
        i = find(cells, "Capital Expenditure")
        if i is not None:
            be, act, pct, paren = row_vals(cells, i)
            rec["cap"] = {"be": be, "act": act, "pct": pct, "paren": paren}
    else:  # FY16-17: Plan/Non-Plan split; capex = sum of two On Capital Account rows
        idxs = [i for i, c in enumerate(cells)
                if c.strip().lower().startswith("on capital account")]
        if len(idxs) == 2:
            tot_be = tot_act = 0.0
            parts = []
            ok = True
            for i in idxs:
                be, act, pct, paren = row_vals(cells, i, first_token=True)
                if be is None or act is None:
                    ok = False
                    break
                tot_be += be
                tot_act += act
                parts.append([be, act, pct])
            if ok:
                rec["cap"] = {"be": tot_be, "act": tot_act, "pct": None,
                              "paren": None, "parts": parts}
    return rec


def validate(iso, rec):
    """Printed pct must equal act/BE (catches split/merged-cell mis-parses)."""
    bad = []
    for key in ("fd", "cap"):
        r = rec.get(key)
        if not r:
            continue
        if "parts" in r:  # FY16-17: check each sub-row against its printed pct
            for j, (be, act, pct) in enumerate(r["parts"]):
                if pct is not None and abs(act / be * 100 - pct) > 0.06:
                    bad.append(f"{key}.part{j}: {act}/{be}={act/be*100:.2f} vs printed {pct}")
        elif r.get("be") and r.get("act") is not None and r.get("pct") is not None:
            if abs(r["act"] / r["be"] * 100 - r["pct"]) > 0.06:
                bad.append(f"{key}: {r['act']}/{r['be']}={r['act']/r['be']*100:.2f} "
                           f"vs printed {r['pct']}")
    for b in bad:
        print(f"  !! {iso} INCONSISTENT {b}")
    return not bad


def main():
    out = {}
    y, m = 2016, 4
    while (y, m) <= (2024, 3):
        iso = f"{y}-{m:02d}"
        fy_start = y if m >= 4 else y - 1
        try:
            html = get(y, m)
        except Exception as e:
            print(f"  {iso}: FETCH ERR {e}")
            html = None
        if html:
            rec = parse(html, fy_start)
            rec["consistent"] = validate(iso, rec)
            out[iso] = rec
            fd = rec.get("fd", {})
            cap = rec.get("cap", {})
            print(f"  {iso}: FD {fd.get('pct')}% (py {fd.get('paren')}) "
                  f"BE {fd.get('be')} | cap {cap.get('act')} cr BE {cap.get('be')}")
        else:
            print(f"  {iso}: UNAVAILABLE")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT} ({len(out)} months)")


if __name__ == "__main__":
    main()
