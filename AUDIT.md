# AUDIT LOG

## Seeded / fetched series (contract lines)

| series_id | latest period | value | source URL | how verified |
|---|---|---|---|---|
| gdp | Q4 FY26 (Jan-Mar 2026) | 7.8 % YoY | https://api.mospi.gov.in/api/nas/getNASData (indicator_code=5) | YoY computed from constant-price levels, new 2022-23 base; matches PIB press note PRID 2269286 ("Q4 grew 7.8%", FY26 7.7%) and multibagg.ai coverage; Q3 FY26 8.0% matches post-PE revision ("revised to around 8%") |
| pfce | Q4 FY26 (Jan-Mar 2026) | 7.1 % YoY | https://api.mospi.gov.in/api/nas/getNASData (indicator_code=10) | Same official payload as gdp (GDP levels reproduce official prints exactly); implied FY26 annual PFCE 7.75% consistent with press coverage "PFCE ... exceeding 7.5 percent in FY26" (thebridgechronicle.com) |
| core8 | May 2026 | 0.5 % YoY | https://eaindustry.nic.in/eight_core_infra/Core_Industries_2011_12_20260622.xlsx | Official OEA time-series workbook (base 2011-12), 'Growth (%)' sheet, 170 monthly obs from Apr 2012; workbook is the OEA's own release, cross-checked against PIB core-industries release cadence |
| us_cpi | May 2026 | 4.2 % YoY | https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0 | YoY computed from official BLS CPI-U NSA index; matches CNBC "Prices rose 4.2% annually" (May 2026 CPI report). Oct 2025 missing at source (shutdown data lapse) — month skipped |
| fedfunds | Jun 2026 | 3.75 % (target upper) | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm | SEEDED (30 monthly obs from Jan 2024) from FOMC decision history: cuts Sep/Nov/Dec 2024 to 4.50; holds to Sep 2025; cuts Sep/Oct/Dec 2025 to 3.50-3.75; held since (4 consecutive holds, 17 Jun 2026 statement; advisorperspectives.com dshort recap) |
| brent | 2026-07-08 | 75.80 US$/bbl | https://query1.finance.yahoo.com/v8/finance/chart/BZ=F | Yahoo chart API daily closes (252 obs, 1y); FRED blocked, stooq denies CSV. BZ=F front-month as spot proxy; level consistent with WPI release commentary of a 2026 crude price surge |
| dxy | 2026-07-08 | 100.96 index | https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB | Yahoo chart API (252 obs); classic ICE DXY (catalog info prefers FRED broad TWI — unavailable; noted in fetcher docstring) |
| ust10y | 2026-07-07 | 4.53 % | https://query1.finance.yahoo.com/v8/finance/chart/^TNX | Yahoo chart API (251 obs). NOTE: Yahoo returns ^TNX as yield in % directly (not x10) — verified vs meta regularMarketPrice 4.529 |

## Part B — accuracy audit of pre-existing live files (2026-07-08)

### wpi.json — SPECIAL CHECK on Apr 2026 "8.3%": CONFIRMED GENUINE, not a base artifact
- Official OEA/PIB April 2026 release (base 2011-12, PRID 2260905): "annual rate of inflation ... stood at 8.3% (provisional) in April 2026", index 167.0. The API-derived 8.3 is EXACTLY the official print. The surge is real: WPI accelerated on a crude-petroleum price shock (March release cites crude petroleum +49.1% MoM; Fuel & Power +4.13% MoM).
- May 2026 (released 15 Jun 2026 with the NEW 2022-23=100 base, linking factor 1.53): official YoY 9.68% (aninews.in; new-base index 109.9). APPENDED ["2026-05-01", 9.68] to wpi.json (hand-transcribed; API still serves old base).
- Back months vs official: Jan 1.68 = final ✓ (Mar release), Feb 2.26 = FINAL ✓ (Apr release: "final ... 158.4 and 2.26%"; the 2.13% provisional print was superseded), Mar 3.88 ✓ (PRID 2252109), Sep 0.19 = final ✓ (Nov release). Nov -0.13 / Dec 0.96 differ from provisional prints (-0.32 / 0.83) — consistent with the API carrying FINAL revised indices; pattern verified on Sep/Jan/Feb finals. VERDICT: wpi.json accurate (final-revision basis); no overwrites needed.

