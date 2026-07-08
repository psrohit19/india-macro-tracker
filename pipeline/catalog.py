"""
Series catalog for the India Macro Tracker.

Every series the dashboard shows is declared here, with:
  - id / name / category / unit
  - freq: D (daily), W (weekly), F (fortnightly), M (monthly), B (bi-monthly),
          Q (quarterly), H (half-yearly)
  - agg: monthly rollup rule ("sum" flow, "last" stock/month-end, "mean", "max")
  - up_is_good: True if an increase is a positive signal (colors the deltas)
  - kind: "level" (delta = % change) | "rate" (delta = pp/bps) | "flow" (absolute)
  - source / url / access / release: provenance & timing (url must be clickable)
  - info: dict(what=..., changes=...) shown behind the tile's ⓘ button
      what    — what the indicator measures and how it is calculated
      changes — recent methodology/release changes to be aware of

The fetchers in pipeline/fetchers/ each populate one or more of these ids.
"""

CATEGORIES = [
    "Composite Signals",
    "Prices & Inflation",
    "Output & Activity",
    "Fiscal",
    "External Sector",
    "Flows & Markets",
    "Deal Environment",
    "Global Context",
    "Money, Credit & Banking",
    "Consumption & Demand",
    "Rural & Agri",
    "Employment",
    "Energy & Infrastructure",
]

