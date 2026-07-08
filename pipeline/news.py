"""
Top-10 macro headlines for the dashboard — refreshed with every pipeline run.

Pulls Google News RSS across a curated set of India + global macro queries,
scores items by macro-relevance keywords and recency, dedupes near-identical
titles, and writes data/news.json (top 10 with links). generate_data.py
embeds it into the page payload; the dashboard renders it where the old
"What changed" panel sat.
"""
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path(__file__).parent.parent / "data" / "news.json"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}

QUERIES = [
    ("RBI monetary policy OR repo rate", "IN"),
    ("India economy GDP OR inflation OR fiscal", "IN"),
    ("India government policy announcement economy", "IN"),
    ("Federal Reserve rate decision OR inflation", "US"),
    ("global economy OR IMF OR world growth", "US"),
    ("crude oil price OR OPEC", "US"),
    ("China economy stimulus OR exports", "US"),
    ("India markets FPI OR SEBI OR rupee", "IN"),
]

# words that make a headline decision-relevant for a CIO
WEIGHTS = {
    "rate": 4, "repo": 5, "rbi": 5, "fed": 4, "policy": 4, "budget": 4,
    "gdp": 4, "inflation": 4, "cpi": 3, "fiscal": 3, "tariff": 4,
    "stimulus": 3, "rupee": 3, "crude": 3, "oil": 2, "opec": 3,
    "sebi": 3, "fpi": 3, "monsoon": 3, "gst": 3, "imf": 3, "cut": 2,
    "hike": 3, "growth": 2, "deficit": 3, "announce": 2, "reform": 3,
    "china": 2, "exports": 2, "capex": 3, "downgrade": 4, "upgrade": 3,
}
JUNK = re.compile(r"(horoscope|cricket|bollywood|celebrit|astrolog)", re.I)
BAD_SOURCES = re.compile(r"(crypto|coin|mexc|cryptorank|nai500|sekber|blockchain|bitcoin|forex\s*live|fxstreet|tmgm)", re.I)


def _fetch(query, region):
    url = ("https://news.google.com/rss/search?q=" + requests.utils.quote(query)
           + f"+when:2d&hl=en-{region}&gl={region}&ceid={region}:en")
    r = requests.get(url, timeout=25, headers=H, proxies={"http": None, "https": None})
    r.raise_for_status()
    root = ET.fromstring(r.text)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = it.findtext("pubDate") or ""
        src = it.find("{https://news.google.com/rss}source")
        source = (it.findtext("source") or "").strip()
        try:
            ts = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        except Exception:
            ts = datetime.now(timezone.utc)
        if title and link and not BAD_SOURCES.search(source or "") and not BAD_SOURCES.search(title):
            items.append(dict(title=title, url=link, source=source, ts=ts.isoformat(), region=region))
    return items


def _score(item, now):
    t = item["title"].lower()
    if JUNK.search(t):
        return -99
    s = sum(w for k, w in WEIGHTS.items() if k in t)
    age_h = (now - datetime.fromisoformat(item["ts"])).total_seconds() / 3600
    s -= age_h / 12                      # freshness decay
    return s


def _dedupe(items):
    seen, out = [], []
    for it in items:
        key = set(re.findall(r"[a-z]{4,}", it["title"].lower()))
        if any(len(key & k) >= max(3, int(0.6 * min(len(key), len(k)))) for k in seen):
            continue
        seen.append(key)
        out.append(it)
    return out


def fetch():
    now = datetime.now(timezone.utc)
    pool = []
    for q, region in QUERIES:
        try:
            pool.extend(_fetch(q, region))
            time.sleep(0.4)
        except Exception as e:
            print(f"  news: query failed ({q[:30]}): {e!r}")
    pool.sort(key=lambda it: -_score(it, now))
    deduped = _dedupe(pool)
    india = [it for it in deduped if it["region"] == "IN"][:6]
    world = [it for it in deduped if it["region"] != "IN"][:10 - len(india)]
    top = india + world
    for it in top:
        # strip the " - Source" suffix Google News appends to titles
        it["title"] = re.sub(r"\s+-\s+[^-]{2,40}$", "", it["title"])
    OUT.write_text(json.dumps(dict(fetched=now.isoformat(), items=top), ensure_ascii=False))
    print(f"  news: {len(top)} headlines")
    return top


if __name__ == "__main__":
    fetch()