### cpi.json / cfpi.json — ACCURATE but were 5 months STALE; gap filled
- Dec 2025: CPI 1.33 ✓, CFPI -2.71 ✓; Nov: 0.71 / -3.91 ✓ (PIB PRID 2213736, exact quotes). Jul-Oct 2025 values match official revised prints (e.g. Oct CPI 0.25 ✓).
- Files ended Dec 2025 because the eSankhyiki CPI API does not yet expose the new 2024=100 base (per esankhyiki.py docstring). Jan-May 2026 official prints APPENDED from PIB releases (PRID 2238889 Feb, 2251519 Mar, 2272112 May): CPI 2.74, 3.21, 3.40, 3.48 (final), 3.93 (prov); CFPI 2.13, 3.47, 3.87, 4.20 (final), 4.78 (prov). Jun 2026 CPI due ~13 Jul 2026.

### iip.json — ACCURATE on the new-base series
- May 2026 5.1 ✓ (PIB PRID 2278961 "growth of 5.1% in May 2026"), Apr 2026 4.9 ✓ (PRID 2267531, FIRST release of new 2022-23-base series). Feb file 5.1 vs old-base print 5.2, Mar file 3.0 vs old-base print ~4.1: pre-April 2026 months in the API are the NEW-base back-series (published "from April 2023 onwards" on eSankhyiki), which restates old-base prints — this is the current official series, not an error. Values before Apr 2023 in iip.json are old-base (spliced).

### fii.json — PLAUSIBLE, cannot exactly verify; coverage thin
- Single obs 2026-07-07 = +848.33 ₹ cr (NSDL). Direction/magnitude consistent with independent NSE cash provisional data (+243 cr FII on Jul 6, FIIs net buyers since late June — business-standard.com, niftytrader.in). NSDL includes primary market, so it will not equal NSE cash figures. NSDL site itself served a stale cached page (23-Jun-2025) via fetch, so exact same-day cross-check unavailable. FLAG: only 1 observation — below the 14-obs contract minimum; daily-tape backfill needed (other workstream).

### Catalog sample-base sanity (pipeline/catalog.py `base=` values) vs mid-2026 reality — FLAGS ONLY, catalog not edited
| series | catalog base | actual (Jul 2026) | source | verdict |
|---|---|---|---|---|
| inrusd | 87.4 | ~95.2 | Yahoo INR=X 95.18 (2026-07-08) | FAR OFF — update sample base |
| nifty | 26400 | ~24,226-24,452 | Yahoo ^NSEI; niftytrader.in | ~8% high — update |
| gsec10y | 6.32 | ~6.73-6.84 | univest.in / whalesbook (Jun 2026) | ~45bp low — update |
| ust10y | 4.15 | 4.53 | Yahoo ^TNX (now live) | ~38bp low |
| dxy | 97.0 | ~101 | Yahoo DX-Y.NYB (now live) | ~4pt low |
| brent | 68.0 | ~74-76 | Yahoo BZ=F (now live) | low |
| us_cpi | 2.6 | 4.2 | BLS/CNBC (now live) | FAR OFF |
| fedfunds | 3.60 | 3.75 | Fed statement 17 Jun 2026 (now live) | off; also 3.60 is not a valid target-range upper bound |
| wpi | 1.8 | 9.68 | PIB (now live) | FAR OFF (2026 crude shock) |
| repo | 5.25 | 5.25 | icfmindia/cleartax MPC coverage | OK ✓ |
| fx_reserves | 702 | ~698-700+ | ddnews.gov.in weekly RBI data | OK ✓ |

### Corrections to the two audit rows above (post-parallel-workstream data landing)
- fx_reserves: catalog base 702 is ~US$35bn HIGH vs the live RBI WSS series now in data/live/fx_reserves.json (latest 2026-06-26 = 666.93 US$ bn). The DD News "crosses $700bn" item used above was from an earlier period. FLAG: update sample base (~667).
- fii.json: backfilled to 64 daily obs by the flows workstream while this audit ran; latest 2026-07-07 = +848.33 ₹ cr unchanged and consistent with the checks above. The "below 14-obs minimum" flag is resolved.