SERIES = [
    # ---------------- Prices & Inflation ----------------
    dict(id="cpi", name="CPI inflation", category="Prices & Inflation",
         unit="% YoY", freq="M", agg="last", up_is_good=False, kind="rate",
         base=3.2, vol=0.25, source="MoSPI (eSankhyiki API)", access="api",
         url="https://cpi.mospi.gov.in/", release="12th, 4:00 pm",
         info=dict(
             what="Consumer Price Index (Combined): YoY change in the retail price of a fixed household consumption basket, weighted across rural and urban India. Computed by NSO/MoSPI from ~2.9 lakh monthly price quotations; published as Rural / Urban / Combined with group-level sub-indices.",
             changes="Rebased to 2024=100 from the Jan 2026 release (was 2012=100): basket widened to 358 items and the Food & Beverages weight cut to ~36.75%, mechanically lowering headline sensitivity to food. First prints are provisional and revised ~2 months later; the back-series splice to the old base is not clean.")),
    dict(id="cpi_core", name="Core CPI", category="Prices & Inflation",
         unit="% YoY", freq="M", agg="last", up_is_good=False, kind="rate",
         base=4.0, vol=0.15, source="MoSPI (derived)", access="api",
         url="https://cpi.mospi.gov.in/", release="12th, with CPI",
         info=dict(
             what="CPI excluding the volatile Food & Beverages and Fuel & Light groups — the underlying, demand-driven inflation trend. Derived by re-weighting the remaining CPI groups; not separately published by MoSPI, so analysts compute it from the group indices.",
             changes="Inherits the CPI 2024=100 rebasing. With the food weight cut in the new base, headline and core converge faster than under the old series; core definitions vary slightly across brokers (some also exclude petrol/diesel within transport), so keep the definition fixed in this tracker.")),
    dict(id="cfpi", name="Food inflation (CFPI)", category="Prices & Inflation",
         unit="% YoY", freq="M", agg="last", up_is_good=False, kind="rate",
         base=2.4, vol=0.6, source="MoSPI (eSankhyiki API)", access="api",
         url="https://cpi.mospi.gov.in/", release="12th, with CPI",
         info=dict(
             what="Consumer Food Price Index: YoY change in the food sub-basket of the CPI (cereals, vegetables, pulses, milk, etc.). The swing factor of Indian headline inflation and a direct read on rural household budgets.",
             changes="Rebased with CPI to 2024=100 in Jan 2026; vegetable and cereal weights changed with the new consumption survey, so YoY comparisons across the base switch need care.")),
    dict(id="wpi", name="WPI inflation", category="Prices & Inflation",
         unit="% YoY", freq="M", agg="last", up_is_good=False, kind="rate",
         base=1.8, vol=0.4, source="OEA / eSankhyiki API", access="api",
         url="https://eaindustry.nic.in/", release="14th",
         info=dict(
             what="Wholesale Price Index: YoY change in prices at first bulk sale, compiled by the Office of the Economic Adviser (DPIIT) across Primary Articles, Fuel & Power and Manufactured Products. A proxy for producer/input-cost inflation; no rural/urban split.",
             changes="Rebased to 2022-23=100 from 15 Jun 2026 (was 2011-12); basket widened 697→957 items. A new Producer Price Index (PPI) launched alongside and is slated to replace WPI over ~5 years — this tracker will migrate when the PPI series stabilizes.")),

    # ---------------- Output & Activity ----------------
    dict(id="iip", name="IIP growth", category="Output & Activity",
         unit="% YoY", freq="M", agg="last", up_is_good=True, kind="rate",
         base=4.2, vol=0.8, source="MoSPI (eSankhyiki API)", access="api",
         url="https://www.mospi.gov.in/iip", release="28th, 4:00 pm",
         info=dict(
             what="Index of Industrial Production: YoY growth in physical output across mining, manufacturing and electricity, weighted by value-added; also published by use-based category (capital goods, consumer durables, etc.). Compiled by NSO from ~4,000 reporting factories.",
             changes="Release moved to the 28th of each month with a 28-day lag from April 2025 (previously the 12th, 42-day lag) — it no longer co-releases with CPI. Rebasing from 2011-12=100 to 2022-23=100 scheduled from 1 Jun 2026. Quick Estimates are revised once, in the Final Estimate.")),
    dict(id="core8", name="Eight core industries", category="Output & Activity",
         unit="% YoY", freq="M", agg="last", up_is_good=True, kind="rate",
         base=3.8, vol=0.9, source="OEA / PIB (PDF)", access="pdf",
         url="https://eaindustry.nic.in/", release="Last working day",
         info=dict(
             what="Index of Eight Core Industries: coal, crude oil, natural gas, refinery products, fertilizers, steel, cement and electricity — 40.27% of the IIP by weight. Compiled by the OEA; releases one month ahead of IIP, making it the standard early proxy.",
             changes="Still on the 2011-12=100 base as of mid-2026 (rebasing pending), so it sits on an older base than the new IIP — growth rates across the two won't reconcile exactly. Provisional prints get two scheduled revisions (1st and 3rd following month).")),
    dict(id="pmi_mfg", name="Manufacturing PMI", category="Output & Activity",
         unit="index", freq="M", agg="last", up_is_good=True, kind="level",
         base=57.6, vol=0.7, source="S&P Global (headline, free)", access="scrape",
         url="https://www.pmi.spglobal.com/Public/Release/PressReleases", release="1st business day",
         info=dict(
             what="HSBC India Manufacturing PMI (compiled by S&P Global): diffusion index from a ~400-firm purchasing-manager survey; 50 = no change, above 50 = expansion. Seasonally adjusted; leads official IIP by 1–2 months.",
             changes="Proprietary series — only the headline number and commentary are free; sub-indices (new orders, prices, employment) require a licensed feed (LSEG/Haver). Sponsor renamed from HSBC branding continuity in 2024; methodology itself unchanged. Redistribution is IP-restricted — keep internal.")),
    dict(id="pmi_svc", name="Services PMI", category="Output & Activity",
         unit="index", freq="M", agg="last", up_is_good=True, kind="level",
         base=59.1, vol=0.8, source="S&P Global (headline, free)", access="scrape",
         url="https://www.pmi.spglobal.com/Public/Release/PressReleases", release="3rd business day",
         info=dict(
             what="HSBC India Services PMI Business Activity Index: diffusion index from a services-firm panel; 50 = no change. Released with the Composite PMI on the third business day.",
             changes="Same access model as Manufacturing PMI: free headline only, licensed sub-indices, IP-restricted redistribution. A flash estimate (~third-to-last business day of the reference month) now precedes the final print.")),
    dict(id="gdp", name="Real GDP growth", category="Output & Activity",
         unit="% YoY", freq="Q", agg="last", up_is_good=True, kind="rate",
         base=6.8, vol=0.3, source="MoSPI NAS (eSankhyiki API)", access="api",
         url="https://www.mospi.gov.in/", release="End Feb/May/Aug/Nov",
         info=dict(
             what="Real Gross Domestic Product, YoY growth at constant prices, from the National Accounts (NSO). Production side is GVA by industry plus net indirect taxes; released ~2 months after each quarter.",
             changes="Major base revision to 2022-23 first published 27 Feb 2026 (was 2011-12): double deflation, Supply-Use Table framework, GST/PFMS/PLFS source data. Each year's number is revised over ~3 subsequent years (PE→FRE→SRE), so treat every print as provisional.")),
    dict(id="pfce", name="PFCE growth", category="Output & Activity",
         unit="% YoY", freq="Q", agg="last", up_is_good=True, kind="rate",
         base=6.1, vol=0.4, source="MoSPI NAS, expenditure side", access="api",
         url="https://www.mospi.gov.in/", release="With GDP",
         info=dict(
             what="Private Final Consumption Expenditure: household (plus NPISH) consumption at constant prices from the expenditure side of the National Accounts — the broadest official measure of consumer demand (~60% of GDP).",
             changes="Rebased with GDP to 2022-23 (Feb 2026) with a revised PFCE estimation methodology drawing on the 2022-24 consumption surveys. Expenditure-side components are statistically weaker than production-side GVA and revise heavily — read levels with the discrepancy term in mind.")),

    # ---------------- Fiscal ----------------
    dict(id="gst", name="Gross GST collections", category="Fiscal",
         unit="₹ lakh cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=2.02, vol=0.05, source="gst.gov.in (monthly PDF)", access="pdf",
         url="https://www.gst.gov.in/newsandupdates", release="1st of month",
         info=dict(
             what="Gross GST revenue collected in the month (CGST + SGST + IGST + cess), before refunds; reported with state-wise splits. A same-month read on nominal transaction activity across the formal economy.",
             changes="The detailed PIB press release was discontinued from Aug 2024; the release now appears as a structured PDF on the GST portal around the 1st. Watch gross vs net (post-refund) — headlines mix them. Rate rationalization episodes distort YoY comparisons.")),
    dict(id="fisc_def", name="Fiscal deficit (FYTD, % of BE)", category="Fiscal",
         unit="% of BE", freq="M", agg="last", up_is_good=False, kind="level",
         base=37.0, vol=6.0, trend=6.0, source="CGA (.xlsm dashboard)", access="file",
         url="https://cga.nic.in/MonthDashboardReport/Published/list.aspx", release="Last working day",
         info=dict(
             what="Union government fiscal deficit, fiscal-year-to-date, expressed as % of the Budget Estimate — from the CGA's monthly accounts (receipts, expenditure, borrowings). The denominator comes from the Union Budget.",
             changes="Figures are cumulative from April — single-month flows require differencing consecutive prints. Data is provisional until the Provisional Accounts (~31 May) and final CAG-audited accounts. The CGA dashboard is a macro-enabled Excel workbook — the most machine-readable fiscal source.")),

    # ---------------- External Sector ----------------
    dict(id="exports", name="Merchandise exports", category="External Sector",
         unit="US$ bn", freq="M", agg="last", up_is_good=True, kind="level",
         base=38.5, vol=1.6, source="Commerce / PIB (~15th)", access="pdf",
         url="https://tradestat.commerce.gov.in/", release="~15th",
         info=dict(
             what="Monthly merchandise export value in US$ from DGCI&S customs data, released by the Commerce Ministry ~15th with commodity and destination detail on TRADESTAT.",
             changes="First prints are provisional and revised in later months (sometimes materially — gold/petroleum reclassifications have moved past months by >$1bn). Services trade is a separate, RBI-estimated release.")),
    dict(id="imports", name="Merchandise imports", category="External Sector",
         unit="US$ bn", freq="M", agg="last", up_is_good=False, kind="level",
         base=61.8, vol=2.2, source="Commerce / PIB (~15th)", access="pdf",
         url="https://tradestat.commerce.gov.in/", release="~15th",
         info=dict(
             what="Monthly merchandise import value in US$ (DGCI&S customs data). Oil, gold and electronics dominate swings; non-oil-non-gold imports are the cleaner domestic-demand read.",
             changes="Same revision caveats as exports. 'Up is bad' here is a simplification — rising imports can also signal strong domestic demand; read alongside the trade deficit and non-oil-non-gold cut.")),
    dict(id="trade_def", name="Trade deficit", category="External Sector",
         unit="US$ bn", freq="M", agg="last", up_is_good=False, kind="level",
         base=23.3, vol=1.8, source="Commerce / PIB (~15th)", access="pdf",
         url="https://tradestat.commerce.gov.in/", release="~15th",
         info=dict(
             what="Merchandise imports minus exports (US$ bn). The monthly goods gap that, net of the services surplus and remittances, drives the current account.",
             changes="Revisions to either leg move the deficit; the services surplus (published separately by RBI) has grown enough that the goods deficit alone overstates external stress.")),
    dict(id="fx_reserves", name="Forex reserves", category="External Sector",
         unit="US$ bn", freq="W", agg="last", up_is_good=True, kind="level",
         base=702.0, vol=3.5, source="RBI WSS (Friday)", access="scrape",
         url="https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2", release="Friday ~5 pm (weekly)",
         info=dict(
             what="RBI's foreign exchange reserves (foreign currency assets, gold, SDRs, IMF reserve tranche), published every Friday for the week ended the previous Friday.",
             changes="Weekly changes conflate intervention with valuation effects — FCA is USD-expressed but holds non-USD assets, so EUR/JPY moves and gold prices swing the headline without any RBI action. Read alongside forward-book data (monthly bulletin) for true intervention.")),

    # ---------------- Flows & Markets ----------------
    dict(id="fii", name="FPI net flows (equity)", category="Flows & Markets",
         unit="₹ cr", freq="D", agg="sum", up_is_good=True, kind="flow",
         base=250, vol=4500, source="NSDL FPI Monitor", access="scrape",
         url="https://www.fpi.nsdl.co.in/Reports/Latest.aspx", release="Daily, EOD",
         info=dict(
             what="Net foreign portfolio investment in Indian equities (buy minus sell, ₹ crore), from NSDL custody data — the market-standard daily FPI flow series, also published in US$ with debt/hybrid splits.",
             changes="Three different 'FII' numbers exist: NSDL flows (used here, includes primary market), NSE cash-segment provisional, and SEBI monthly AUC — they rarely match; don't mix definitions. Daily prints are provisional. Debt flows split across FAR/VRR/general limits since the index-inclusion reforms.")),
    dict(id="dii", name="DII net flows", category="Flows & Markets",
         unit="₹ cr", freq="D", agg="sum", up_is_good=True, kind="flow",
         base=2600, vol=3000, source="NSE (fiidiiTradeReact)", access="scrape",
         url="https://www.nseindia.com/reports/fii-dii", release="Daily, ~6 pm",
         info=dict(
             what="Net purchases by Domestic Institutional Investors — mutual funds, insurers, banks and DFIs combined — in the cash market (₹ crore), published by NSE each evening.",
             changes="Provisional same-evening figure, finalized next morning; no daily breakdown of the MF vs insurance mix (only SEBI/AMFI monthly data splits it). The steady SIP bid means DII flows are structurally positive — compare to trend, not zero.")),
    dict(id="fii_m", name="FPI net flows (monthly)", category="Flows & Markets",
         unit="₹ cr", freq="M", agg="last", up_is_good=True, kind="flow",
         base=0, vol=0, derive_sum_from="fii", source="NSDL (monthly rollup)", access="scrape",
         url="https://www.fpi.nsdl.co.in/Reports/Latest.aspx", release="Derived from daily",
         info=dict(
             what="Calendar-month sum of NSDL daily FPI equity net flows (₹ crore) — the monthly view of foreign positioning; smoother and more decision-relevant than the daily tape. The current month accumulates as days land.",
             changes="Derived series: exactly the daily NSDL numbers bucketed by month, so it inherits the NSDL-vs-NSE-vs-SEBI definitional caveats. The in-progress month is month-to-date, not a full month — compare completed months for YoY.")),
    dict(id="dii_m", name="DII net flows (monthly)", category="Flows & Markets",
         unit="₹ cr", freq="M", agg="last", up_is_good=True, kind="flow",
         base=0, vol=0, derive_sum_from="dii", source="NSE (monthly rollup)", access="scrape",
         url="https://www.nseindia.com/reports/fii-dii", release="Derived from daily",
         info=dict(
             what="Calendar-month sum of NSE daily DII net flows (₹ crore) — mutual funds, insurers, banks and DFIs combined. The structural domestic bid, best read monthly against SIP inflows.",
             changes="Derived from the daily provisional NSE figures; small gaps vs the finalized monthly numbers are expected. In-progress month is month-to-date.")),
    dict(id="sip", name="SIP inflows", category="Flows & Markets",
         unit="₹ cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=28900, vol=500, source="AMFI", access="file",
         url="https://www.amfiindia.com/research-information/amfi-monthly", release="~8th–10th",
         info=dict(
             what="Monthly mutual-fund inflows via Systematic Investment Plans (₹ crore), from AMFI — the structural retail bid underpinning DII flows.",
             changes="AMFI periodically revises how it counts SIP registrations vs live accounts; the flow number itself is stable. Compare against gross equity-scheme flows to see whether lumpsum money is amplifying or offsetting the SIP trend.")),
    dict(id="gsec10y", name="10Y G-sec yield", category="Flows & Markets",
         unit="%", freq="D", agg="last", up_is_good=False, kind="rate",
         base=6.32, vol=0.05, source="FBIL / CCIL", access="file",
         url="https://www.fbil.org.in/", release="Daily, EOD",
         info=dict(
             what="Yield on the on-the-run 10-year government security (FBIL valuation benchmark) — the economy's risk-free anchor for corporate bond and loan pricing.",
             changes="The benchmark bond changes when a new 10Y is issued, creating small discontinuities vs a constant-maturity series; FBIL's valuation yield can differ a few bps from the traded level. This tracker uses the FBIL EOD series.")),
    dict(id="inrusd", name="INR / USD", category="Flows & Markets",
         unit="₹", freq="D", agg="last", up_is_good=False, kind="level",
         base=87.4, vol=0.35, source="FBIL reference rate", access="scrape",
         url="https://www.rbi.org.in/scripts/referenceratearchive.aspx", release="Daily, ~1:30 pm",
         info=dict(
             what="FBIL reference rate for the rupee vs the US dollar — a once-daily fix computed from a ~12:30 pm market snapshot and disseminated via RBI around 1:30 pm.",
             changes="It is a midday fix, not a close — the market moves after it. FBIL has computed the rate since 2018 (not RBI). 'Up is bad' = depreciation; note REER (monthly, RBI bulletin) is the better competitiveness measure.")),
    dict(id="liquidity", name="System liquidity (net LAF)", category="Flows & Markets",
         unit="₹ lakh cr", freq="D", agg="mean", up_is_good=True, kind="level",
         base=2.4, vol=0.5, source="RBI MMO (daily PR)", access="pdf",
         url="https://www.rbi.org.in/scripts/bs_viewmmo.aspx", release="Daily, next morning",
         info=dict(
             what="Net banking-system liquidity absorbed/injected via the RBI's Liquidity Adjustment Facility (repo, reverse repo, SDF, MSF, fine-tuning ops) — positive = surplus. From the daily Money Market Operations release.",
             changes="Government cash balances with the RBI are a large hidden driver — the headline LAF net can mislead around tax dates and heavy spending weeks. The 2025 CRR cuts structurally raised surplus liquidity; compare to the post-cut regime, not older history.")),

    # ---------------- Money, Credit & Banking ----------------
    dict(id="repo", name="Policy repo rate", category="Money, Credit & Banking",
         unit="%", freq="M", agg="last", up_is_good=None, kind="rate",
         base=5.25, vol=0.0, source="RBI MPC", access="scrape",
         url="https://www.rbi.org.in/scripts/annualpolicy.aspx", release="6 meetings / yr",
         info=dict(
             what="The RBI's policy repo rate, set by the six-member Monetary Policy Committee at six scheduled meetings a year; the SDF (repo−25bps) and MSF (repo+25bps) form the corridor.",
             changes="A rate-cutting cycle ran through 2025 with phased CRR reductions alongside — track the stance and CRR, not just the repo level. Direction is context-dependent (neither up nor down is unconditionally 'good'), so deltas here are shown neutral.")),
    dict(id="m3", name="M3 growth", category="Money, Credit & Banking",
         unit="% YoY", freq="F", agg="last", up_is_good=True, kind="rate",
         base=10.1, vol=0.25, source="RBI WSS (fortnightly)", access="scrape",
         url="https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2", release="Fortnightly",
         info=dict(
             what="Broad money (currency + deposits) growth YoY, from the RBI's fortnightly reporting cycle in the Weekly Statistical Supplement.",
             changes="Reporting Fridays are irregularly spaced — don't assume clean bi-weekly gaps. The HDFC twins merger (Jul 2023) distorted base effects into FY25; RBI publishes merger-adjusted growth separately.")),
    dict(id="credit", name="Bank credit growth", category="Money, Credit & Banking",
         unit="% YoY", freq="F", agg="last", up_is_good=True, kind="rate",
         base=11.6, vol=0.3, source="RBI WSS (fortnightly)", access="scrape",
         url="https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2", release="Fortnightly",
         info=dict(
             what="Scheduled commercial banks' non-food credit outstanding, YoY growth — the broadest read on bank lending to the economy. Fortnightly from the WSS; sectoral detail follows monthly.",
             changes="Use the merger-adjusted series (HDFC merger polluted unadjusted YoY well into 2024-25). Rising bank-NBFC substitution means bank credit alone understates total credit; check the monthly sectoral deployment release for the NBFC on-lending line.")),
    dict(id="deposits", name="Deposit growth", category="Money, Credit & Banking",
         unit="% YoY", freq="F", agg="last", up_is_good=True, kind="rate",
         base=10.2, vol=0.25, source="RBI WSS (fortnightly)", access="scrape",
         url="https://www.rbi.org.in/Scripts/WSSViewDetail.aspx?TYPE=Section&PARAM1=2", release="Fortnightly",
         info=dict(
             what="Scheduled commercial banks' aggregate deposits, YoY growth. The credit-deposit growth gap drives funding pressure and deposit-rate competition.",
             changes="Merger adjustment applies here too. CASA vs term-deposit mix (monthly data) matters as much as the headline — a term-deposit-led rebound carries higher funding costs.")),
    dict(id="cards", name="Credit card spends", category="Money, Credit & Banking",
         unit="₹ lakh cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=1.94, vol=0.06, source="RBI bank-wise card stats", access="file",
         url="https://www.rbi.org.in/Scripts/ATMView.aspx", release="Monthly, ~2 wk lag",
         info=dict(
             what="Total credit-card spend (POS + online) in the month, from the RBI's bank-wise ATM/POS/card statistics — the cleanest high-frequency read on urban discretionary consumption.",
             changes="RBI revamped the card-statistics format in 2023 (separating PoS vs e-commerce); series before/after need mapping. Festive-season timing shifts (Diwali month moving between Oct/Nov) swing YoY — use the 3MMA alongside.")),
    dict(id="personal_loans", name="Personal loans growth", category="Money, Credit & Banking",
         unit="% YoY", freq="M", agg="last", up_is_good=True, kind="rate",
         base=12.8, vol=0.4, source="RBI sectoral deployment", access="file",
         url="https://data.rbi.org.in/DBIE/", release="Monthly, ~1 mo lag",
         info=dict(
             what="YoY growth in banks' personal-loan book (housing, vehicle, credit card receivables, other retail) from the RBI's monthly sectoral deployment of credit release — the consumption-financing engine.",
             changes="RBI raised risk weights on unsecured retail credit (Nov 2023) and partially rolled them back in 2025 — policy-driven kinks in the series are regulatory, not demand, signals. Sectoral data covers ~95% of bank credit, excludes NBFC lending.")),

    # ---------------- Consumption & Demand ----------------
    dict(id="pv", name="PV retail sales (4W)", category="Consumption & Demand",
         unit="lakh units", freq="M", agg="last", up_is_good=True, kind="level",
         base=3.45, vol=0.22, source="FADA / Vahan", access="scrape",
         url="https://www.fada.in/", release="~5th–7th",
         info=dict(
             what="Passenger-vehicle retail registrations in the month, from FADA (sourced from the Vahan registration database) — actual consumer offtake, as opposed to SIAM's factory-dispatch (wholesale) numbers.",
             changes="Vahan months back-revise for weeks as RTOs enter late registrations — every recent month drifts up after first print. Coverage excludes a few non-Vahan states (Telangana historically; now integrated). The wholesale-retail gap is itself a channel-inventory signal.")),
    dict(id="tw", name="2W retail sales", category="Consumption & Demand",
         unit="lakh units", freq="M", agg="last", up_is_good=True, kind="level",
         base=14.2, vol=1.1, source="FADA / Vahan", access="scrape",
         url="https://www.fada.in/", release="~5th–7th",
         info=dict(
             what="Two-wheeler retail registrations (FADA/Vahan) — the classic mass-market and rural-adjacent demand barometer.",
             changes="Same Vahan back-revision caveat as PV. EV two-wheelers are included; subsidy-scheme changes (FAME→EMPS→PM E-DRIVE transitions) create policy-driven monthly spikes around deadline months.")),
    dict(id="tractors", name="Tractor sales", category="Consumption & Demand",
         unit="'000 units", freq="M", agg="last", up_is_good=True, kind="level",
         base=81.0, vol=9.0, source="TMA + M&M/Escorts filings", access="scrape",
         url="https://www.tmaindia.in/", release="1st (cos), mid-month (TMA)",
         info=dict(
             what="Monthly tractor sales — industry aggregate from the Tractor and Mechanization Association (dispatches), cross-checked with M&M and Escorts Kubota monthly exchange filings (1st of month). The single best rural capex/sentiment proxy.",
             changes="TMA reports dispatches, Vahan/FADA report registrations — timing differs by weeks around season starts. TAFE (unlisted) doesn't disclose monthly, so company-filings coverage is ~60% of the market; TMA fills the gap with a lag.")),
    dict(id="upi", name="UPI transaction value", category="Consumption & Demand",
         unit="₹ lakh cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=26.5, vol=0.7, source="NPCI / RBI PSI (xlsx)", access="file",
         url="https://www.npci.org.in/what-we-do/upi/product-statistics", release="1st–3rd",
         info=dict(
             what="Total value of UPI transactions in the month (NPCI). Tracks the digitization of payments as much as consumption itself — best read as trend and YoY rather than level.",
             changes="NPCI robots-blocks scraping; the RBI Payment System Indicators xlsx is the stable machine-readable mirror. P2P vs P2M split matters for the consumption read (P2M is the spend signal) — NPCI publishes it separately.")),
    dict(id="fuel", name="Petroleum consumption", category="Consumption & Demand",
         unit="MMT", freq="M", agg="last", up_is_good=True, kind="level",
         base=20.6, vol=0.7, source="PPAC (PDF)", access="pdf",
         url="https://ppac.gov.in/", release="Mid–late month",
         info=dict(
             what="Total petroleum-product consumption (petrol, diesel, LPG, ATF, etc.) from PPAC — diesel is the freight/economic-activity read, petrol the personal-mobility read.",
             changes="Provisional mid-month estimates precede the full monthly report; small revisions are routine. EV adoption is beginning to bend the petrol trend in metros — structural, not cyclical.")),
    dict(id="airpax", name="Domestic air passengers", category="Consumption & Demand",
         unit="lakh", freq="M", agg="last", up_is_good=True, kind="level",
         base=148.0, vol=6.0, source="DGCA / data.gov.in API", access="api",
         url="https://www.dgca.gov.in/digigov-portal/", release="~3rd week",
         info=dict(
             what="Domestic scheduled-airline passengers carried in the month (DGCA traffic statistics) — a premium-consumption and business-activity proxy.",
             changes="DGCA PDF is timeliest; the data.gov.in mirror lags but is API-accessible. Airline capacity events (groundings, new inductions) can move the number independently of demand.")),
    dict(id="fastag", name="FASTag toll collections", category="Consumption & Demand",
         unit="₹ cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=6600, vol=180, source="NPCI / NHAI", access="file",
         url="https://www.npci.org.in/what-we-do/netc-fastag/product-statistics", release="Early month",
         info=dict(
             what="Monthly electronic toll collections via FASTag (NPCI NETC) — a near-universal road-freight and intercity mobility proxy since tolling went mandatory-electronic.",
             changes="Toll-rate revisions (typically April) create level shifts; new toll-plaza additions add mechanical growth. Volume (transaction count) is the cleaner activity read than value.")),

    # ---------------- Rural & Agri ----------------
    dict(id="rainfall", name="Rainfall vs LPA (season-to-date)", category="Rural & Agri",
         unit="% of LPA", freq="W", agg="last", up_is_good=True, kind="level",
         base=103.0, vol=3.0, source="IMD", access="scrape",
         url="https://mausam.imd.gov.in/", release="Weekly in season",
         info=dict(
             what="Cumulative southwest-monsoon rainfall as % of the Long Period Average (IMD), Jun–Sep — the single most important leading indicator for rural incomes, kharif output and food inflation.",
             changes="IMD updated the LPA base period to 1971-2020 (LPA ≈ 87 cm) — older '% of LPA' readings sit on a different denominator. Distribution (spatial/temporal) matters as much as the aggregate; a 100% season with a long dry spell can still hurt yields.")),
    dict(id="reservoirs", name="Reservoir storage", category="Rural & Agri",
         unit="% of capacity", freq="W", agg="last", up_is_good=True, kind="level",
         base=64.0, vol=3.0, source="CWC weekly bulletin", access="pdf",
         url="https://cwc.gov.in/", release="Thursday (weekly)",
         info=dict(
             what="Live storage in the ~150 CWC-monitored major reservoirs as % of capacity — drives rabi-season sowing prospects, hydro generation and urban water supply.",
             changes="CWC has expanded the monitored-reservoir set over time (capacity denominator changes) — compare % of capacity, and vs the 10-year average the bulletin provides, not absolute BCM across years.")),
    dict(id="mgnrega", name="MGNREGA work demand", category="Rural & Agri",
         unit="cr households", freq="M", agg="last", up_is_good=False, kind="level",
         base=2.05, vol=0.18, source="nrega.nic.in / data.gov.in", access="api",
         url="https://nrega.nic.in/", release="Monthly",
         info=dict(
             what="Households demanding work under the rural employment guarantee in the month — an inverse rural-distress gauge: demand rises when farm and informal work dries up.",
             changes="Demand data is administrative and can be suppressed by budget exhaustion or Aadhaar-linked payment issues (i.e., measured demand < true demand in stressed months). Strong seasonality — compare YoY, not MoM.")),
    dict(id="rural_wages", name="Rural wage growth", category="Rural & Agri",
         unit="% YoY", freq="M", agg="last", up_is_good=True, kind="rate",
         base=5.9, vol=0.3, source="Labour Bureau (PDF)", access="pdf",
         url="https://labourbureau.gov.in/", release="~2 mo lag",
         info=dict(
             what="YoY growth in nominal rural wages (agricultural and non-agricultural occupations) from the Labour Bureau's Wage Rates in Rural India. Deflate by rural CPI for the real-wage read that actually drives rural demand.",
             changes="~2-month publication lag and occasional gap months. Real rural wage growth was negative-to-flat for much of 2022-24 — the level of the real series matters more than nominal momentum.")),

    # ---------------- Employment ----------------
    dict(id="plfs_ur", name="Unemployment rate (PLFS, CWS)", category="Employment",
         unit="%", freq="M", agg="last", up_is_good=False, kind="rate",
         base=5.1, vol=0.2, source="MoSPI monthly PLFS bulletin", access="pdf",
         url="https://www.mospi.gov.in/", release="~2 wk after month-end",
         info=dict(
             what="All-India unemployment rate (Current Weekly Status, age 15+) from the Periodic Labour Force Survey — share of the labour force that sought but didn't find work in the reference week.",
             changes="Big change: PLFS went monthly, all-India (rural+urban) from April 2025 — previously only quarterly urban bulletins existed. The monthly series is young; seasonal patterns aren't yet established, so read a few months together. LFPR and WPR in the same bulletin matter as much as the UR.")),
    dict(id="epfo", name="EPFO net payroll additions", category="Employment",
         unit="lakh", freq="M", agg="last", up_is_good=True, kind="level",
         base=15.2, vol=1.3, source="EPFO / PIB (PDF)", access="pdf",
         url="https://www.epfindia.gov.in/", release="~2 mo lag",
         info=dict(
             what="Net new EPF subscribers in the month (new enrolments minus exits plus rejoins) — a formal-sector payroll proxy from provident-fund administrative data.",
             changes="Heavily revised — every month's figure is restated for several subsequent releases (sometimes by double-digit %). Captures formalization of existing jobs as well as new jobs; ~2-month publication lag.")),

    # ---------------- Energy & Infrastructure ----------------
    dict(id="power_gen", name="Electricity generation", category="Energy & Infrastructure",
         unit="BU", freq="D", agg="sum", up_is_good=True, kind="level",
         base=156.0, vol=5.0, source="Grid India PSP / CEA API", access="api",
         url="https://report.grid-india.in/", release="Daily PSP, monthly summary",
         info=dict(
             what="All-India electricity generation (billion units) from Grid India's daily Power Supply Position report and CEA monthly summaries — the classic same-day industrial-activity proxy.",
             changes="Rooftop solar behind the meter doesn't appear in grid generation — the series increasingly understates true electricity demand growth. Weather (heatwaves/cold snaps) drives short-run swings; YoY comparisons around extreme-weather months mislead.")),
    dict(id="peak_demand", name="Peak power demand", category="Energy & Infrastructure",
         unit="GW", freq="D", agg="max", up_is_good=True, kind="level",
         base=242.0, vol=6.0, source="Grid India / Vidyut Pravah", access="scrape",
         url="https://vidyutpravah.in/", release="Daily",
         info=dict(
             what="Maximum instantaneous all-India power demand met (GW) in the day — monthly value is the month's peak. Tracks both economic activity and cooling demand.",
             changes="Summer peaks are weather events as much as economic ones — the national peak record is usually a heatwave print. 'Demand met' excludes shortage; check the unmet-demand line in the PSP report when the grid is stressed.")),

    # ================= Round-2 additions (14 series) =================

    # -- Output & Activity --
    dict(id="obicus_cu", name="Capacity utilisation (OBICUS)", category="Output & Activity",
         unit="%", freq="Q", agg="last", up_is_good=True, kind="rate",
         base=75.4, vol=0.8, source="RBI OBICUS survey", access="file",
         url="https://www.rbi.org.in/Scripts/QuarterlyPublications.aspx", release="Quarterly, with MPC",
         info=dict(
             what="Capacity utilisation of ~700-800 manufacturing firms from the RBI's quarterly Order Books, Inventories and Capacity Utilisation Survey — the standard trigger gauge for the private capex cycle (sustained CU above ~75-76% historically precedes fresh investment).",
             changes="Sample composition shifts between rounds and responses arrive with a ~2-quarter lag to the reference quarter. RBI also publishes a seasonally-adjusted CU — use one consistently; the two diverge around festive quarters.")),

    # -- Fiscal --
    dict(id="capex", name="Central govt capex (FYTD)", category="Fiscal",
         unit="₹ lakh cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=4.2, vol=0.5, trend=5.5, source="CGA monthly accounts", access="file",
         url="https://cga.nic.in/MonthDashboardReport/Published/list.aspx", release="Last working day",
         info=dict(
             what="Union government capital expenditure, fiscal-year-to-date (₹ lakh crore), from the same CGA monthly accounts as the deficit — the public-investment engine that has led the capex cycle since FY21. Compare against the % of Budget Estimate to judge pace.",
             changes="Cumulative from April — difference consecutive months for the monthly flow; March and quarter-ends carry bunched spending. Loans to states for capex (a separate line) blur the centre-vs-state split; grants-in-aid for capital assets are excluded from this headline.")),

    # -- External Sector --
    dict(id="svc_exports", name="Services exports", category="External Sector",
         unit="US$ bn", freq="M", agg="last", up_is_good=True, kind="level",
         base=32.5, vol=0.9, source="RBI monthly PR", access="scrape",
         url="https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx", release="~1 month lag",
         info=dict(
             what="Monthly services export receipts (software, business services, travel, transport) estimated by the RBI — India's structural external strength; the services surplus offsets roughly half the goods deficit.",
             changes="Monthly figures are provisional RBI estimates later reconciled in the quarterly BoP — revisions can be meaningful. GCC (global capability centre) expansion is shifting the mix from IT-services contracts to in-house exports, which the data captures with a lag.")),

    # -- Money, Credit & Banking --
    dict(id="walr", name="WALR (fresh loans)", category="Money, Credit & Banking",
         unit="%", freq="M", agg="last", up_is_good=False, kind="rate",
         base=8.6, vol=0.08, source="RBI lending-rate data", access="file",
         url="https://data.rbi.org.in/DBIE/", release="Monthly, ~1 mo lag",
         info=dict(
             what="Weighted Average Lending Rate on fresh rupee loans of scheduled commercial banks — the cleanest read on how much of the RBI's policy easing is actually reaching borrowers (transmission).",
             changes="Falling WALR is coded green here because 2025-26 is an easing cycle — in a tightening cycle the reading flips. External-benchmark-linked loans (EBLR, now the majority) transmit within a quarter; MCLR-linked legacy books lag by 6-12 months, so the WALR moves in steps.")),
    dict(id="gnpa", name="GNPA ratio (banks)", category="Money, Credit & Banking",
         unit="%", freq="H", agg="last", up_is_good=False, kind="rate",
         base=2.3, vol=0.1, source="RBI Financial Stability Report", access="pdf",
         url="https://www.rbi.org.in/Scripts/FsReports.aspx", release="Jun & Dec (FSR)",
         info=dict(
             what="Gross non-performing assets as % of gross advances for scheduled commercial banks, from the RBI's half-yearly Financial Stability Report (with NNPA, slippage and sectoral cuts) — the system-wide asset-quality gauge.",
             changes="Multi-decade lows through 2025-26 after the post-AQR clean-up; the FSR's stress-test projections matter more than the headline at this level. Write-offs flatter the ratio — track the slippage ratio alongside. Unsecured-retail and microfinance NPAs are the current watch pockets.")),

    # -- Consumption & Demand --
    dict(id="cv", name="CV retail sales", category="Consumption & Demand",
         unit="'000 units", freq="M", agg="last", up_is_good=True, kind="level",
         base=84.0, vol=6.0, source="FADA / Vahan", access="scrape",
         url="https://www.fada.in/", release="~5th–7th",
         info=dict(
             what="Commercial vehicle retail registrations (FADA/Vahan) — trucks and buses; the classic leading indicator of freight demand, infrastructure activity and the broader industrial cycle. MHCV vs LCV split separates capex-linked from consumption-linked demand.",
             changes="Same Vahan back-revision caveat as PV/2W. Regulatory events (axle-load norms, BS-VI phases, scrappage policy) create pre-buy spikes and payback troughs that look like demand swings but aren't.")),
    dict(id="gold", name="Gold demand (India)", category="Consumption & Demand",
         unit="tonnes", freq="Q", agg="last", up_is_good=True, kind="level",
         base=200.0, vol=25.0, source="World Gold Council", access="scrape",
         url="https://www.gold.org/goldhub/research/gold-demand-trends", release="Quarterly (~1 mo lag)",
         info=dict(
             what="India consumer gold demand (jewellery + bars & coins) from the World Gold Council's quarterly Gold Demand Trends — a rural-savings and wedding/festival-demand proxy with a long history. Tracked strictly in TONNES (volume), never value, so record gold prices don't masquerade as demand strength.",
             changes="Price-elastic: record gold prices suppress tonnage while value spent rises — read tonnes and value together. WGC revises recent quarters; smuggled/unofficial flows are estimated. Import-duty changes (e.g. the 2024 cut) shift official vs unofficial mix.")),
    dict(id="trai_subs", name="Wireless subscriber net adds", category="Consumption & Demand",
         unit="mn", freq="M", agg="last", up_is_good=True, kind="level",
         base=3.0, vol=1.5, source="TRAI monthly report", access="file",
         url="https://www.trai.gov.in/release-publication/reports/telecom-subscriptions-reports", release="~2 mo lag",
         info=dict(
             what="Net monthly change in wireless (mobile) subscribers from TRAI's subscription report, with urban/rural and active-subscriber (VLR) detail — a mass-market connectivity and affordability read.",
             changes="Tariff hikes trigger SIM consolidation (negative adds that aren't demand destruction); the active-VLR series is cleaner than gross subscriptions. ~2-month publication lag; 5G FWA additions now sit in a separate line.")),

    # -- Rural & Agri --
    dict(id="sowing", name="Kharif sowing acreage", category="Rural & Agri",
         unit="lakh ha", freq="W", agg="last", up_is_good=True, kind="level",
         base=690.0, vol=25.0, trend=40.0, source="Dept. of Agriculture", access="scrape",
         url="https://agriwelfare.gov.in/", release="Friday, in season",
         info=dict(
             what="Cumulative area sown under kharif crops (lakh hectares), released weekly by the Agriculture Ministry during Jun-Sep (rabi counterpart Oct-Jan) — the real-time read on the farm season that rainfall only predicts.",
             changes="Weekly numbers are compiled from state reports of varying quality and are always compared to 'same period last year' and 'normal area' — use those ratios, not the raw level. Crop-mix shifts (paddy vs pulses vs cotton) matter more than the aggregate for farm incomes.")),

    # -- Employment --
    dict(id="lfpr", name="Labour force participation rate", category="Employment",
         unit="%", freq="M", agg="last", up_is_good=True, kind="rate",
         base=56.2, vol=0.3, source="MoSPI monthly PLFS bulletin", access="pdf",
         url="https://www.mospi.gov.in/", release="With PLFS UR",
         info=dict(
             what="Share of the 15+ population in the labour force (working or seeking work), Current Weekly Status, from the same monthly PLFS bulletin as the unemployment rate. A falling UR with falling LFPR is discouragement, not job creation — always read the pair together.",
             changes="Monthly series only exists since April 2025. India's female LFPR is the structural story — the bulletin's gender split is worth tracking separately. Definitional differences vs CMIE's tighter 'actively seeking' standard explain the level gap between the two sources.")),

    # -- Energy & Infrastructure --
    dict(id="coal", name="Coal production", category="Energy & Infrastructure",
         unit="MT", freq="M", agg="last", up_is_good=True, kind="level",
         base=85.0, vol=8.0, source="Ministry of Coal / PIB", access="scrape",
         url="https://coal.gov.in/", release="1st week",
         info=dict(
             what="All-India coal production (million tonnes) — Coal India, SCCL and captive/commercial mines — from Ministry of Coal releases. Feeds ~70% of power generation; also a mining-activity and rail-freight driver.",
             changes="Strong seasonality (monsoon dips, Q4 push to annual targets). Captive/commercial mine share is rising, so Coal India's own 1st-of-month number no longer represents the whole sector — use the all-India figure. Power-plant coal stocks (CEA daily) are the stress signal to watch alongside.")),

    # -- RBI forward-looking surveys (bi-monthly, with MPC) --
    dict(id="ccs", name="Consumer confidence (CSI)", category="Output & Activity",
         unit="index", freq="B", agg="last", up_is_good=True, kind="level",
         base=97.5, vol=1.5, source="RBI CCS (bi-monthly)", access="file",
         url="https://www.rbi.org.in/Scripts/BimonthlyPublications.aspx", release="With MPC",
         info=dict(
             what="Current Situation Index from the RBI's Consumer Confidence Survey (~6,000 urban households, 19 cities): perceptions of economy, employment, prices, income and spending; 100 = neutral. The Future Expectations Index (FEI) runs ~20 points more optimistic.",
             changes="Urban-only — no rural read; sample cities have been expanded over time. Bi-monthly, timed to MPC meetings. Level shifts around survey-redesign rounds (2023) — YoY comparisons across redesigns need care.")),
    dict(id="ies", name="Inflation expectations (1yr, households)", category="Prices & Inflation",
         unit="%", freq="B", agg="last", up_is_good=False, kind="rate",
         base=8.9, vol=0.3, source="RBI IES (bi-monthly)", access="file",
         url="https://www.rbi.org.in/Scripts/BimonthlyPublications.aspx", release="With MPC",
         info=dict(
             what="Median one-year-ahead inflation expectation of urban households from the RBI's Inflation Expectations Survey — the anchoring gauge the MPC cites; direction and de-anchoring matter more than the level.",
             changes="Households systematically over-estimate inflation (median runs ~4-5pp above actual CPI) — track the change, never the gap to actual. Bi-monthly with MPC; the 3-month-ahead series is noisier but leads turning points.")),
    dict(id="ios", name="Business expectations (IOS)", category="Output & Activity",
         unit="index", freq="Q", agg="last", up_is_good=True, kind="level",
         base=133.0, vol=2.0, source="RBI IOS (quarterly)", access="file",
         url="https://www.rbi.org.in/Scripts/QuarterlyPublications.aspx", release="With MPC",
         info=dict(
             what="Business Expectations Index from the RBI's Industrial Outlook Survey of ~1,500 manufacturers: net-response composite on production, orders, employment, input costs and profit margins for the coming quarter; >100 = expansion expected.",
             changes="Response rates fluctuate and the panel skews to larger firms — MSME stress under-registers. The assessment-vs-expectation gap (what firms said would happen vs what happened) is a useful over-optimism correction.")),

    # ================= Deal Environment =================
    dict(id="nifty", name="Nifty 50", category="Deal Environment",
         unit="index", freq="D", agg="last", up_is_good=True, kind="level",
         base=26400, vol=180, trend=800, source="NSE", access="scrape",
         url="https://www.nseindia.com/market-data/live-equity-market", release="Daily, EOD",
         info=dict(
             what="NSE Nifty 50 closing level — the public-market backdrop for entry/exit pricing, portfolio marks and IPO appetite.",
             changes="Track alongside its P/E (next tile): a rising index on flat earnings is multiple expansion, a different signal for exits than earnings-led gains. Index reconstitutions (Mar/Sep) shift composition.")),
    dict(id="nifty_pe", name="Nifty 50 P/E (trailing)", category="Deal Environment",
         unit="x", freq="D", agg="last", up_is_good=None, kind="level",
         base=22.6, vol=0.3, source="NSE indices", access="scrape",
         url="https://www.nseindia.com/market-data/live-equity-market", release="Daily",
         info=dict(
             what="Trailing twelve-month price-to-earnings ratio of the Nifty 50 (NSE's official computation) — the valuation gauge that frames both entry multiples and exit windows. Coded neutral: high P/E is good for sellers, bad for buyers.",
             changes="NSE switched its official index P/E from standalone to consolidated earnings in 2021 — pre-2021 history sits ~10-15% higher on the old basis. Compare to the 10-year band, not a point average.")),
    dict(id="vix", name="India VIX", category="Deal Environment",
         unit="index", freq="D", agg="last", up_is_good=False, kind="level",
         base=13.5, vol=1.2, source="NSE", access="scrape",
         url="https://www.nseindia.com/market-data/live-market-indices", release="Daily",
         info=dict(
             what="Implied 30-day volatility of Nifty options — the risk-appetite thermometer. Sub-12 = complacency (good IPO windows), 20+ = stress (windows shut).",
             changes="Computed from the Nifty option chain; methodology stable since 2014. Spikes are event-driven (elections, budgets, global shocks) — read levels against the event calendar.")),
    dict(id="ipo_qip", name="IPO + QIP issuance", category="Deal Environment",
         unit="₹ cr", freq="M", agg="last", up_is_good=True, kind="level",
         base=17500, vol=9000, source="SEBI bulletin / prime", access="file",
         url="https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=4&ssid=23&smid=0", release="Monthly, ~1 mo lag",
         info=dict(
             what="Fresh equity raised via IPOs and Qualified Institutional Placements in the month (SEBI primary-market data) — the most direct gauge of whether the exit window is open.",
             changes="Extremely lumpy — one mega-IPO doubles a month; read the 3-month average and the pipeline (DRHPs filed) together. SEBI bulletin data lags ~a month; exchanges publish faster but less complete numbers.")),
    dict(id="corp_spread", name="AAA 3Y corporate spread", category="Deal Environment",
         unit="bps", freq="M", agg="last", up_is_good=False, kind="rate",
         base=68, vol=7, source="FIMMDA / CCIL", access="file",
         url="https://www.fimmda.org/", release="Daily (tracked monthly)",
         info=dict(
             what="Spread of 3-year AAA corporate bond yields over the matching G-sec (FIMMDA valuations) — the market price of credit risk and the marginal cost of acquisition debt.",
             changes="Valuation-based (matrix) rather than traded for many points — spreads can be stale in illiquid stretches. Widening that persists beyond a quarter is a genuine financing-conditions signal; day-to-day noise is not.")),

    # ================= Global Context =================
    dict(id="brent", name="Brent crude", category="Global Context",
         unit="US$/bbl", freq="D", agg="last", up_is_good=False, kind="level",
         base=68.0, vol=1.6, source="FRED / EIA", access="api",
         url="https://fred.stlouisfed.org/series/DCOILBRENTEU", release="Daily",
         info=dict(
             what="Brent crude spot price — the single most important exogenous variable for India: every $10/bbl adds roughly 0.3-0.4% of GDP to the import bill and ~30bps to CPI with a lag.",
             changes="India's actual import basket trades at a discount/premium to Brent that varies with Russian-crude share — PPAC publishes the Indian basket price if precision matters. FRED daily series is free API.")),
    dict(id="dxy", name="Dollar index (DXY)", category="Global Context",
         unit="index", freq="D", agg="last", up_is_good=False, kind="level",
         base=97.0, vol=0.6, source="FRED / ICE", access="api",
         url="https://fred.stlouisfed.org/series/DTWEXBGS", release="Daily",
         info=dict(
             what="Trade-weighted US dollar strength — the global risk-appetite dial that drives EM flows: a rising dollar tightens global financial conditions and typically coincides with FII selling in India.",
             changes="DXY (ICE) is EUR-heavy; FRED's broad trade-weighted index is the better economic measure — this tracker uses the FRED broad index. The two diverge when EUR moves alone.")),
    dict(id="ust10y", name="US 10Y Treasury yield", category="Global Context",
         unit="%", freq="D", agg="last", up_is_good=False, kind="rate",
         base=4.15, vol=0.04, source="FRED", access="api",
         url="https://fred.stlouisfed.org/series/DGS10", release="Daily",
         info=dict(
             what="US 10-year Treasury yield — the global risk-free rate that anchors the India-US spread; a narrowing spread pressures FPI debt flows and the rupee.",
             changes="Watch the India 10Y minus US 10Y spread (derivable from two tiles here) — it compressed to multi-decade lows in 2024-26, changing the old flow heuristics.")),
    dict(id="fedfunds", name="Fed funds target (upper)", category="Global Context",
         unit="%", freq="M", agg="last", up_is_good=False, kind="rate",
         base=3.60, vol=0.0, source="FOMC / FRED", access="api",
         url="https://fred.stlouisfed.org/series/DFEDTARU", release="8 FOMC meetings/yr",
         info=dict(
             what="Upper bound of the Federal Reserve's policy rate target — sets the global cost of capital and frames how much room the RBI has to ease without pressuring the rupee.",
             changes="The dot plot and futures-implied path move markets more than the level itself; consider adding the 12-month-forward implied rate as a companion series later.")),
    dict(id="us_cpi", name="US CPI inflation", category="Global Context",
         unit="% YoY", freq="M", agg="last", up_is_good=False, kind="rate",
         base=2.6, vol=0.15, source="BLS / FRED", access="api",
         url="https://fred.stlouisfed.org/series/CPIAUCSL", release="~10th–13th"),
    dict(id="global_pmi", name="Global composite PMI", category="Global Context",
         unit="index", freq="M", agg="last", up_is_good=True, kind="level",
         base=52.4, vol=0.6, source="S&P Global (headline)", access="scrape",
         url="https://www.pmi.spglobal.com/Public/Release/PressReleases", release="~5th business day"),
]

