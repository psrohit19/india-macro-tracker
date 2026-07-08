# India Macro Tracker — Blueprint & Data-Source Map

*Prepared July 2026 · for internal use*

This document is the build plan for a weekly/monthly India macroeconomic tracker served as a
live, daily-refreshed web dashboard. It covers the indicator universe, where each series
comes from and how it's accessed, the release calendar, the comparison framework, the
technical architecture, and a phased build plan. A working prototype (`dashboard.html` +
`pipeline/`) accompanies this document.

---

## 1. Design principles

**Ingest at native frequency, publish on two cadences.** Daily/weekly/fortnightly series
(FII, DII, yields, FX, reserves, credit) are stored raw and also rolled up to the monthly
grid — flows are summed, stocks taken at month-end, averages/max where appropriate — so the
weekly edition shows the high-frequency pulse and the monthly edition puts *every* series on
one comparable monthly grid.

**Four comparisons on every metric.** Latest value vs (1) the most recent previous period,
(2) the same period last year, (3) the trailing 12-period average, and (4) the trailing
10-year average — both averages at the series' native frequency (120 points for monthly, 40
quarters, 520 weeks, ~2,500 trading days; series younger than 10 years use their full
available history). Deltas are expressed in percentage points/bps for rates, % change for levels, and
absolute terms for flows (whose sign flips). Delta color = direction × whether up is good
for that series (falling CPI is green; falling IIP is red).

**Revisions are first-class.** Vahan registrations, EPFO payrolls, GST, trade, PFCE and every
"provisional" first print restate. Store vintages — keep the old value when a new one
arrives — so any past edition can be reproduced "as known on date X".

**Free sources only in v1.** The full 61-series universe below is buildable at zero data
cost. Known paid gates (SIAM granular auto data, PMI sub-indices, CMIE, DGCIS bulk trade,
NielsenIQ FMCG, real-estate consultancies) are documented in §6 as conscious add-ons.

---

## 2. The indicator universe (61 series)

Freq: D daily · W weekly · F fortnightly · M monthly · Q quarterly.
Access: **api** (clean programmatic) · **file** (Excel/CSV download) · **scrape** (HTML/session parsing) · **pdf** (PDF table extraction).

### Prices & Inflation
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| CPI (combined; rural/urban cuts) | M | MoSPI eSankhyiki API | api | 12th, 4 pm |
| Core CPI | M | derived from CPI groups | api | 12th |
| Food inflation (CFPI) | M | MoSPI eSankhyiki API | api | 12th |
| WPI | M | OEA / eSankhyiki API | api | 14th |

### Output & Activity
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| IIP | M | MoSPI eSankhyiki API | api | **28th**, 4 pm (moved from 12th, Apr 2025) |
| Eight core industries | M | OEA / PIB | pdf | last working day |
| Manufacturing PMI (headline) | M | S&P Global press page | scrape | 1st business day |
| Services PMI (headline) | M | S&P Global press page | scrape | 3rd business day |
| Real GDP / GVA | Q | MoSPI NAS API | api | end Feb/May/Aug/Nov |
| PFCE (+ GFCF, GFCE) | Q | MoSPI NAS, expenditure side | api | with GDP |

### Fiscal
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Gross GST collections (+state cuts) | M | gst.gov.in monthly PDF | pdf | 1st |
| Fiscal deficit, receipts, expenditure (FYTD, % of BE) | M | CGA .xlsm dashboard | file | last working day |
| E-way bills | M | GSTN / PIB | scrape | early month |

### External Sector
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Merchandise exports / imports / trade deficit | M | Commerce/DGCI&S via PIB (+ TRADESTAT Excel) | pdf | ~15th |
| Forex reserves (FCA/gold split) | W | RBI Weekly Statistical Supplement | scrape | Friday ~5 pm |
| CAD / BoP; external debt | Q | RBI | file | quarterly |

### Flows & Markets
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| FPI net flows, equity & debt, ₹ + USD | D | NSDL FPI Monitor | scrape | EOD |
| DII net flows | D | NSE `fiidiiTradeReact` | scrape | ~6 pm |
| SIP / MF inflows | M | AMFI | file | ~8th–10th |
| 10Y G-sec yield | D | FBIL (structured daily file) | file | EOD |
| INR/USD reference rate | D | FBIL / RBI archive | scrape | ~1:30 pm |
| System liquidity (net LAF) | D | RBI Money Market Operations PR | pdf | next morning |

