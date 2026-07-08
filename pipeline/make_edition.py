"""
Weekly/monthly edition generator — the distributable.

Produces edition.html: a dated, one-page, print-friendly snapshot (headline
strip + composite signals + "what changed" bullets + full category table of
YoY moves) meant to be emailed to partners on schedule, with the dashboard as
the click-through for detail. Print to PDF via headless Chrome for the email
attachment; the analyst can edit the bullets before sending.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
data = json.loads((ROOT / "data" / "data.json").read_text())
by_cat = {}
for s in data["series"]:
    by_cat.setdefault(s["category"], []).append(s)

def dcls(d, up):
    if not d or d["dir"] == 0 or up is None:
        return "neut"
    return "good" if (d["dir"] == 1) == up else "bad"

def yoy_row(s):
    for r in s["rows"]:
        if r[0].startswith("vs LY"):
            return r
    return None

heroes = [s for s in data["series"] if s.get("headline")]
comps = by_cat.get("Composite Signals", [])

rows_html = ""
for cat in data["categories"]:
    items = by_cat.get(cat, [])
    if not items or cat == "Composite Signals":
        continue
    rows_html += f'<tr class="cat"><td colspan="4">{cat}</td></tr>'
    for s in items:
        r = yoy_row(s)
        d = r[2] if r else None
        arrow = "→" if not d or d["dir"] == 0 else ("▲" if d["dir"] == 1 else "▼")
        rows_html += (f'<tr><td>{s["name"]}</td>'
                      f'<td class="v">{s["latest"]["value"]} {s["unit"]}</td>'
                      f'<td class="v">{s["latest"]["period"]}</td>'
                      f'<td class="v {dcls(d, s["up_is_good"])}">'
                      f'{arrow} {d["text"] if d else "—"} YoY</td></tr>')

hero_html = "".join(
    f'<div class="h"><div class="hn">{s["name"]}</div>'
    f'<div class="hv">{s["latest"]["value"]}<span> {s["unit"]}</span></div>'
    f'<div class="hy {dcls(yoy_row(s)[2] if yoy_row(s) else None, s["up_is_good"])}">'
    f'{(yoy_row(s)[2]["text"] + " YoY") if yoy_row(s) and yoy_row(s)[2] else ""}</div></div>'
    for s in heroes)

comp_html = "".join(
    f'<div class="h"><div class="hn">{s["name"]}</div>'
    f'<div class="hv">{s["latest"]["value"]}</div>'
    f'<div class="hy neut">vs 10-yr norm</div></div>'
    for s in comps)

bullets_html = "".join(
    f'<li class="{b["sentiment"]}">{b["text"]}</li>' for b in data.get("bullets", []))

asof = data["as_of"]
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>India Macro — Edition {asof}</title><style>
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#0b0b0b;background:#fff;
margin:0;padding:32px;max-width:860px;margin:0 auto}}
h1{{font-size:20px;margin:0}} .sub{{color:#52514e;font-size:13px;margin:2px 0 18px}}
h2{{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#898781;margin:20px 0 8px}}
.strip{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.h{{border:1px solid #e1e0d9;border-radius:8px;padding:10px 12px}}
.hn{{font-size:11px;color:#898781}} .hv{{font-size:20px;font-weight:650}}
.hv span{{font-size:11px;color:#898781;font-weight:400}}
.hy{{font-size:11.5px;font-weight:600}} .good{{color:#006300}} .bad{{color:#d03b3b}} .neut{{color:#898781}}
ul{{margin:0;padding-left:0;list-style:none}} li{{font-size:13px;padding:3px 0;color:#333}}
li:before{{content:"●";margin-right:8px;font-size:9px}}
li.good:before{{color:#006300}} li.bad:before{{color:#d03b3b}} li.neut:before{{color:#898781}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
td{{padding:4px 8px;border-bottom:1px solid #eee}}
tr.cat td{{font-weight:650;text-transform:uppercase;font-size:10.5px;letter-spacing:.04em;
color:#898781;padding-top:12px;border-bottom:1px solid #c3c2b7}}
td.v{{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}
.foot{{font-size:10.5px;color:#898781;margin-top:20px;line-height:1.5}}
@media print{{body{{padding:0}}}}
</style></head><body>
<h1>India Macro Tracker — Edition</h1>
<div class="sub">Data as of {asof} · sample data pending live fetchers · full dashboard has drill-downs &amp; CSV</div>
<h2>Headlines</h2><div class="strip">{hero_html}</div>
<h2>Composite signals</h2><div class="strip">{comp_html}</div>
<h2>What changed</h2><ul>{bullets_html}</ul>
<h2>All series — year-on-year</h2><table>{rows_html}</table>
<div class="foot">Internal use only. PMI and WGC series carry redistribution restrictions.
Seasonal series should be read YoY. Revision-prone series (Vahan, EPFO, trade, PFCE) are provisional
at first print. Generated automatically by the tracker pipeline; bullets are editable before circulation.</div>
</body></html>"""

out = ROOT / "edition.html"
out.write_text(html)
print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
