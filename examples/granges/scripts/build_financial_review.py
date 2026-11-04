#!/usr/bin/env python3
"""Review a frozen Gränges packet with fixed formulas; never ingest or run a model."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CASE_DATA = Path(__file__).resolve().parents[1] / "data"
sys.path.insert(0, str(ROOT))
from betaforge.financials import VERSION, evaluate
from betaforge.storage import EvidenceStore
from betaforge.tools import EvidenceTools


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Evidence path escapes its frozen directory")
    return path


def verify_packet(packet):
    snapshot = packet / "snapshot"
    manifest = read_json(snapshot / "manifest.json")
    if digest(inside(snapshot, manifest["database"])) != manifest["database_sha256"]:
        raise ValueError("Frozen database hash mismatch")
    for blob in manifest["blobs"]:
        if digest(inside(snapshot, blob["path"])) != blob["sha256"]:
            raise ValueError("Frozen source blob hash mismatch")
    reports = packet / "reports"
    catalogue, texts = {}, {}
    for report in read_json(reports / "prepared/index.json")["reports"]:
        report_id = report["report_id"]
        if digest(inside(reports, f"sources/{report_id}.pdf")) != report["source_sha256"]:
            raise ValueError("Frozen report PDF hash mismatch")
        text_path = inside(reports, f"prepared/{report_id}.json")
        if digest(text_path) != report["prepared_sha256"]:
            raise ValueError("Frozen prepared report hash mismatch")
        texts[report_id] = read_json(text_path)
        if len(texts[report_id]) != report["pages"]:
            raise ValueError("Prepared page count mismatch")
        catalogue[report_id] = report
    return manifest, catalogue, texts


def verify_quote(evidence, catalogue, texts):
    report_id, page = evidence.get("report_id"), evidence.get("page")
    report = catalogue.get(report_id)
    if not report or evidence.get("sha256") != report["source_sha256"]:
        raise ValueError("Quality fact report hash mismatch")
    if evidence.get("prepared_sha256") != report["prepared_sha256"]:
        raise ValueError("Quality fact prepared hash mismatch")
    if type(page) is not int or not 1 <= page <= report["pages"]:
        raise ValueError("Quality fact page outside report")
    quote = evidence.get("quote")
    if not isinstance(quote, str) or not quote.strip() or " ".join(quote.split()) not in " ".join(texts[report_id][page - 1]["text"].split()):
        raise ValueError("Quality fact quote absent from cited page")
    if evidence.get("source_pointer") != f"/{page - 1}/text":
        raise ValueError("Quality fact source pointer mismatch")


def load_quality_facts(path, catalogue, texts, analysis_date=None):
    body, source_hash = read_json(path), digest(path)
    if body.get("instrument_id") != 426:
        raise ValueError("Quality facts are for a different company")
    records = {}
    for index, fact in enumerate(body["facts"]):
        verify_quote(fact["evidence"], catalogue, texts)
        report_type, year, period = fact["report_type"], fact["year"], fact["period"]
        end = date.fromisoformat(fact["period_end"])
        if analysis_date and end > date.fromisoformat(analysis_date):
            raise ValueError("Quality fact period ends after the frozen analysis date")
        if report_type not in {"year", "quarter", "r12"} or type(year) is not int or type(period) is not int:
            raise ValueError("Invalid quality fact reporting period")
        if end.year != year or (report_type == "year" and period != 5) or (report_type != "year" and period not in range(1, 5)):
            raise ValueError("Quality fact date differs from its reporting period")
        next_month = 1 if report_type == "year" else period * 3 % 12 + 1
        next_year = year + (next_month == 1)
        expected_end = date(next_year, next_month, 1) - timedelta(days=1)
        if end != expected_end:
            raise ValueError("Quality fact date differs from its reporting period")
        start = fact.get("period_start")
        if fact["kind"] == "stock":
            if start is not None:
                raise ValueError("Stock quality facts require a closing date without a flow period start")
        elif fact["kind"] == "flow":
            expected_start = (date(year, 1, 1) if report_type == "year" else
                              date(year, period * 3 - 2, 1) if report_type == "quarter" else
                              date(next_year - 1, next_month, 1))
            if start != expected_start.isoformat():
                raise ValueError("Quality fact flow dates differ from its reporting period")
        else:
            raise ValueError("Quality fact must identify stock or flow")
        key = (fact["metric"], report_type, year, period, end.isoformat())
        if key in records:
            raise ValueError("Duplicate quality fact selection")
        record = dict(fact, id=f"quality:{source_hash[:16]}:{index}",
                      source_id="quality-facts:" + source_hash, pointer=f"/facts/{index}")
        normalized(record)
        records[key] = record
    for note in body.get("notes", []):
        verify_quote(note["evidence"], catalogue, texts)
    return records, body.get("notes", [])


def select_fact(records, metric, year, report_type, period):
    matches = [record for key, record in records.items() if key[:4] == (metric, report_type, year, period)]
    if len(matches) != 1:
        raise ValueError(f"Expected one explicit quality fact selection: {metric}, {year}, {report_type}, {period}")
    return matches[0]


def annual_fact(records, metric, year=2025):
    return select_fact(records, metric, year, "year", 5)


def calculation_period(formula, inputs):
    records = [dict(record, field=field) for field, record in inputs.items() if record is not None]
    warnings, period = EvidenceTools._financial_periods(formula, records)
    flow_field = {"ebit_margin": "revenue", "incremental_ebit_margin": "revenue_current",
                  "operating_roic": "ebit", "working_capital_to_sales": "revenue",
                  "group_cash_conversion": "cfo", "pe": "diluted_eps", "ev_ebit": "ebit"}.get(formula)
    selected = inputs.get(flow_field, {}) if flow_field else {}
    if formula == "invested_capital":
        selected = inputs.get("group_equity", {})
    for key in ("report_type", "period_start", "period_end", "year", "period"):
        if selected.get(key) is not None:
            period[key] = selected[key]
    return warnings, period


def load_market_benchmark(context_path, analysis_date):
    """Verify a saved SIXRX snapshot and reproduce its annualized level return."""
    context_path = Path(context_path).resolve()
    context = read_json(context_path)
    directory = context_path.parent
    manifest_path = inside(directory, context["manifest"])
    if digest(manifest_path) != context["manifest_sha256"]:
        raise ValueError("Market benchmark manifest hash mismatch")
    manifest = read_json(manifest_path)
    if context.get("analysis_date") != analysis_date or manifest.get("analysis_date") != analysis_date:
        raise ValueError("Market benchmark analysis date differs from valuation")
    identity = context.get("benchmark", {})
    if (context.get("context_type") != "historical_market_total_return"
            or manifest.get("context_type") != "historical_market_total_return"
            or manifest.get("series") != "SIXRX"
            or identity.get("symbol") != "SIXRX" or identity.get("currency") != "SEK"
            or identity.get("return_type") != "gross_total_return"
            or identity.get("dividends") != "fully_reinvested"
            or context.get("status") != "verified_from_rounded_public_levels"):
        raise ValueError("Market benchmark identity or return convention is incompatible")
    source_ids = set()
    for source in manifest["sources"]:
        source_ids.add(source["id"])
        if digest(inside(directory, source["file"])) != source["sha256"]:
            raise ValueError("Market benchmark raw source hash mismatch")
    if not {"levels", "methodology", "identity", "publisher_feed"}.issubset(source_ids):
        raise ValueError("Market benchmark lacks supporting sources")
    script = manifest.get("calculation_script")
    if script and digest(inside(directory, script["file"])) != script["sha256"]:
        raise ValueError("Market benchmark calculation source hash mismatch")
    start, end = context["start_observation"], context["end_observation"]
    analysis = date.fromisoformat(analysis_date)
    start_day, end_day = date.fromisoformat(start["date"]), date.fromisoformat(end["date"])
    anchor = analysis.replace(year=analysis.year - 10)
    if context["start_anchor_date"] != anchor.isoformat() or not start_day <= anchor < end_day <= analysis:
        raise ValueError("Market benchmark observation dates are incompatible")
    days = (end_day - start_day).days
    calculation = context["calculation"]
    if calculation["day_count"] != "ACT/365" or calculation["elapsed_days"] != days:
        raise ValueError("Market benchmark day count mismatch")
    first, last = Decimal(start["level"]), Decimal(end["level"])
    stated = Decimal(calculation["annualized_return_percent"])
    if not all(x.is_finite() for x in (first, last, stated)) or first <= 0 or last <= 0:
        raise ValueError("Invalid market benchmark levels or return")
    with localcontext() as arithmetic:
        arithmetic.prec = 40
        reproduced = ((last / first) ** (Decimal(365) / days) - 1) * 100
        if abs(reproduced - stated) > Decimal("1e-30"):
            raise ValueError("Market benchmark return does not match saved levels")
    return dict(context=context, context_path=str(context_path), context_sha256=digest(context_path),
                reproduced_annualized_return_percent=str(reproduced))


def normalized(record):
    unit = record.get("unit")
    if unit in {"currency", "currency/share"} and record.get("currency") != "SEK":
        raise ValueError("Review requires an explicit source currency")
    if unit in {"currency", "SEK", "currency/share", "SEK/share", "SEK/shares", "SEK/tonnes"} and record.get("currency", "SEK") != "SEK":
        raise ValueError("Review requires explicitly selected SEK inputs")
    if unit not in {"currency", "SEK", "currency/share", "SEK/share", "SEK/shares", "SEK/tonnes", "shares", "tonnes", "dimensionless", "multiple"}:
        raise ValueError("Review cannot normalize an ambiguous source unit")
    if isinstance(record["scale"], bool) or isinstance(record["value"], bool):
        raise ValueError("Boolean is not a source amount or scale")
    scale, value = Decimal(str(record["scale"])), Decimal(str(record["value"]))
    if not scale.is_finite() or scale <= 0 or not value.is_finite():
        raise ValueError("Invalid source value or scale")
    with localcontext() as context:
        context.prec = 40
        return value * scale


def build_review(packet, facts_path, run=None, operating_tax_rate=None, tax_reason=None, scenario_weights=None, market_benchmark_context=None, current_facts_path=None):
    packet, facts_path = Path(packet).resolve(), Path(facts_path).resolve()
    if operating_tax_rate is not None and not tax_reason:
        raise ValueError("An operating tax assumption requires a reason")
    if operating_tax_rate is None:
        operating_tax_rate = Decimal("0.20")
        tax_reason = ("Analyst operating-tax proxy of 20%, informed by rounded group effective rates of 20%/19% in FY2025/FY2024 (annual 2025 p148). "
                      "This is not a measured tax rate on EBIT: financing effects, credits, geographic mix and temporary differences can change it. Sensitivity uses 19% and a conservative 25% stress.")
    if scenario_weights is not None and (run is None or len(scenario_weights) != 3):
        raise ValueError("Three explicit scenario weights and an original run are required")
    if market_benchmark_context is not None and scenario_weights is None:
        raise ValueError("A candidate benchmark comparison requires explicit scenario weights")
    manifest, catalogue, texts = verify_packet(packet)
    analysis_date = read_json(packet / "packet.json")["analysis_date"]
    extra, notes = load_quality_facts(facts_path, catalogue, texts, analysis_date)
    current = None
    if current_facts_path is not None:
        current_facts_path = Path(current_facts_path).resolve()
        current, current_notes = load_quality_facts(current_facts_path, catalogue, texts, analysis_date)
        if extra.keys() & current.keys():
            raise ValueError("Duplicate quality fact selection across annual and current facts")
        notes = notes + current_notes
    calculations = []

    def calculate(label, formula, inputs, options=None, display_role=None):
        values = {name: normalized(record) for name, record in inputs.items() if record is not None}
        period_warnings, period = calculation_period(formula, inputs)
        result = evaluate(formula, values, options)
        result.update(label=label, inputs=inputs, options=options or {}, **period)
        result["warnings"].extend(period_warnings)
        if display_role:
            result["display_role"] = display_role
            if formula in {"pe", "ev_ebit"}:
                result["current_period_reason"] = ("Frozen dated closing price paired with the latest selected R12 diluted EPS; economic period follows the earnings denominator."
                    if formula == "pe" else "Latest selected R12 earnings denominator; the provider EV numerator remains a saved unit interpretation with no independently verified valuation date.")
                if formula == "pe":
                    result["price_date"] = inputs["price"].get("period_end")
        result["id"] = "quality-calc:" + hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:24]
        calculations.append(result)
        return result

    def derived(result, output):
        return dict(id=result["id"] + "#" + output, value=result["outputs"][output]["value"],
                    unit=result["outputs"][output]["unit"], scale="1", kind="calculation", currency="SEK",
                    **{key: result[key] for key in ("report_type", "period_start", "period_end", "year", "period") if key in result})

    def assumption(value, unit, reason):
        return dict(id="assumption:" + hashlib.sha256(json.dumps([str(value), unit, reason]).encode()).hexdigest()[:16], value=str(value),
                    unit=unit, scale="1", kind="assumption", basis=reason, currency="SEK")

    with EvidenceStore(packet / "snapshot" / manifest["database"], readonly=True) as store:
        store.validate_report_links(catalogue, instrument_id=426)

        def saved(metric, year, report_type="year", provider="borsdata", period=None):
            matches = [r for r in store.query_financials(426, report_type, [metric], 200)
                       if r.get("year") == year and r.get("provider") == provider
                       and (period is None or r.get("period") == period)]
            if len(matches) != 1:
                raise ValueError(f"Expected one explicit saved selection: {metric}, {year}, {report_type}")
            return matches[0]

        def fact(metric, year=2025):
            return annual_fact(extra, metric, year)

        annual = {year: {"ebit": fact("reported_operating_profit", year), "revenue": fact("net_sales", year)}
                  for year in range(2021, 2026)}
        for year, inputs in annual.items():
            if normalized(inputs["ebit"]) != normalized(saved("operating_Income", year)) or normalized(inputs["revenue"]) != normalized(saved("net_Sales", year)):
                raise ValueError("Reported annual selections differ from the frozen provider figures")
        for year, inputs in annual.items():
            calculate(f"FY{year} reported EBIT margin", "ebit_margin", inputs)
            if year > 2021:
                calculate(f"FY{year} reported group incremental margin; qualified", "incremental_ebit_margin",
                          dict(ebit_current=inputs["ebit"], ebit_previous=annual[year - 1]["ebit"],
                               revenue_current=inputs["revenue"], revenue_previous=annual[year - 1]["revenue"]),
                          dict(comparable_periods=True, revenue_passthrough=True))
        for metric in ("trade_receivables", "inventories", "trade_payables"):
            calculate(f"FY2025 average {metric.replace('_', ' ')} / sales", "working_capital_to_sales",
                      dict(balance_end=fact(metric), balance_start=fact(metric, 2024), revenue=annual[2025]["revenue"]),
                      dict(balance_basis="average"))
        capitals = {}
        for year in (2024, 2025):
            capitals[year] = calculate(f"FY{year} operating invested capital proxy", "invested_capital",
                {name: fact(metric, year) for name, metric in {
                    "group_equity": "group_equity", "gross_debt_including_leases": "gross_debt_including_leases",
                    "net_pension_liability": "net_pension_liability", "cash": "cash_and_equivalents",
                    "non_operating_assets": "associates_joint_ventures_book_value"}.items()})
        roic_inputs = dict(ebit=annual[2025]["ebit"],
                           invested_capital_start=derived(capitals[2024], "invested_capital"),
                           invested_capital_end=derived(capitals[2025], "invested_capital"))
        roic_inputs["operating_tax_rate"] = assumption(operating_tax_rate, "dimensionless", tax_reason)
        roic_inputs["operating_tax_rate"]["evidence"] = next(n["evidence"] for n in notes if n["id"] == "operating-tax-assumption-context")
        calculate("FY2025 operating ROIC; explicit analyst operating-tax proxy", "operating_roic", roic_inputs)
        for rate in (Decimal("0.19"), Decimal("0.25")):
            sensitivity = dict(roic_inputs, operating_tax_rate=assumption(rate, "dimensionless", "Sensitivity only: 19% prior group effective-rate context or 25% conservative tax stress; neither is a measured operating tax rate"))
            calculate(f"FY2025 operating ROIC tax sensitivity: {rate * 100}%", "operating_roic", sensitivity)
        calculate("FY2025 group cash conversion before dividends", "group_cash_conversion",
                  dict(cfo=saved("cash_Flow_From_Operating_Activities", 2025),
                       cash_capex=saved("capital_expenditure_cash_outflow", 2025, provider="issuer_report"),
                       interest_paid_outside_cfo=fact("cash_interest_paid_outside_cfo"),
                       group_net_income=fact("group_net_income")))
        calculate("Q3 2026 group cash bridge; only signed net interest disclosed", "group_cash_conversion",
                  dict(cfo=store.get_observation("obs_f24a1fa72757c04895a9ada8"),
                       cash_capex=store.get_observation("obs_b38bf3ea2cef4ff1f3ba1411"),
                       net_interest_cash_outside_cfo=store.get_observation("obs_22463bf6a71536ee6f27964d"),
                       group_net_income=store.get_observation("obs_ff0d44f1b6c2ca94bcb09d34")))
        if current is not None:
            def current_fact(metric, year=2026, report_type="r12"):
                return select_fact(current, metric, year, report_type, 3)

            for report_type, label in (("quarter", "Q3 2026"), ("r12", "R12 September 2026")):
                periods = {year: dict(ebit=current_fact("reported_operating_profit", year, report_type),
                                      revenue=current_fact("net_sales", year, report_type))
                           for year in (2025, 2026)}
                calculate(label + " reported EBIT margin", "ebit_margin", periods[2026], display_role="current")
                calculate(label + " reported group incremental margin; qualified", "incremental_ebit_margin",
                          dict(ebit_current=periods[2026]["ebit"], ebit_previous=periods[2025]["ebit"],
                               revenue_current=periods[2026]["revenue"], revenue_previous=periods[2025]["revenue"]),
                          dict(comparable_periods=True, revenue_passthrough=True), display_role="current")
            current_capitals = {}
            for year in (2025, 2026):
                current_capitals[year] = calculate(f"September {year} operating invested capital proxy", "invested_capital",
                    {name: current_fact(metric, year, "quarter") for name, metric in {
                        "group_equity": "group_equity", "gross_debt_including_leases": "gross_debt_including_leases",
                        "net_pension_liability": "net_pension_liability", "cash": "cash_and_equivalents",
                        "non_operating_assets": "associates_joint_ventures_book_value"}.items()}, display_role="current")
            calculate("R12 September 2026 operating ROIC; explicit analyst operating-tax proxy", "operating_roic",
                      dict(ebit=current_fact("reported_operating_profit"),
                           invested_capital_start=derived(current_capitals[2025], "invested_capital"),
                           invested_capital_end=derived(current_capitals[2026], "invested_capital"),
                           operating_tax_rate=roic_inputs["operating_tax_rate"]), display_role="current")
            calculate("R12 September 2026 average inventories / sales", "working_capital_to_sales",
                      dict(balance_start=current_fact("inventories", 2025, "quarter"),
                           balance_end=current_fact("inventories", 2026, "quarter"), revenue=current_fact("net_sales")),
                      dict(balance_basis="average"), display_role="current")
            cfo_key = ("statutory_cash_flow_operations", "r12", 2026, 3, "2026-09-30")
            cash_inputs = dict(cfo=current.get(cfo_key) or store.get_observation("obs_07f62b452118f0692883a22c"),
                               cash_capex=store.get_observation("obs_9bf16f556aa471d059ac602a"),
                               group_net_income=current_fact("group_net_income"))
            net_interest_key = ("net_interest_cash_outside_cfo", "r12", 2026, 3, "2026-09-30")
            if net_interest_key in current:
                cash_inputs["net_interest_cash_outside_cfo"] = current[net_interest_key]
            calculate("R12 September 2026 group cash conversion before dividends", "group_cash_conversion",
                      cash_inputs, display_role="current")
        calculate("Parent-common FCF yield; ownership-matched cash flow not established", "fcf_yield", {},
                  dict(cash_flow_scope="parent_common", denominator_scope="market_cap"))
        price = store.get_observation("obs_5f3162480174db7f08137b5b")
        calculate("Dated price / R12 reported diluted EPS", "pe",
                  dict(price=price, diluted_eps=saved("reported_eps_diluted", 2026, "r12", "issuer_report")),
                  display_role="current" if current is not None else None)
        provider_roic = store.get_observation("obs_16fda6d7672e1f3c38c3ae4b")

        parity, probability_proposal, benchmark_comparison = None, None, None
        if run is not None:
            run = Path(run).resolve()
            old_inputs = {r["id"]: r for r in read_json(run / "inputs.json")}

            def prior(identifier):
                record = old_inputs[identifier]
                if record.get("kind") == "report":
                    report_id, page = record["report_id"], record["page"]
                    if " ".join(record["quote"].split()) not in " ".join(texts[report_id][page - 1]["text"].split()):
                        raise ValueError("Saved valuation input quote absent from frozen report")
                return record

            old = {c["id"]: c for c in read_json(run / "calculations.json")}
            parity = {"original_run": str(run), "inputs_sha256": digest(run / "inputs.json"),
                      "calculations_sha256": digest(run / "calculations.json"), "checks": {}}
            case_ids = {
                "bear": ("input:89c1f161f7c5209d1562", "input:d7ce4cbec87bc8609273", "input:f18ab01cf809171021a4", "input:6f36213debc1431f29e4", "calc:58483a4265ad1711632e", "calc:44251337e56efb345589"),
                "base": ("input:c03895a0c38dfa246e66", "input:6e38393a2b4c8338300e", "input:1d7ee1df9a5b369453e6", "input:883d6f98904105394487", "calc:ec089d26955fb8159230", "calc:791e2ac113fabdd105dc"),
                "bull": ("input:210d6fc20c8767f9cc22", "input:a2dba4a20ee7638eabfe", "input:35fca68df39c69f6798b", "input:a46083fd60229c15788f", "calc:8bb04786888b2fb17641", "calc:9e9577bc76984e4d0163")}
            cases = {}
            for case, (volume, per_tonne, multiple, retained_cash, old_target, old_pv) in case_ids.items():
                forecast = calculate(f"Preserved {case} operating drivers", "volume_ebit",
                                     dict(sales_volume=prior(volume), ebit_per_tonne=prior(per_tonne)))
                result = calculate(f"Preserved {case} EV/EBIT valuation; original assumptions", "valuation_case",
                    dict(forecast_ebit=derived(forecast, "ebit"), exit_multiple=prior(multiple),
                         current_financial_net_debt=store.get_observation("obs_e74767f47c89884763567078"),
                         annual_retained_cash=prior(retained_cash), years=prior("input:7211be03731c4f826fc4"),
                         additional_leases=store.get_observation("obs_3b3bb59e28d1facc650d497b"), pensions=prior("input:5fd8080ec75c51aca847"),
                         nci_value=store.get_observation("obs_4024d098807adab4327644b4"),
                         non_operating_assets=prior("input:5104335396dcb215a6b3"),
                         forecast_shares=store.get_observation("obs_f97da8105dea2fb518c9a7e4"),
                         annual_dividend_per_share=prior("input:1f61e7e3dbc941644097"),
                         required_return=prior("input:053e3a1cdaa061d73f9c"), price=price))
                result["preserved_assumptions"] = [prior(identifier) for identifier in (
                    "input:33be41b75e8b6b338a8b", "input:b94b7bf91e02b6804b43", "input:e8df20b5149765e05fe4")]
                parity["checks"][case] = {key: result["outputs"][key]["value"] == old[identifier]["result"]
                                          for key, identifier in (("future_target", old_target), ("present_value", old_pv))}
                cases[case] = result
            if not all(check for case in parity["checks"].values() for check in case.values()):
                raise ValueError("Preserved valuation does not match original saved outputs")
            if scenario_weights is not None:
                proposal_reason = "Explicit invocation of analyst-proposed case weights; conditional on the three modeled going-concern cases, with an unquantified distress/dilution tail. Subjective and editable, not calibrated or adopted defaults."
                weighted_inputs = {"years": prior("input:7211be03731c4f826fc4")}
                for (case, result), weight in zip(cases.items(), scenario_weights):
                    weighted_inputs[case + "_weight"] = assumption(weight, "dimensionless", case + ": " + proposal_reason)
                    weighted_inputs[case + "_present_value"] = derived(result, "present_value")
                    weighted_inputs[case + "_future_target"] = derived(result, "future_target")
                    weighted_inputs[case + "_annual_dividend_per_share"] = prior("input:1f61e7e3dbc941644097")
                weighted = calculate("Conditional analyst proposal: probability-weighted case values", "scenario_weighted_values", weighted_inputs)
                candidate = calculate("Conditional analyst proposal: IRR of expected cash flows", "expected_cashflow_irr",
                    dict(price=price, expected_annual_dividend_per_share=derived(weighted, "expected_annual_dividend_per_share"),
                         expected_future_target=derived(weighted, "expected_future_target"), years=prior("input:7211be03731c4f826fc4")))
                probability_proposal = dict(weights={case: str(weight) for case, weight in zip(cases, scenario_weights)},
                                            basis=proposal_reason, rationale_path="examples/granges/docs/research/scenario-probabilities-proposal.md")
                if market_benchmark_context is not None:
                    benchmark = load_market_benchmark(market_benchmark_context, "2026-11-01")
                    candidate_return = candidate["outputs"]["irr_percent"]["value"]
                    index_return = benchmark["reproduced_annualized_return_percent"]
                    with localcontext() as arithmetic:
                        arithmetic.prec = 40
                        difference = Decimal(candidate_return) - Decimal(index_return)
                    benchmark_comparison = dict(candidate_calculation=candidate["id"] + "#irr_percent",
                        candidate_annualized_return_percent=candidate_return,
                        benchmark_annualized_return_percent=index_return,
                        difference_percentage_points=str(difference), source=benchmark,
                        interpretation="The conditional candidate IRR is below the historical SIXRX CAGR" if difference < 0 else "The conditional candidate IRR is at or above the historical SIXRX CAGR",
                        limits=["The candidate is a subjective three-year going-concern scenario summary; an unquantified distress/dilution tail remains.",
                                "SIXRX is a trailing ten-year historical gross SEK total return from rounded public levels, not a future return forecast.",
                                "The index reinvests dividends. Candidate IRR accounts for the timing of interim cash distributions; it does not model their reinvested terminal wealth.",
                                "The annual-rate difference is an indicative opportunity-cost comparison, not an identical holding-period or reinvestment experiment, and does not change the original 10% valuation discount rate."])
            calculate("Provider-convention EV / R12 reported EBIT; separate from full claim bridge", "ev_ebit",
                      dict(enterprise_value=prior("input:9f1230aebe6a5a6a045e"), ebit=saved("operating_Income", 2026, "r12", period=3)),
                      display_role="current" if current is not None else None)

    review = dict(schema_version=1, formula_version=VERSION, instrument_id=426,
                frozen_analysis_date=analysis_date, reviewed_at=datetime.now(timezone.utc).isoformat(),
                packet=str(packet), database_sha256=manifest["database_sha256"],
                quality_facts=str(facts_path), quality_facts_sha256=digest(facts_path),
                calculations=calculations, preserved_valuation=parity, probability_proposal=probability_proposal,
                market_benchmark_comparison=benchmark_comparison,
                provider_roic=provider_roic,
                supplier_finance=[fact(metric) for metric in ("supplier_finance_in_trade_payables", "supplier_finance_in_other_liabilities", "supplier_finance_total")],
                notes=notes, interpretation=[
                    "Reported margins describe consolidated history. Full-year EBIT/sales selections were verified against the annual statements and matched the saved provider numbers. Incremental margins are descriptive reported-group changes, not isolated organic operating leverage; M&A, FX, comparability items and aluminium pass-through affect them.",
                    "Operating capital deducts the carrying value of associates/JVs because their result is outside reported EBIT. This is an explicit classification proxy; two balance dates do not measure intrayear funding peaks.",
                    f"The operating ROIC uses an explicit analyst {operating_tax_rate * 100}% operating-tax proxy, with 19%/25% sensitivity. The source context is FY2025/FY2024 effective group tax rates and the tax reconciliation. Provider ROIC retains its distinct source-defined profit/capital basis and unresolved provider unit metadata.",
                    "Supplier-finance components remain identified inside their reported liabilities. Reclassifying them as valuation debt requires a separate, consistent convention.",
                    "The approved post-lease group cash conversion is unavailable without verified cash lease principal. FY2025 gross cash interest and Q3 net cash interest are kept distinct. No parent-owner FCF yield is inferred.",
                    "The base valuation is an unchanged EV/EBIT scenario with explicit debt, leases, pensions, NCI and dividends. It keeps the old assumptions of NCI at book value, unchanged lease/pension claims and unchanged issued-share count as a dilution proxy. It is not a full DCF or a new investment recommendation."])
    if current is not None:
        review.update(current_facts=str(current_facts_path), current_facts_sha256=digest(current_facts_path),
                      diagnostic_cutoff=dict(analysis_date=analysis_date, quarter_end="2026-09-30",
                                             r12_start="2025-10-01", r12_end="2026-09-30"),
                      current_data_limits=[
                          "Latest profitability uses reported consolidated Q3 and R12 figures with matched prior-year periods. Aluminium pass-through, acquisitions, FX and one-offs qualify incremental margins.",
                          "Latest inventory/sales and operating ROIC use September 2025/2026 closing balances and the matching R12 flow. Two-point averages do not measure intrayear capital peaks; the annual operating-tax proxy remains an assumption.",
                          "Trade receivables and trade payables / sales retain FY2025 annual balances: interim receivable/payable aggregates do not establish actual trade components.",
                          "R12 statutory CFO uses the saved provider quarter-sum convention unless an explicit report fact is supplied. Rounded issuer annual/YTD roll-forward totals can differ; the selected records remain visible.",
                          "Gross outside-CFO cash interest and lease principal remain missing. Known cash after capex and any verified signed net-interest subtotal are shown; neither establishes final group conversion or parent-common FCF."])
    return review


def render_markdown(review):
    lines = ["# Gränges financial quality review", "", "Deterministic review of the frozen 1 November 2026 evidence. New quality facts are separate from the original valuation.", ""]
    for statement in review["interpretation"]:
        lines += ["- " + statement]
    if review.get("current_data_limits"):
        lines += ["", "## Latest diagnostic limits", ""]
        lines += ["- " + limit for limit in review["current_data_limits"]]
    lines += ["", "| Calculation | Primary output | Missing input or qualification |", "|---|---|---|"]
    for calc in review["calculations"]:
        output = calc["outputs"][calc["primary_output"]]
        display = output["value"]
        display = f"{Decimal(display):,.4f} {output['unit']}" if display is not None else "Unavailable"
        qualification = ', '.join(calc['missing_inputs'])
        if output["value"] is None and not qualification:
            qualification = calc["warnings"][0] if calc["warnings"] else "See detailed outputs"
        lines.append(f"| {calc['label']} | {display} | {qualification or '—'} |")
    for calc in review["calculations"]:
        lines += ["", "## " + calc["label"], "", calc["formula_text"], "", "Calculation ID: `" + calc["id"] + "`.", ""]
        for key, record in calc["inputs"].items():
            if record is not None:
                lines.append(f"- `{key}` = {record['value']} × {record['scale']} {record['unit']}; `{record['id']}`; {record.get('basis', '')}.")
        for key, output in calc["outputs"].items():
            lines.append(f"- `{key}`: {output['value'] if output['value'] is not None else 'Unavailable'} {output['unit']}.")
        lines += ["- " + warning for warning in calc["warnings"]]
    if review["preserved_valuation"]:
        lines += ["", "Original bear/base/bull targets and present values match exactly: " + str(review["preserved_valuation"]["checks"]) + "."]
    if review["probability_proposal"]:
        lines += ["", "Probability weights: " + str(review["probability_proposal"]["weights"]) + ". " + review["probability_proposal"]["basis"]]
    if review["market_benchmark_comparison"]:
        comparison = review["market_benchmark_comparison"]
        lines += ["", "## Historical market comparison", "",
                  f"Conditional candidate cash-flow IRR: {Decimal(comparison['candidate_annualized_return_percent']):.4f}%. SIXRX trailing ten-year gross total-return CAGR: {Decimal(comparison['benchmark_annualized_return_percent']):.4f}%. Difference: {Decimal(comparison['difference_percentage_points']):.4f} percentage points.", ""]
        lines += ["- " + limit for limit in comparison["limits"]]
    lines += ["", "The JSON file contains complete selected source records, PDF hashes, page locations and formula outputs.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=ROOT / "data/granges-codex/packet-20261101")
    parser.add_argument("--facts", type=Path, default=CASE_DATA / "quality-facts-20261103.json")
    parser.add_argument("--current-facts", type=Path, help="Verified latest-quarter/R12 facts; annual-only behavior when omitted")
    parser.add_argument("--original-run", type=Path, default=ROOT / "data/granges-codex/runs/20261101-full")
    parser.add_argument("--output", required=True, help="New directory; existing outputs are never overwritten")
    parser.add_argument("--operating-tax-rate", type=Decimal)
    parser.add_argument("--tax-reason")
    parser.add_argument("--scenario-weights", type=Decimal, nargs=3, metavar=("BEAR", "BASE", "BULL"), help="Explicit analyst-proposed fractions; no default probabilities")
    parser.add_argument("--market-benchmark-context", help="Saved SIXRX context with verified manifest/raw sources and matching analysis date")
    args = parser.parse_args(argv)
    output = Path(args.output).resolve()
    if output.exists():
        parser.error("Output directory already exists")
    if any(output.is_relative_to(Path(source).resolve()) for source in (args.packet, args.original_run)):
        parser.error("Output must be outside frozen evidence and the original model run")
    review = build_review(args.packet, args.facts, args.original_run, args.operating_tax_rate, args.tax_reason, args.scenario_weights, args.market_benchmark_context, args.current_facts)
    output.mkdir(parents=True)
    (output / "review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    (output / "review.md").write_text(render_markdown(review))
    print(f"Saved {len(review['calculations'])} transparent calculations to {output}")


if __name__ == "__main__":
    main()