### Money, Credit & Banking
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Policy repo rate / MPC stance | 6×/yr | RBI press releases | scrape | MPC calendar |
| M3 growth | F | RBI WSS | scrape | fortnightly |
| Bank credit / deposit growth | F | RBI WSS (merger-adjusted) | scrape | fortnightly |
| Credit card spends | M | RBI bank-wise card statistics | file | ~2-week lag |
| Personal-loan / sectoral credit growth | M | RBI sectoral deployment | file | ~1-month lag |

### Consumption & Demand
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| PV retail sales (4W) | M | FADA press release / Vahan | scrape | ~5th–7th |
| 2W retail sales | M | FADA / Vahan | scrape | ~5th–7th |
| Tractor sales | M | TMA (free aggregate) + M&M/Escorts filings (1st) | scrape | 1st / mid-month |
| UPI value & volume | M | NPCI monthly file; RBI PSI xlsx (stable history) | file | 1st–3rd |
| Petroleum consumption | M | PPAC | pdf | mid–late month |
| Domestic air passengers | M | DGCA PDF / data.gov.in API | api | ~3rd week |
| FASTag toll collections | M | NPCI / NHAI | file | early month |

### Rural & Agri
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Rainfall vs LPA | W (seasonal) | IMD | scrape | weekly |
| Reservoir storage (% capacity) | W | CWC bulletin | pdf | Thursday |
| MGNREGA work demand | M | nrega.nic.in / data.gov.in | api | monthly |
| Rural wage growth | M | Labour Bureau | pdf | ~2-month lag |
| Fertiliser sales | M | Dept. of Fertilizers | scrape | monthly |
| (seasonal add-on) Kharif/Rabi sowing acreage | W | Agri Ministry PR | scrape | weekly in season |

### Employment
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Unemployment rate (PLFS CWS — **monthly since Apr 2025**) | M | MoSPI bulletin / PIB | pdf | ~2 wks after month-end |
| EPFO net payroll additions | M | EPFO / PIB | pdf | ~2-month lag; heavily revised |

### Energy & Infrastructure
| Series | Freq | Source | Access | Release |
|---|---|---|---|---|
| Electricity generation | D | Grid India PSP (date-templated PDF) / CEA API on data.gov.in | api | daily |
| Peak power demand | D | Grid India / Vidyut Pravah | scrape | daily |
| Rail freight loading | M | Railways / PIB | scrape | early month |
| Major-port cargo | M | MoPSW PDF (12 major ports only) | pdf | early month |

### Round-2 additions (14 series, added to the categories above)
| Series | Category | Freq | Source | Access | Release |
|---|---|---|---|---|---|
| Inflation expectations (households, 1Y) | Prices | B | RBI IES | file | with MPC |
| Capacity utilisation (OBICUS) | Output | Q | RBI survey | file | with MPC |
| Consumer confidence (CSI) | Output | B | RBI CCS | file | with MPC |
| Business expectations (IOS) | Output | Q | RBI IOS | file | with MPC |
| Central govt capex (FYTD) | Fiscal | M | CGA monthly accounts | file | last working day |
| Services exports | External | M | RBI monthly PR | scrape | ~1-month lag |
| WALR on fresh loans | Money & Banking | M | RBI lending-rate data | file | ~1-month lag |
| GNPA ratio (banks) | Money & Banking | H | RBI Financial Stability Report | pdf | Jun & Dec |
| CV retail sales | Consumption | M | FADA / Vahan | scrape | ~5th–7th |
| Gold demand (India) | Consumption | Q | World Gold Council | scrape | ~1-month lag |
| Wireless subscriber net adds | Consumption | M | TRAI | file | ~2-month lag |
| Kharif/Rabi sowing acreage | Rural & Agri | W | Dept. of Agriculture | scrape | Friday, in season |
| Labour force participation rate | Employment | M | MoSPI PLFS bulletin | pdf | with PLFS UR |
| Coal production | Energy & Infra | M | Ministry of Coal / PIB | scrape | 1st week |

Frequency legend addition: **B** bi-monthly (RBI survey rounds, aligned to MPC) · **H** half-yearly (FSR).

### Round-3 restructure (CIO review)

**Benched** (redundant or unautomatable; kept in this doc for reference, removed from the build):
e-way bills, rail freight, major-port cargo, fertiliser sales.

**Added — Deal Environment (5):** Nifty 50, Nifty P/E (trailing), India VIX, IPO+QIP issuance
(SEBI), AAA 3Y corporate spread (FIMMDA). (PE-VC deal value was added then dropped on review —
paid source, low incremental signal.)

**Added — Global Context (6):** Brent crude, broad dollar index, US 10Y, Fed funds target,
US CPI, global composite PMI — all free via FRED API except the PMI headline.