# --- default info for entries declared without one (keeps additions terse) ---
_DEFAULT_INFO = {
    "us_cpi": dict(
        what="US consumer price inflation YoY (BLS) — drives Fed policy expectations and therefore the dollar, US yields and EM flows; included as the upstream variable behind three other tiles in this block.",
        changes="Core PCE, not CPI, is the Fed's target measure — CPI prints move markets more but the Fed reacts to PCE; when they diverge, trust PCE for the policy path."),
    "global_pmi": dict(
        what="J.P.Morgan Global Composite PMI (S&P Global): output-weighted world manufacturing + services diffusion index; >50 = global expansion. Context for India's export-facing series.",
        changes="Free headline only, like the India PMIs; country weights rebalance annually. India is now a meaningful positive contributor — the global number is not fully independent of the India series here."),
}
for s in SERIES:
    if "info" not in s:
        s["info"] = _DEFAULT_INFO[s["id"]]

# ---------------------------------------------------------------------------
# Presentation & analytics flags (applied post-hoc so entries stay terse)
# ---------------------------------------------------------------------------

# The 8 headline series shown in the hero strip at the top of the page.
HEADLINE = ["cpi", "iip", "gst", "credit", "fii_m", "pv", "trade_def", "gsec10y"]

# Tile presentation overrides:
#   compact — number + comparisons only, no chart (daily flow tapes)
#   chart   — wide tile with a period-toggle chart (1D/5D/1M/6M/1Y/2Y/3Y/5Y/10Y)
DISPLAY = {"fii": "compact", "dii": "compact",
           "nifty": "chart", "repo": "chart", "gsec10y": "chart", "inrusd": "chart"}

