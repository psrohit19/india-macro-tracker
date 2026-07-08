"""Inject data/data.json into template.html -> dashboard.html + index.html.
index.html is an identical copy so GitHub Pages serves the tracker at the
repo's root URL."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
data = (ROOT / "data" / "data.json").read_text()
data = data.replace("</", "<\\/")
html = (ROOT / "pipeline" / "template.html").read_text().replace("/*__DATA__*/", data)
for name in ("dashboard.html", "index.html"):
    (ROOT / name).write_text(html)
print(f"wrote dashboard.html + index.html ({len(html)//1024} KB)")