**Composite indices (4, derived):** Rural Demand, Urban Discretionary, Capex Cycle and
Financial Conditions — equal-weight z-score composites on a 10-year monthly grid,
recomputed each refresh.

**Presentation logic:** 8-series headline strip + auto-generated "What changed" bullets
(top 12-period z-moves) + category pulse board (YoY heatmap chips). Seasonal series lead
with YoY and de-emphasize MoM. Structurally trending series replace the 10-yr-average row
with "YoY growth vs 3-yr trend CAGR". Revision-prone series carry a "revises" badge.
Every tile drills down to full history with per-series CSV export; a global CSV exports
everything. `pipeline/alerts.py` holds threshold rules (Slack webhook); `make_edition.py`
generates the dated one-page edition for partner distribution.

Current universe: **70 series + 4 composites** (incl. derived monthly FII/DII rollups).

### Round-4: live wiring + presentation (verified from the build environment)

**LIVE via MoSPI eSankhyiki API (unauthenticated, verified July 2026):** CPI headline and
CFPI (`getCPIIndex` with `state="All India"`, `limit` param raises the 10-row cap; latest
exposed print Dec 2025 — the 2024-base 2026 series is not in the API yet), WPI (`getWpiRecords`
returns index levels; YoY computed in the fetcher with a base-jump guard), IIP
(`getIIPMonthly`, `growth_rate` field direct, base 2022-23, history from FY21). NAS endpoint
responds (`series="Current"` casing matters) — GDP/PFCE wiring needs indicator-code mapping,
scaffolded. FRED is network-blocked from the build sandbox; the fetcher ships ready and goes
live on firm infrastructure (fredgraph.csv needs no API key).

**Presentation:** daily FII/DII are compact number tiles; monthly FII/DII are derived series
(calendar-month sums of the daily tape, current month = MTD). Nifty, repo rate, 10Y G-sec and
INR/USD render as wide tiles with 1D/5D/1M/6M/1Y/2Y/3Y/5Y/10Y period toggles; every drill-down
modal has the same toggles. Live tiles show a green LIVE stamp; sample tiles remain flagged.

---

## 3. Source access — what we verified

**MoSPI eSankhyiki API (`api.mospi.gov.in`) is the backbone.** Official REST API (beta):
signup → login → ~30-min bearer token; JSON/CSV out. Endpoints: `/api/cpi/getCPIIndex`,
`/api/wpi/getWpiRecords`, `/api/iip/getIIPMonthly`, `/api/nas/getNASData` (PFCE lives on the
expenditure side of NAS). An official MCP server also exists (`mcp.mospi.gov.in`,
`github.com/nso-india/esankhyiki-mcp`). Verify the new-base series are exposed (see §7).

**RBI has no public API.** DBIE moved to `data.rbi.org.in/DBIE/` (11,000+ series,
Excel/CSV downloads, no documented REST). Practical paths: scrape the Weekly Statistical
Supplement tables (reserves, M3, credit), download the monthly Excel files (card spends,
sectoral credit, Payment System Indicators for UPI), parse the daily MMO press release
(liquidity). RBI is the single biggest engineering line-item.

**NSE requires the cookie dance.** Akamai bot protection; prime a session on the homepage,
reuse cookies, throttle, refresh on 401 — use a maintained wrapper (`nsepython`,
`jugaad-data`). Datacenter IPs are often blocked: run this fetcher through a proxy or a
small India-region VM. NSDL's FPI page is plain ASP.NET — parse the HTML table (VIEWSTATE
post-back only needed for historical ranges).

**Three different "FII" numbers exist.** NSDL provisional flows ≠ NSE cash-segment
provisional ≠ SEBI monthly AUC. Pick one per chart and label it (we use NSDL as canonical).

**data.gov.in is supplementary, not a backbone.** Real keyed REST API
(`api.data.gov.in/resource/{uuid}?api-key=…`), but it's a dataset *catalog* — many macro
resources are stale snapshots. Reliable there: CEA power, DGCA air traffic, MGNREGA.

**PDF sources need a parsing chain.** GST (detailed monthly PDF on gst.gov.in since the PIB
release was discontinued Aug 2024), trade, EPFO, PLFS, core-8, PPAC, ports, CWC. Chain:
camelot(lattice) → camelot(stream) → pdfplumber; snapshot every raw file to object storage
before parsing so a broken parser never loses data. FADA/MoSPI/EPFO URLs carry random hash
prefixes — discover each month's link from the listing page, never hard-code.

