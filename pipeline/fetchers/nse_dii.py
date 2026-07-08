"""
NSE DII (and provisional FII cash) daily flows.

Source: https://www.nseindia.com/reports/fii-dii
Unofficial JSON endpoint: https://www.nseindia.com/api/fiidiiTradeReact

NSE sits behind Akamai bot protection — a bare GET 401s. Required dance:
  1. GET https://www.nseindia.com with browser-like headers -> cookies
  2. reuse the Session for the /api call; throttle; refresh cookies on 401.
Prefer a maintained wrapper (nsepython / NseIndiaApi / jugaad-data) over
hand-rolling. NOTE: datacenter IPs (AWS/GCP) are often blocked — if running
in CI, route through a proxy or run this one fetcher from a small India VPS.
"""
SERIES_IDS = ["dii"]


def fetch():
    # TODO(wire-up), e.g. with nsepython:
    #   from nsepython import nsefetch
    #   j = nsefetch("https://www.nseindia.com/api/fiidiiTradeReact")
    #   dii = next(r for r in j if r["category"].startswith("DII"))
    #   return [{"series_id": "dii", "period_iso": <date>, "value": float(dii["netValue"])}]
    raise NotImplementedError("wire me up: see docstring")
