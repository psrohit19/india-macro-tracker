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

# (query, google-news locale, coverage bucket)
QUERIES = [
    ("RBI monetary policy OR repo rate OR India inflation", "IN", "IN"),
    ("India economy GDP OR fiscal OR government policy", "IN", "IN"),
    ("India markets FPI OR SEBI OR rupee OR budget", "IN", "IN"),
    ("Federal Reserve OR US inflation OR US economy", "US", "US"),
    ("US treasury yields OR FOMC OR jobs report", "US", "US"),
    ("ECB OR eurozone economy OR Europe inflation", "US", "EU"),
    ("Bank of Japan OR Japan economy OR yen", "US", "JP"),
    ("IMF OR global economy OR world growth OR trade war", "US", "GL"),
    ("crude oil price OR OPEC decision", "US", "GL"),
    ("China economy stimulus OR exports slowdown", "US", "GL"),
]

# Tier-1 sources only (matched against the Google News source name)
TIER1 = re.compile(
    r"(bloomberg|reuters|financial times|\bft\b|economic times|economictimes|"
    r"livemint|\bmint\b|business standard|businessline|moneycontrol|"
    r"wall street journal|wsj|cnbc|nikkei|the economist|ndtv profit|"
    r"business today|fortune india|the hindu|times of india|indian express|"
    r"barron|marketwatch|axios|associated press|\bap news\b|afp)", re.I)

# words that make a headline decision-relevant for a CIO
WEIGHTS = {
    "rate": 4, "repo": 5, "rbi": 5, "fed": 4, "policy": 4, "budget": 4,
    "gdp": 4, "inflation": 4, "cpi": 3, "fiscal": 3, "tariff": 4,
    "stimulus": 3, "rupee": 3, "crude": 3, "oil": 2, "opec": 3,
    "sebi": 3, "fpi": 3, "monsoon": 3, "gst": 3, "imf": 3, "cut": 2,
    "hike": 3, "growth": 2, "deficit": 3, "announce": 2, "reform": 3,
    "china": 2, "exports": 2, "capex": 3, "downgrade": 4, "upgrade": 3,
}
JUNK = re.compile(r"(horoscope|cricket|bollywood|celebrit|astrolog|"
                  r"\bnepal\b|\bnrb\b|rastra bank|sri lanka|\bpakistan\b|"
                  r"bangladesh|\bbhutan\b|maldives)", re.I)
BAD_SOURCES = re.compile(r"(crypto|coin|mexc|cryptorank|nai500|sekber|blockchain|bitcoin|forex\s*live|fxstreet|tmgm)", re.I)


def _fetch(query, region, bucket):
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
            if not TIER1.search(source or ""):
                continue
            items.append(dict(title=title, url=link, source=source, ts=ts.isoformat(), bucket=bucket))
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
    for q, region, bucket in QUERIES:
        try:
            pool.extend(_fetch(q, region, bucket))
            time.sleep(0.4)
        except Exception as e:
            print(f"  news: query failed ({q[:30]}): {e!r}")
    pool.sort(key=lambda it: -_score(it, now))
    deduped = _dedupe(pool)
    # coverage quotas: India 4, US 2, Europe 1, Japan 1, Global 2 — then backfill
    quotas = {"IN": 4, "US": 2, "EU": 1, "JP": 1, "GL": 2}
    top, used = [], set()
    for b, n in quotas.items():
        for it in [x for x in deduped if x["bucket"] == b][:n]:
            top.append(it); used.add(it["url"])
    for it in deduped:                          # backfill to 10 if a bucket ran dry
        if len(top) >= 10:
            break
        if it["url"] not in used:
            top.append(it); used.add(it["url"])
    top = top[:10]
    for it in top:
        # strip the " - Source" suffix Google News appends to titles
        it["title"] = re.sub(r"\s+-\s+[^-]{2,40}$", "", it["title"])
    OUT.write_text(json.dumps(dict(fetched=now.isoformat(), items=top), ensure_ascii=False))
    print(f"  news: {len(top)} headlines")
    return top


if __name__ == "__main__":
    fetch()
