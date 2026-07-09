"""Parse cached releases for the three series. Emits:
  parsed_svc.json   {iso: US$ mn}  (later prid wins)
  parsed_walr.json  {iso: %}       (narrative era; later prid wins)
  parsed_pl.json    {iso: %}       (from title-month-anchored sentence)
  review_pl.txt     one line per sectoral release: prid, month, value, sentence
  review_walr.txt   per-release extracted (month, value) pairs
  svc_prints.json   {iso: [[prid, value], ...]} full print history for revision audit
  parse_fail.log
"""
import json, re
from html import unescape
from pathlib import Path
from datetime import date

HERE = Path(__file__).parent
REL = HERE / "releases"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MNUM = {m: i + 1 for i, m in enumerate(MONTHS)}
prids = json.load(open(HERE / "prids.json"))
fail = open(HERE / "parse_fail.log", "w")

def text_of(prid):
    h = (REL / f"{prid}.html").read_text()
    # cut the footer archive tree (starts at the year/month nav block)
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)))

def lines_of(prid):
    h = (REL / f"{prid}.html").read_text()
    t = unescape(re.sub(r"<[^>]+>", "\n", re.sub(
        r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)))
    return [l.strip() for l in t.split("\n") if l.strip()]

# ---------------- svc ----------------
svc, svc_prints = {}, {}
MABBR = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
row_re = re.compile(
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s*[–:\-]?\s*(\d{2}|\d{4})$")
for prid in sorted(prids["svc"], key=int):
    f = REL / f"{prid}.html"
    if not f.exists():
        fail.write(f"svc {prid}: html missing\n"); continue
    lines = lines_of(prid)
    got = {}
    for i, l in enumerate(lines):
        g = row_re.fullmatch(l)
        if not g:
            continue
        yr = int(g.group(2))
        if yr < 100:
            yr += 2000
        for j in range(i + 1, min(i + 4, len(lines))):
            if re.fullmatch(r"[\d,]+", lines[j]):
                iso = f"{yr}-{MABBR[g.group(1)[:3]]:02d}-01"
                got[iso] = float(lines[j].replace(",", ""))
                break
    if not got:
        fail.write(f"svc {prid}: no table rows ({prids['svc'][prid][1]})\n")
        continue
    for iso, v in got.items():
        svc[iso] = v
        svc_prints.setdefault(iso, []).append([int(prid), v])
json.dump(svc, open(HERE / "parsed_svc.json", "w"))
json.dump(svc_prints, open(HERE / "svc_prints.json", "w"))
print("svc:", len(svc), min(svc, default=None), max(svc, default=None))

# ---------------- walr (narrative era) ----------------
walr = {}
rw = open(HERE / "review_walr.txt", "w")
for prid in sorted((p for p in prids["walr"] if int(p) >= 54122), key=int):
    f = REL / f"{prid}.html"
    if not f.exists():
        fail.write(f"walr {prid}: html missing\n"); continue
    t = text_of(prid)
    i = t.find("fresh rupee loans")
    if i < 0:
        fail.write(f"walr {prid}: phrase missing\n"); continue
    seg = t[i:i + 400]
    j = seg.find("outstanding")
    if j > 0:
        seg = seg[:j]
    # keep only the first sentence (PSB/PVB breakdowns follow in the next one)
    sm = re.search(r"\.\s+(?=[A-Z])", seg)
    if sm:
        seg = seg[:sm.start() + 1]
    pairs = re.findall(
        r"([\d.]+) per cent (?:in |as at end[-\s]?|at end[-\s]?)"
        r"(%s),?\s*(\d{4})" % "|".join(MONTHS), seg)
    if not pairs:
        fail.write(f"walr {prid}: no pairs; seg={seg[:200]}\n"); continue
    rw.write(f"{prid} {prids['walr'][prid][1]} :: {pairs}\n")
    for v, mon, yr in pairs:      # later prid wins; within one release
        iso = date(int(yr), MNUM[mon], 1).isoformat()
        walr[iso] = float(v)
rw.close()
json.dump(walr, open(HERE / "parsed_walr.json", "w"))
print("walr:", len(walr), min(walr, default=None), max(walr, default=None))

# ---------------- personal loans ----------------
pl = {}
rp = open(HERE / "review_pl.txt", "w")
for prid in sorted(prids["pl"], key=int):
    f = REL / f"{prid}.html"
    ym, title = prids["pl"][prid]
    if not f.exists():
        fail.write(f"pl {prid}: html missing\n"); continue
    tm = re.search(r"Sectoral Deployment of Bank Credit\s*[–-]?\s*"
                   r"(?:Revised Data for\s+)?(%s)\s+(\d{4})" % "|".join(MONTHS),
                   title)
    if not tm:
        fail.write(f"pl {prid}: title not parsed: {title}\n"); continue
    mon, yr = tm.group(1), tm.group(2)
    iso = date(int(yr), MNUM[mon], 1).isoformat()
    t = text_of(prid)
    # isolate the highlights region (skip nav); find sentence w/ personal loans
    k = t.find("Highlights")
    body = t[k:] if k > 0 else t
    m = re.search(r"[Pp]ersonal loans?", body)
    sent = body[max(0, m.start() - 60):m.start() + 340].strip() if m else ""
    pats = [
        r"personal loans? segment[^.]{0,160}?growth of ([\d.]+) per cent",
        r"[Pp]ersonal loans?[^.]{0,160}?\bby ([\d.]+) per cent(?:\s*\(y-o-y\))? in %s %s" % (mon, yr),
        r"[Pp]ersonal loans?[^.]{0,160}?\bto ([\d.]+) per cent(?:\s*\(y-o-y\))? in %s %s" % (mon, yr),
        r"[Pp]ersonal loans?[^.]{0,120}?registered ([\d.]+) per cent growth",
        r"[Pp]ersonal loans?[^.]{0,120}?(?:moderated|accelerated|decelerated) to ([\d.]+) per cent",
        r"[Pp]ersonal loans?[^.]{0,160}?growth of ([\d.]+) per cent",
        r"[Pp]ersonal loans?[^.]{0,200}?([\d.]+) per cent[^.]{0,40}in %s %s" % (mon, yr),
    ]
    val, patno = None, None
    for n, p in enumerate(pats):
        mm = re.search(p, body)
        if mm:
            val, patno = float(mm.group(1)), n
            break
    flag = "MERGER" if "merger" in sent.lower() else ""
    rp.write(f"{prid}\t{iso}\tpat{patno}\t{val}\t{flag}\t{sent[:400]}\n")
    if val is None:
        fail.write(f"pl {prid} {iso}: NOT PARSED; sent={sent[:300]}\n")
        continue
    pl[iso] = val
rp.close()
json.dump(pl, open(HERE / "parsed_pl.json", "w"))
print("pl:", len(pl), min(pl, default=None), max(pl, default=None))
fail.close()
print("fails:", (HERE / "parse_fail.log").read_text().count("\n"))