# Monthly/quarterly series where month-on-month is mostly calendar/seasonality:
# YoY becomes the lead comparison and "vs prev" is de-emphasized.
SEASONAL = {"gst", "pv", "tw", "cv", "tractors", "fuel", "airpax", "coal",
            "gold", "mgnrega", "sowing", "exports", "imports", "trade_def",
            "upi", "fastag", "cards", "ipo_qip", "power_gen", "capex"}

# Structurally trending series: "vs 10-yr avg" is meaningless (always above),
# so the long-term row becomes "YoY growth vs 3-yr trend CAGR" instead.
TREND_LT = {"gst", "upi", "cards", "fastag", "airpax", "trai_subs", "capex",
            "svc_exports", "sip", "exports", "imports", "power_gen", "coal",
            "fx_reserves", "nifty", "pe_deals"}

# First prints that systematically restate — tiles carry a "revises" badge.
REVISION_PRONE = {"iip", "gdp", "pfce", "exports", "imports", "trade_def",
                  "svc_exports", "epfo", "pv", "tw", "cv", "mgnrega", "sowing",
                  "core8", "gold"}

for s in SERIES:
    s["headline"] = s["id"] in HEADLINE
    s["seasonal"] = s["id"] in SEASONAL
    s["lt_mode"] = "trend" if s["id"] in TREND_LT else "avg"
    s["revision_prone"] = s["id"] in REVISION_PRONE
    s["display"] = DISPLAY.get(s["id"], "std")

