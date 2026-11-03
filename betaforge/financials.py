"""Small, explicit financial formulas over normalized base-unit inputs."""
from decimal import Decimal, InvalidOperation, localcontext


VERSION = "1"
MONEY = "SEK"
FRACTION = "dimensionless"


def _definition(text, required, outputs, primary, limits, optional=None, options=None):
    return {"version": VERSION, "formula_text": text, "required_fields": required,
            "optional_fields": optional or {}, "output_units": outputs,
            "primary_output": primary, "limits": limits, "options": options or []}


FORMULAS = {
    "ebit_margin": _definition("100 × EBIT / revenue", {"ebit": MONEY, "revenue": MONEY},
        {"margin_percent": "percent"}, "margin_percent", "Positive revenue; keep reported and adjusted EBIT separate."),
    "incremental_ebit_margin": _definition("100 × (EBIT current − EBIT previous) / (revenue current − revenue previous)",
        {k: MONEY for k in ("ebit_current", "ebit_previous", "revenue_current", "revenue_previous")},
        {"ebit_change": MONEY, "revenue_change": MONEY, "incremental_margin_percent": "percent"},
        "incremental_margin_percent", "Comparable periods must be confirmed; a zero revenue change is undefined. Small, negative and pass-through changes need interpretation.",
        options=["comparable_periods", "revenue_passthrough"]),
    "working_capital_to_sales": _definition("100 × selected operating balance / annual or R12 revenue; average balance = (opening + closing) / 2",
        {"balance_end": MONEY, "revenue": MONEY}, {"selected_balance": MONEY, "ratio_percent": "percent"},
        "ratio_percent", "Use a named trade balance. Sales ratios are not inventory/payable days.",
        optional={"balance_start": MONEY}, options=["balance_basis"]),
    "invested_capital": _definition("group book equity + gross debt including leases + net pension liability − cash − identified non-operating assets",
        {k: MONEY for k in ("group_equity", "gross_debt_including_leases", "net_pension_liability", "cash", "non_operating_assets")},
        {"invested_capital": MONEY}, "invested_capital", "Group equity already includes NCI and goodwill; gross debt already includes leases. Add none of them twice."),
    "operating_roic": _definition("NOPAT = EBIT × (1 − operating tax rate); ROIC = 100 × NOPAT / ((opening invested capital + closing invested capital) / 2)",
        {"ebit": MONEY, "operating_tax_rate": FRACTION, "invested_capital_start": MONEY, "invested_capital_end": MONEY},
        {"nopat": MONEY, "average_invested_capital": MONEY, "roic_percent": "percent"},
        "roic_percent", "Explicit tax fraction and positive average capital. Two-point capital average is a proxy, not issuer ROCE or provider ROIC."),
    "group_cash_conversion": _definition("cash after debt-like service = CFO − cash capex − interest paid outside CFO − lease principal outside CFO; conversion = 100 × that cash / group net income",
        {k: MONEY for k in ("cfo", "cash_capex", "interest_paid_outside_cfo", "lease_principal_outside_cfo", "group_net_income")},
        {"cash_after_capex": MONEY, "cash_after_capex_and_interest": MONEY,
         "cash_after_capex_and_net_interest": MONEY, "cash_after_debt_like_service": MONEY,
         "noncash_sbc_addback": MONEY, "conversion_percent": "percent"},
        "conversion_percent", "Capex, cash interest and lease principal are positive outflows. CFO already includes working capital/tax. Before dividends; not parent-owner FCFE. SBC is disclosed separately.",
        optional={"net_interest_cash_outside_cfo": MONEY, "noncash_sbc_addback": MONEY}),
    "fcf_yield": _definition("100 × explicitly scoped free cash flow / matching valuation denominator",
        {"free_cash_flow": MONEY, "valuation_denominator": MONEY}, {"yield_percent": "percent"},
        "yield_percent", "Parent-common cash requires market cap; unlevered firm cash requires enterprise value. Negative cash yield remains negative.",
        options=["cash_flow_scope", "denominator_scope"]),
    "ev_ebit": _definition("enterprise value / matching EBIT", {"enterprise_value": MONEY, "ebit": MONEY},
        {"multiple": FRACTION}, "multiple", "Positive EBIT; keep EV claim convention and earnings scope consistent."),
    "pe": _definition("dated share price / matching diluted earnings per share",
        {"price": "SEK/shares", "diluted_eps": "SEK/shares"}, {"multiple": FRACTION},
        "multiple", "Positive EPS and nonnegative price; a loss is not a meaningful P/E."),
    "volume_ebit": _definition("forecast sales volume × forecast EBIT per tonne",
        {"sales_volume": "tonnes", "ebit_per_tonne": "SEK/tonnes"}, {"ebit": MONEY},
        "ebit", "Volume is actual tonnes; per-tonne EBIT is SEK, not kSEK."),
    "revenue_ebit": _definition("forecast revenue × forecast EBIT margin fraction",
        {"revenue": MONEY, "ebit_margin": FRACTION}, {"ebit": MONEY},
        "ebit", "Margin is a fraction: 0.10 means 10%. Do not double-forecast the same driver with the volume model."),
    "valuation_case": _definition("future financial net debt = current financial net debt − annual retained cash × years; EV = forecast EBIT × exit multiple; common equity = EV − future financial net debt − additional leases − pensions − NCI + non-operating assets; future target = common equity / forecast shares; present value = future target / (1 + required return)^years + sum(annual dividend per share / (1 + required return)^t)",
        {"forecast_ebit": MONEY, "exit_multiple": FRACTION, "current_financial_net_debt": MONEY,
         "annual_retained_cash": MONEY, "years": FRACTION, "additional_leases": MONEY,
         "pensions": MONEY, "nci_value": MONEY, "non_operating_assets": MONEY,
         "forecast_shares": "shares", "annual_dividend_per_share": "SEK/shares", "required_return": FRACTION},
        {"future_financial_net_debt": MONEY, "enterprise_value": MONEY, "total_claims": MONEY,
         "common_equity": MONEY, "future_target": "SEK/shares", "terminal_pv": "SEK/shares",
         "dividend_pv": "SEK/shares", "present_value": "SEK/shares", "price_gap_percent": "percent"},
        "present_value", "Retained cash is after common dividends and all other cash needs. Explicit zero claims; positive shares/EBIT/multiple. Annual year-end dividends, integer horizon 1–10 years; negative common equity is not a negative share-price quote.",
        optional={"price": "SEK/shares"}),
    "scenario_weighted_values": _definition("expected value = sum(scenario probability × scenario value), separately for present value, terminal target and annual dividend",
        {**{case + "_weight": FRACTION for case in ("bear", "base", "bull")},
         **{case + "_" + field: "SEK/shares" for case in ("bear", "base", "bull")
            for field in ("present_value", "future_target", "annual_dividend_per_share")}, "years": FRACTION},
        {"expected_present_value": "SEK/shares", "expected_future_target": "SEK/shares",
         "expected_annual_dividend_per_share": "SEK/shares"}, "expected_present_value",
        "Nonnegative probabilities must sum exactly to one. Same valuation date, horizon, share/currency basis and year-end payment timing. Weights are analyst judgments, not measured frequencies."),
    "expected_cashflow_irr": _definition("0 = −price + sum(expected annual dividend per share / (1 + IRR)^t, t=1..years) + expected terminal target / (1 + IRR)^years",
        {"price": "SEK/shares", "expected_annual_dividend_per_share": "SEK/shares",
         "expected_future_target": "SEK/shares", "years": FRACTION},
        {"initial_cash_flow": "SEK/shares", "annual_interim_cash_flow": "SEK/shares",
         "terminal_cash_flow": "SEK/shares", "irr_percent": "percent"}, "irr_percent",
        "Positive initial price and nonnegative future cash payments, integer horizon 1–10 years. Equal year-end dividends; terminal year also receives the terminal target. Solve expected cash flows, never average scenario IRRs. This is not a guaranteed or probability-weighted realized annual return."),
}


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a financial number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Invalid financial number") from error
    if not result.is_finite() or abs(result) > Decimal("1e100"):
        raise ValueError("Nonfinite or excessive financial number")
    return result


