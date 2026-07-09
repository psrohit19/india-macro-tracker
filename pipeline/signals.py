"""
Signals & Playbook engine — turns the series into ~7 investment-decision
theme signals, each with a status light, a data-driven headline, and a
playbook implication. Computed fresh on every refresh from the latest live
values; rules are deliberately transparent (read them below) so the IC can
challenge them.

Status: "green" (supportive), "amber" (watch), "red" (adverse).
Sample-flagged series never drive a signal (their inputs are skipped).
"""


def _latest(recs, sid):
    r = recs.get(sid)
    if not r or r.get("sample"):
        return None
    return r["latest"]["raw"]


def _yoy_delta(recs, sid):
    """Signed YoY delta direction (+1/-1/0) and text from the record rows."""
    r = recs.get(sid)
    if not r or r.get("sample"):
        return None
    for row in r["rows"]:
        if row[0].startswith("vs LY") and row[2]:
            return row[2]
    return None


def build_signals(recs):
    S = []

    def add(name, status, headline, implication, drivers):
        S.append(dict(name=name, status=status, headline=headline,
                      implication=implication,
                      drivers=[d for d in drivers if d in recs]))

    # ---- 1. Growth momentum ----
    iip = _latest(recs, "iip"); pmi = _latest(recs, "pmi_mfg"); gst = _yoy_delta(recs, "gst")
    credit = _latest(recs, "credit")
    score = sum([1 if (iip or 0) >= 4.5 else 0, 1 if (pmi or 0) >= 54 else 0,
                 1 if (credit or 0) >= 12 else 0])
    st = "green" if score >= 2 else ("amber" if score == 1 else "red")
    add("Growth momentum", st,
        f"IIP {iip:.1f}%, mfg PMI {pmi:.1f}, credit {credit:.1f}% — expansion intact but PMI off its 2025 highs" if iip and pmi and credit else "Mixed prints",
        "Underwrite base-case revenue growth, but haircut FY27 exit-multiple assumptions if PMI slips below 54.",
        ["iip", "pmi_mfg", "gst", "credit", "power_gen"])

    # ---- 2. Inflation & rate path ----
    cpi = _latest(recs, "cpi"); wpi = _latest(recs, "wpi"); brent = _latest(recs, "brent")
    cpi_d = _yoy_delta(recs, "cpi")
    rising = cpi_d and cpi_d["dir"] == 1
    if (cpi or 0) > 5.5 or ((wpi or 0) > 8 and rising and (brent or 0) > 85):
        st = "red"
    elif rising or (wpi or 0) > 6 or (brent or 0) > 75:
        st = "amber"
    else:
        st = "green"
    add("Inflation & rate path", st,
        f"CPI {cpi:.1f}% and re-accelerating; WPI {wpi:.1f}% on the crude shock; Brent ${brent:.0f}" if cpi and wpi and brent else "Inflation prints mixed",
        "Rate cuts are likely done for now — model portfolio-company debt at current rates, not lower; revisit floating-rate exposure.",
        ["cpi", "cfpi", "wpi", "ies", "brent", "repo"])

    # ---- 3. Rural engine ----
    rain = _latest(recs, "rainfall"); sow = _yoy_delta(recs, "sowing"); trac = _yoy_delta(recs, "tractors")
    bad_season = (rain or 100) < 92 or (sow and sow["dir"] == -1)
    strong_proxy = trac and trac["dir"] == 1
    st = "red" if bad_season and not strong_proxy else ("amber" if bad_season else "green")
    add("Rural engine", st,
        f"Monsoon {rain:.0f}% of normal, sowing down YoY — but tractors still +25% on support programs" if rain else "Rural signals mixed",
        "Stress-test rural-exposed portcos' H2 demand; delayed sowing hits Oct-Mar cash flows if rains don't normalize by early August.",
        ["rainfall", "sowing", "reservoirs", "tractors", "tw", "mgnrega"])

    # ---- 4. External & currency ----
    inr = _yoy_delta(recs, "inrusd"); fx = _latest(recs, "fx_reserves"); fytd = _latest(recs, "fii_fytd")
    dep = inr and inr["dir"] == 1                       # rupee weakening YoY
    heavy_out = (fytd or 0) < -100000
    st = "red" if dep and heavy_out else ("amber" if dep or heavy_out else "green")
    add("External & currency", st,
        f"INR ~95/$ (weak YoY), FPI FYTD -₹1.4 lakh cr, reserves ${fx:.0f}bn buffer intact" if fx else "External account under watch",
        "Dollar-revenue portcos gain; importers squeezed. Hedge near-term INR exposure on deals with foreign-currency legs.",
        ["inrusd", "fx_reserves", "fii_fytd", "trade_def", "brent", "dxy", "ust10y"])

    # ---- 5. Credit default risk ----
    gnpa = _latest(recs, "gnpa"); gnpa_d = _yoy_delta(recs, "gnpa")
    crg = _latest(recs, "credit"); dep_g = _latest(recs, "deposits"); pl = _latest(recs, "personal_loans")
    gap = (crg - dep_g) if (crg is not None and dep_g is not None) else None
    stress = 0
    if gnpa is not None and gnpa > 3: stress += 2
    if gnpa_d and gnpa_d["dir"] == 1: stress += 2       # NPAs turning up = the signal
    if gap is not None and gap > 4: stress += 1          # credit outrunning deposits
    if (pl or 0) > 15: stress += 1                       # unsecured buildup
    st = "red" if stress >= 3 else ("amber" if stress >= 1 else "green")
    gap_txt = f"{gap:+.1f}pp" if gap is not None else "n/a"
    add("Credit default risk", st,
        f"GNPA {gnpa:.1f}% (multi-decadal low) but credit-deposit gap {gap_txt} and personal loans {pl:.1f}% — classic late-cycle buildup" if gnpa is not None else "Asset quality benign",
        "System defaults are at cyclical lows — which is when underwriting gets sloppy. Assume higher default probabilities than today's in LBO/credit models; watch unsecured-retail slippage in the Dec FSR.",
        ["gnpa", "credit", "deposits", "personal_loans", "walr", "liquidity"])

    # ---- 6. Financing conditions ----
    liq = _latest(recs, "liquidity"); walr = _yoy_delta(recs, "walr")
    easing = walr and walr["dir"] == -1
    st = "green" if (liq or 0) > 0 and easing else ("amber" if (liq or 0) > -1 else "red")
    add("Financing conditions", st,
        f"System liquidity +₹{liq:.1f} lakh cr surplus; WALR transmitting lower" if liq is not None else "Liquidity neutral",
        "Window to lock acquisition financing is open while transmission lasts — it closes if the crude shock forces the RBI to defend the rupee.",
        ["liquidity", "walr", "repo", "m3", "gsec10y"])

    # ---- 7. Exit window ----
    vix = _latest(recs, "vix"); ipo = _latest(recs, "ipo_qip"); pe = _latest(recs, "nifty_pe")
    if (vix or 0) >= 17:
        st = "red"
    elif (vix or 0) >= 13 or (ipo or 0) < 10000:
        st = "amber"
    else:
        st = "green"
    add("Exit window", st,
        f"VIX {vix:.1f} (spiked on Iran headlines), issuance thin, Nifty {pe:.1f}x vs ~22x norm" if vix and pe else "Window conditions mixed",
        "Hold DRHP-ready exits until VIX settles back under ~13; use the pause to prep documentation so filings move fast when the window reopens.",
        ["vix", "ipo_qip", "nifty", "nifty_pe", "fii_m", "dii_m"])

    return S