# ---------------------------------------------------------------------------
# Composite indices — z-score composites over a 10-year monthly grid.
# sign +1 = component enters positively; -1 = inverted (e.g. MGNREGA demand).
# In production these are computed off the monthly rollup table.
# ---------------------------------------------------------------------------
COMPOSITES = [
    dict(id="cmp_rural", name="Rural Demand Index",
         components=[("tractors", 1), ("tw", 1), ("mgnrega", -1),
                     ("rural_wages", 1), ("rainfall", 1)],
         info=dict(
             what="Equal-weight composite of z-scores (10-year window, monthly grid) of tractor sales, 2W retail, MGNREGA work demand (inverted), real rural wage growth and rainfall vs LPA. Positive = rural demand running above its 10-year norm.",
             changes="Components with shorter histories use full available history for their z-window. MGNREGA enters inverted (rising work demand = distress). Rainfall drops out of the composite outside the monsoon season in production.")),
    dict(id="cmp_urban", name="Urban Discretionary Index",
         components=[("pv", 1), ("cards", 1), ("airpax", 1), ("upi", 1)],
         info=dict(
             what="Equal-weight z-score composite of PV retail sales, credit-card spends, domestic air passengers and UPI value — the urban middle-class discretionary pulse vs its 10-year norm.",
             changes="Trending components (UPI, cards) enter as deviations from their own trend, not raw levels, so digitization drift doesn't permanently inflate the index.")),
    dict(id="cmp_capex", name="Capex Cycle Index",
         components=[("obicus_cu", 1), ("capex", 1), ("cv", 1),
                     ("iip", 1), ("core8", 1)],
         info=dict(
             what="Equal-weight z-score composite of capacity utilisation (OBICUS), central government capex, CV retail sales, IIP growth and core-industries growth — public + private investment-cycle momentum.",
             changes="OBICUS is quarterly and enters with a lag (repeated across its quarter's months). A sustained reading above +0.5σ alongside CU >75% has historically preceded private-capex upturns.")),
    dict(id="cmp_fci", name="Financial Conditions Index",
         components=[("liquidity", 1), ("credit", 1), ("fii", 1),
                     ("gsec10y", -1), ("walr", -1)],
         info=dict(
             what="Equal-weight z-score composite of system liquidity, bank credit growth, FPI flows, the 10Y G-sec yield (inverted) and WALR (inverted). Positive = financial conditions looser than the 10-year norm — supportive for deal financing and multiples.",
             changes="Sign conventions follow 'higher composite = easier conditions'. RBI publishes no official FCI; this mirrors common sell-side constructions (Goldman/CRISIL versions weight components differently).")),
]