def evaluate(formula, values, options=None):
    """Return auditable outputs; missing inputs affect only dependent outputs."""
    if formula not in FORMULAS:
        raise ValueError("Unknown financial formula")
    definition = FORMULAS[formula]
    options = dict(options or {})
    unknown = set(values) - set(definition["required_fields"]) - set(definition["optional_fields"])
    if unknown:
        raise ValueError("Unknown input fields: " + ", ".join(sorted(unknown)))
    if set(options) - set(definition["options"]):
        raise ValueError("Unknown formula options")
    v = {key: _decimal(value) for key, value in values.items() if value is not None}
    result = {"formula": formula, "version": VERSION, "primary_output": definition["primary_output"],
              "formula_text": definition["formula_text"], "outputs": {}, "warnings": [],
              "missing_inputs": sorted(set(definition["required_fields"]) - set(v))}

    def has(*keys):
        return all(key in v for key in keys)

    def warn(message):
        if message not in result["warnings"]:
            result["warnings"].append(message)

    def emit(key, value):
        if not value.is_finite() or abs(value) > Decimal("1e100"):
            raise ValueError("Nonfinite or excessive formula output")
        result["outputs"][key] = {"value": str(value), "unit": definition["output_units"][key]}

    def nonnegative(*keys):
        if any(key in v and v[key] < 0 for key in keys):
            raise ValueError("Expected positive outflow or balance magnitude: " + ", ".join(keys))

    with localcontext() as context:
        context.prec = 40
        if formula == "ebit_margin" and has("ebit", "revenue"):
            if v["revenue"] > 0:
                emit("margin_percent", v["ebit"] / v["revenue"] * 100)
            else:
                warn("EBIT margin needs positive revenue")
        elif formula == "incremental_ebit_margin":
            if has("ebit_current", "ebit_previous"):
                emit("ebit_change", v["ebit_current"] - v["ebit_previous"])
            if has("revenue_current", "revenue_previous"):
                change = v["revenue_current"] - v["revenue_previous"]
                emit("revenue_change", change)
                if change < 0:
                    warn("Revenue contracted: interpret both changes, not the ratio sign alone")
                if v["revenue_previous"] and abs(change / v["revenue_previous"]) < Decimal("0.01"):
                    warn("Revenue change is below 1% of the prior value; the incremental ratio is unstable")
            if options.get("comparable_periods") is not True:
                warn("Comparable period, scope and EBIT basis have not been confirmed")
            elif has("ebit_current", "ebit_previous", "revenue_current", "revenue_previous"):
                if change:
                    emit("incremental_margin_percent", (v["ebit_current"] - v["ebit_previous"]) / change * 100)
                    warn("Reported-period ratio does not isolate organic operating leverage; inspect acquisition, FX and earnings-basis effects")
                else:
                    warn("Incremental margin is undefined when revenue change is zero")
            if options.get("revenue_passthrough"):
                warn("Pass-through revenue can distort incremental margin; inspect the operating driver")
        elif formula == "working_capital_to_sales":
            basis = options.get("balance_basis", "average")
            if basis not in {"average", "closing"}:
                raise ValueError("balance_basis must be average or closing")
            if basis == "average" and "balance_start" not in v:
                result["missing_inputs"].append("balance_start")
            if has("balance_end") and (basis == "closing" or has("balance_start")):
                balance = (v["balance_start"] + v["balance_end"]) / 2 if basis == "average" else v["balance_end"]
                emit("selected_balance", balance)
                if has("revenue") and v["revenue"] > 0:
                    emit("ratio_percent", balance / v["revenue"] * 100)
                elif has("revenue"):
                    warn("Working-capital ratio needs positive annual/R12 revenue")
            warn("Balance basis: " + basis + "; ratio to sales, not inventory/payable days")
        elif formula == "invested_capital":
            nonnegative("gross_debt_including_leases", "net_pension_liability", "cash", "non_operating_assets")
            if not result["missing_inputs"]:
                capital = v["group_equity"] + v["gross_debt_including_leases"] + v["net_pension_liability"] - v["cash"] - v["non_operating_assets"]
                emit("invested_capital", capital)
                if capital <= 0:
                    warn("Nonpositive invested capital cannot support a meaningful operating ROIC")
            warn("Goodwill and NCI are already in group equity; leases are already in gross debt")
        elif formula == "operating_roic":
            if has("operating_tax_rate") and not 0 <= v["operating_tax_rate"] <= 1:
                raise ValueError("Operating tax rate must be a fraction between zero and one")
            if has("ebit", "operating_tax_rate"):
                emit("nopat", v["ebit"] * (1 - v["operating_tax_rate"]))
                if v["ebit"] < 0 and v["operating_tax_rate"] > 0:
                    warn("Negative EBIT: the formula assumes a tax benefit that may not be immediately usable")
            if has("invested_capital_start", "invested_capital_end"):
                capital = (v["invested_capital_start"] + v["invested_capital_end"]) / 2
                emit("average_invested_capital", capital)
                if capital <= 0:
                    warn("Operating ROIC needs positive average invested capital")
                elif has("ebit", "operating_tax_rate"):
                    emit("roic_percent", v["ebit"] * (1 - v["operating_tax_rate"]) / capital * 100)
            warn("Explicit operating-tax assumption and two-point average; distinct from issuer ROCE/provider ROIC")
        elif formula == "group_cash_conversion":
            nonnegative("cash_capex", "interest_paid_outside_cfo", "lease_principal_outside_cfo", "noncash_sbc_addback")
            if has("cfo", "cash_capex"):
                cash = v["cfo"] - v["cash_capex"]
                emit("cash_after_capex", cash)
                if has("interest_paid_outside_cfo"):
                    emit("cash_after_capex_and_interest", cash - v["interest_paid_outside_cfo"])
                if has("net_interest_cash_outside_cfo"):
                    emit("cash_after_capex_and_net_interest", cash + v["net_interest_cash_outside_cfo"])
                if has("interest_paid_outside_cfo", "lease_principal_outside_cfo"):
                    after_service = cash - v["interest_paid_outside_cfo"] - v["lease_principal_outside_cfo"]
                    emit("cash_after_debt_like_service", after_service)
                    if has("group_net_income") and v["group_net_income"] > 0:
                        emit("conversion_percent", after_service / v["group_net_income"] * 100)
                    elif has("group_net_income"):
                        warn("Cash conversion is not meaningful with nonpositive group net income")
            if has("noncash_sbc_addback"):
                emit("noncash_sbc_addback", v["noncash_sbc_addback"])
                warn("SBC addback is disclosed separately; compensation remains an economic cost")
            else:
                warn("SBC cash-flow addback has not been supplied or confirmed as zero")
            warn("CFO already includes working capital and taxes; before dividends and not parent-owner FCFE")
        elif formula == "fcf_yield":
            pair = (options.get("cash_flow_scope"), options.get("denominator_scope"))
            if pair not in {("parent_common", "market_cap"), ("firm", "enterprise_value")}:
                warn("Cash-flow ownership/financing scope does not match the valuation denominator")
            elif has("free_cash_flow", "valuation_denominator"):
                if v["valuation_denominator"] > 0:
                    emit("yield_percent", v["free_cash_flow"] / v["valuation_denominator"] * 100)
                    if v["free_cash_flow"] < 0:
                        warn("Negative free cash flow indicates cash consumption, not a cheap positive multiple")
                else:
                    warn("Cash yield needs a positive matching valuation denominator")
        elif formula in {"ev_ebit", "pe"}:
            numerator, denominator = ("enterprise_value", "ebit") if formula == "ev_ebit" else ("price", "diluted_eps")
            if formula == "pe":
                nonnegative("price")
            if has(numerator, denominator):
                if v[denominator] > 0:
                    emit("multiple", v[numerator] / v[denominator])
                    if v[numerator] < 0:
                        warn("Negative enterprise value needs a cash/claim-convention explanation")
                else:
                    warn("Nonpositive earnings do not support a meaningful earnings multiple")
        elif formula in {"volume_ebit", "revenue_ebit"}:
            first, second = ("sales_volume", "ebit_per_tonne") if formula == "volume_ebit" else ("revenue", "ebit_margin")
            nonnegative(first)
            if has(first, second):
                if formula == "revenue_ebit" and abs(v[second]) > 1:
                    raise ValueError("Forecast EBIT margin must be a fraction between -1 and 1")
                emit("ebit", v[first] * v[second])
        elif formula in {"scenario_weighted_values", "expected_cashflow_irr"}:
            if has("years") and (v["years"] != v["years"].to_integral_value() or not 1 <= v["years"] <= 10):
                raise ValueError("Return horizon must be an integer from 1 to 10 years")
            if formula == "scenario_weighted_values":
                weights = [case + "_weight" for case in ("bear", "base", "bull")]
                nonnegative(*v)
                if has(*weights) and sum(v[key] for key in weights) != 1:
                    raise ValueError("Scenario probabilities must sum exactly to one")
                if not result["missing_inputs"]:
                    for field, output in (("present_value", "expected_present_value"), ("future_target", "expected_future_target"), ("annual_dividend_per_share", "expected_annual_dividend_per_share")):
                        emit(output, sum(v[case + "_weight"] * v[case + "_" + field] for case in ("bear", "base", "bull")))
                warn("Scenario weights are explicit judgments; all cash flows use the same horizon and payment timing")
            else:
                nonnegative("expected_annual_dividend_per_share", "expected_future_target")
                if has("price") and v["price"] <= 0:
                    raise ValueError("Expected cash-flow IRR requires a positive initial share price")
                if not result["missing_inputs"]:
                    price, dividend, target, years = (v[k] for k in ("price", "expected_annual_dividend_per_share", "expected_future_target", "years"))
                    years = int(years)
                    emit("initial_cash_flow", -price)
                    emit("annual_interim_cash_flow", dividend)
                    emit("terminal_cash_flow", dividend + target)
                    if dividend == 0 and target == 0:
                        warn("No positive future cash flow: a finite IRR does not exist; total loss remains explicit")
                    else:
                        # Solve for q = 1/(1+IRR). Positive future cash makes PV(q)
                        # strictly increasing, so the root is unique and bounded.
                        def pv(q):
                            return dividend * sum(q ** t for t in range(1, years + 1)) + target * q ** years
                        low = high = Decimal(1)
                        for _ in range(1024):
                            if pv(low) <= price <= pv(high):
                                break
                            if pv(low) > price:
                                high, low = low, low / 2
                            else:
                                low, high = high, high * 2
                        else:
                            raise ValueError("Expected cash-flow IRR could not be bracketed")
                        for _ in range(160):
                            middle = (low + high) / 2
                            if pv(middle) > price:
                                high = middle
                            else:
                                low = middle
                        emit("irr_percent", (1 / ((low + high) / 2) - 1) * 100)
                warn("IRR of expected cash flows is a scenario summary, not an average of scenario IRRs or a promised return")
        elif formula == "valuation_case":
            nonnegative("additional_leases", "pensions", "nci_value", "non_operating_assets", "annual_dividend_per_share", "price")
            if has("years") and (v["years"] != v["years"].to_integral_value() or not 1 <= v["years"] <= 10):
                raise ValueError("Valuation horizon must be an integer from 1 to 10 years")
            if has("required_return") and v["required_return"] < 0:
                raise ValueError("Required return must be a nonnegative fraction")
            if has("required_return") and v["required_return"] > 1:
                warn("Required return exceeds 100%; verify that a fraction, not percentage points, was supplied")
            if has("forecast_shares") and v["forecast_shares"] <= 0:
                raise ValueError("Forecast shares must be positive")
            if has("current_financial_net_debt", "annual_retained_cash", "years"):
                emit("future_financial_net_debt", v["current_financial_net_debt"] - v["annual_retained_cash"] * v["years"])
            if has("forecast_ebit", "exit_multiple"):
                if v["forecast_ebit"] <= 0 or v["exit_multiple"] <= 0:
                    warn("An earnings-multiple valuation needs positive forecast EBIT and exit multiple")
                else:
                    emit("enterprise_value", v["forecast_ebit"] * v["exit_multiple"])
            if not result["missing_inputs"] and "enterprise_value" in result["outputs"]:
                debt = v["current_financial_net_debt"] - v["annual_retained_cash"] * v["years"]
                claims = debt + v["additional_leases"] + v["pensions"] + v["nci_value"]
                equity = v["forecast_ebit"] * v["exit_multiple"] - claims + v["non_operating_assets"]
                emit("total_claims", claims)
                emit("common_equity", equity)
                if equity < 0:
                    warn("Negative common equity: flag financing/distress risk; do not quote a negative share price")
                else:
                    target = equity / v["forecast_shares"]
                    factor = 1 + v["required_return"]
                    terminal = target / factor ** int(v["years"])
                    dividends = sum((v["annual_dividend_per_share"] / factor ** year for year in range(1, int(v["years"]) + 1)), Decimal(0))
                    emit("future_target", target)
                    emit("terminal_pv", terminal)
                    emit("dividend_pv", dividends)
                    emit("present_value", terminal + dividends)
                    if has("price") and v["price"] > 0:
                        emit("price_gap_percent", ((terminal + dividends) / v["price"] - 1) * 100)
                    elif has("price"):
                        warn("A zero price cannot support a percentage valuation gap")
            warn("Retained cash is after common dividends; cash already netted in financial debt is not added again")
    primary = definition["primary_output"]
    result["outputs"].setdefault(primary, {"value": None, "unit": definition["output_units"][primary]})
    return result