**Paywalled (excluded from v1):** SIAM granular auto data (₹47k–61k/product/yr), PMI
sub-indices (LSEG/Haver/Bloomberg), CMIE (largely redundant now that PLFS is monthly),
DGCIS bulk trade (₹3.5 lakh/yr). Free substitutes used: FADA/Vahan retail for autos, PMI
headline, PLFS/EPFO for jobs, PIB headline trade.

---

## 4. Architecture

```
 fetchers (per source)          storage                    serving
 ──────────────────────         ───────────────────        ─────────────────────
 eSankhyiki API  ─┐                                        dashboard.html
 data.gov.in API ─┤   raw snapshots → S3/GCS               (self-contained page,
 RBI Excel/WSS   ─┼─► observations → Postgres         ┌──► rebuilt each refresh)
 NSDL/NSE scrape ─┤   (series_id, period, value,      │
 PDF extractors  ─┘    vintage_date) + metadata       ├──► Metabase (BI portal,
                                │                     │    SSO, analyst self-serve)
                      transforms (dbt/DuckDB):        │
                      monthly rollups, MoM/YoY,  ─────┘
                      12-period avg, 3MMA
```

The dashboard never touches a source directly — it reads only the computed tables, so a
government site being down never breaks the morning view; the series just shows as stale in
the freshness panel.

**Refresh model** (release-calendar-driven, not blind polling):
daily batch at ~19:45 IST (FII, DII, FX, yields, liquidity, power) + 09:15 IST (overnight
prints); weekly Friday-night job (reserves, WSS); monthly jobs pinned to each release day
(GST 1st, PMI 1st/3rd, FADA ~5th, CPI 12th, WPI 14th, trade 15th, IIP 28th, core-8 & CGA
month-end) that poll every ~15 min until the new print lands, then stop. Every run re-pulls
recent periods to catch revisions. Optional Slack/email alert on key prints.

**Orchestration:** GitHub Actions cron now (see `.github/workflows/refresh.yml`); graduate
to Prefect when dependencies multiply. Skip Airflow. **Storage:** Postgres (long/tidy
schema + vintages); DuckDB/dbt for transforms; hundreds of series at this cadence needs no
warehouse. **Serving:** the generated page for the tracker itself; Metabase on Postgres for
ad-hoc exploration; behind SSO/VPN.

---

## 5. Phased build

**Phase 1 (prototype — done).** 61-series catalog, comparison engine (prev / LY / 12-period
avg), self-contained dashboard page, refresh scaffold. Sample data flagged per-tile.

**Phase 2 (first live data, ~easiest 60%).** Wire: eSankhyiki (CPI/WPI/IIP/GDP/PFCE),
data.gov.in (power, air pax, MGNREGA), RBI file downloads (cards, UPI/PSI, sectoral credit),
NSDL FII, FBIL yields/FX, AMFI. Stand up Postgres + vintage tracking.

**Phase 3 (the scrape/PDF pack).** GST, trade, EPFO, PLFS, core-8, CGA .xlsm, FADA, TMA,
PPAC, ports, rail, WSS (reserves/M3/credit), IMD, CWC, fertiliser. NSE DII via wrapper +
non-datacenter egress.

**Phase 4 (production hardening).** Metabase + SSO, alerting on prints and on fetcher
failures, release-calendar table maintained a quarter ahead, runbook for scraper breakage.

**Operating model options.** (a) Scheduled Cowork session runs the refresh daily and
republishes the page — zero infrastructure, fine for v1. (b) GitHub repo + Actions cron +
internal hosting — the production home; the code in this folder moves over unchanged.

---

## 6. Make vs buy

DBnomics (free aggregator) already carries MOSPI national-accounts series and IMF/WB India
cuts — use it to skip some scrapers. If the firm prefers to buy the pipeline outright:
Trading Economics API (~$199/mo, call-capped) at the low end; CEIC India Premium or CMIE
Economic Outlook (both enterprise-priced, India-deep) replace most ingestion, leaving only
the dashboard to build. The DIY pipeline earns its keep through zero marginal data cost,
series not sold commercially (Vahan cuts, e-way bills), and control of timing/vintages.

---

## 7. Known risks & watch-items

Base-year changes landed across H1 2026 (CPI 2024=100; WPI 2022-23=100 + new PPI; GDP
2022-23; IIP 2022-23 from 1 Jun 2026) — historical splices are not clean; store both bases.
eSankhyiki is beta (auth/rate limits may shift). NSE anti-bot changes without notice —
keep the wrapper library updated. GST/PIB publication formats have changed once already
(Aug 2024) and can again. PMI redistribution is IP-restricted even at headline level —
keep the dashboard internal. EPFO/Vahan revise heavily — always show vintage-aware YoY.
