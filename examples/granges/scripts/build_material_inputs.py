"""Attach scoped input decisions to an existing Gränges review; preserve its results."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from decimal import Decimal, localcontext
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from betaforge.saved_view import checked_path
from betaforge.storage import EvidenceStore
from examples.granges.scripts.build_financial_review import normalized, verify_packet


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def build_material_inputs(review, packet):
    """Select the already-reviewed sources; do not evaluate valuation formulas."""
    manifest, catalogue, texts = verify_packet(packet)
    if review["instrument_id"] != 426 or review["database_sha256"] != manifest["database_sha256"]:
        raise ValueError("Review differs from the frozen company evidence")
    calculations = review["calculations"]
    narrative_path = Path(review["preserved_valuation"]["original_run"]) / "answer.md"
    narrative_body = narrative_path.read_bytes()
    paragraphs = narrative_body.decode().split("\n\n")

    def narrative(prefix):
        found = [p for p in paragraphs if p.startswith(prefix)]
        if len(found) != 1:
            raise ValueError("Expected one saved rationale paragraph: " + prefix)
        return found[0]

    def rationale_evidence(quote):
        return dict(source_id="saved-narrative:" + hashlib.sha256(narrative_body).hexdigest(),
                    section="9. Three-year operating valuation", quote=quote)

    def report_evidence(page, row):
        quote = next(line.strip() for line in texts["granges-q3-2026"][page - 1]["text"].splitlines()
                     if line.strip().startswith(row))
        return dict(report_id="granges-q3-2026", page=page, row=row, quote=quote,
                    source_pointer=f"/{page - 1}/text",
                    sha256=catalogue["granges-q3-2026"]["source_sha256"],
                    prepared_sha256=catalogue["granges-q3-2026"]["prepared_sha256"])

    def report_derivation(identifier, evidence, values, labels, signs, selected):
        with localcontext() as arithmetic:
            arithmetic.prec = 40
            result = sum((Decimal(value) * sign for value, sign in zip(values, signs)), Decimal(0))
        return dict(id="reconciliation:" + identifier, value=str(result), scale="1000000", unit="SEK",
                    currency="SEK", kind="calculation", basis="Derived report reconciliation, not a new forecast",
                    report_type="r12", period_start=selected["period_start"], period_end=selected["period_end"],
                    evidence=evidence, derivation=dict(formula=" + ".join(("− " if sign < 0 else "") + label for label, sign in zip(labels, signs)),
                    inputs=[dict(label=label, value=value, scale="1000000", unit="SEK") for label, value in zip(labels, values)]))

    def calculation(formula, *, current=False, label=None):
        found = [c for c in calculations if c["formula"] == formula
                 and (not current or c.get("display_role") == "current" and c.get("report_type") == "r12")
                 and (label is None or c["label"] == label)]
        if len(found) != 1:
            raise ValueError("Expected one explicit calculation selection: " + formula)
        return found[0]

    rows = []

    def add(key, label, definition, selected, uses, reason, *, candidates=(), limits=(), status="matched", evidence=()):
        selected = deepcopy(selected)
        source_evidence = selected.get("evidence", []) if selected else []
        if isinstance(source_evidence, dict):
            source_evidence = [source_evidence]
        if selected and not source_evidence and selected.get("report_id") in catalogue:
            source_evidence = [dict(report_id=selected["report_id"], page=selected["page"],
                                    quote=selected.get("quote"),
                                    sha256=catalogue[selected["report_id"]]["source_sha256"],
                                    prepared_sha256=catalogue[selected["report_id"]]["prepared_sha256"])]
        rows.append(dict(id=key, label=label, definition=definition,
                         definition_status="documented", reconciliation_status=status,
                         selected=selected, candidates=list(candidates), selection_reason=reason,
                         valuation_uses=list(uses), limitations=list(limits),
                         evidence=deepcopy(source_evidence) + list(evidence)))

    def output(calc, name):
        return dict(id=calc["id"] + "#" + name, **calc["outputs"][name], scale="1",
                    kind="calculation", basis=calc["label"], currency="SEK",
                    report_type=calc.get("report_type"), period_start=calc.get("period_start"),
                    period_end=calc.get("period_end"))

    with EvidenceStore(packet / "snapshot" / manifest["database"], readonly=True) as store:
        def provider(metric, family="r12", year=2026, period=3):
            found = [r for r in store.query_financials(426, family, [metric], 200)
                     if r.get("provider") == "borsdata" and r.get("year") == year and r.get("period") == period]
            if len(found) != 1:
                raise ValueError("Expected one provider candidate: " + metric)
            return found[0]

        def compare(selected, candidate, explanation, definition="unresolved"):
            residual, status = None, "not_comparable"
            try:
                with localcontext() as arithmetic:
                    arithmetic.prec = 40
                    difference = normalized(selected) - normalized(candidate)
                residual = dict(value=str(difference), unit=selected.get("currency") if selected["unit"] == "currency" else selected["unit"],
                                formula="selected value × selected scale − candidate value × candidate scale")
                status = "matched" if difference == 0 else "disagrees"
            except ValueError:
                explanation += " Candidate unit is unresolved; no normalized numeric residual is asserted."
            return dict(record=candidate, definition_status=definition,
                        reconciliation_status=status, comparison_basis=explanation, residual=residual)

        margin = calculation("ebit_margin", current=True)
        sales, ebit = margin["inputs"]["revenue"], margin["inputs"]["ebit"]
        add("r12-sales", "R12 net sales", "Consolidated reported net sales for the trailing twelve months, including metal-price pass-through.", sales,
            ["EBIT and incremental margins", "Inventory intensity", "Historical context for operating forecasts"],
            "Use the issuer's displayed R12 total and matching duration; retain the provider's rounded quarter-sum view separately.",
            candidates=[compare(sales, provider("net_Sales"), "Same R12 end date; displayed issuer total versus provider quarter aggregation.")],
            limits=["Revenue growth is not automatically organic growth or fabrication growth."])
        add("r12-ebit", "R12 reported EBIT", "Consolidated operating profit before finance and tax, with reported comparability costs retained; distinct from adjusted EBIT.", ebit,
            ["Reported profitability", "Operating ROIC", "Current EV/EBIT sanity check"],
            "Use the explicit reported line for consistent diagnostic history. Adjusted earnings remain separate evidence for forecast interpretation.",
            candidates=[compare(ebit, provider("operating_Income"), "Reported R12 earnings on the same issuer and period.")],
            limits=["Fire costs, acquisitions, FX and pass-through effects qualify incremental-margin interpretation."])
        pe = calculation("pe")
        eps = pe["inputs"]["diluted_eps"]
        add("diluted-eps", "R12 diluted EPS", "Profit attributable to parent shareholders per weighted-average diluted share over the earnings period.", eps,
            ["P/E sanity check"], "Use the report's explicitly diluted EPS, rather than assuming the provider EPS has that share basis.",
            candidates=[compare(eps, provider("earnings_Per_Share"), "Same R12 end date; provider basic/diluted denominator policy remains unresolved.")])
        add("dated-price", "Frozen share price", "Dated daily closing price in SEK per share at the analysis cutoff; not an annual average or live quote.", pe["inputs"]["price"],
            ["Entry-price comparison", "P/E", "Conditional expected cash-flow return"],
            "Use the latest saved trading close on or before the frozen analysis date.",
            limits=["The price is intentionally frozen to the original analysis; a later review date does not refresh it."])
        base = calculation("valuation_case", label="Preserved base EV/EBIT valuation; original assumptions")
        bridge = base["inputs"]
        definitions = {
            "current_financial_net_debt": ("Financial net debt", "Issuer financial net debt excluding leases; cash is already netted.", "Deduct this claim once; preserve the displayed APM and its rounding residual.", "net_Debt"),
            "additional_leases": ("Lease liabilities", "Lease debt deducted separately because the selected financial net debt excludes it.", "Keep the full scenario claims convention explicit and consistent with its EBIT/multiple basis.", None),
            "pensions": ("Pension claim", "Reported pension obligation used as an additional debt-like claim under the saved scenario convention.", "Keep the original supplementary deduction visible; it is a valuation convention.", None),
            "nci_value": ("Minority ownership claim", "Non-controlling-interest book equity used as an explicit fair-value proxy in the common-equity bridge.", "Consolidated earnings include minority-owned operations, so their claim needs an explicit deduction.", None),
            "forecast_shares": ("Forecast share denominator", "Latest disclosed issued shares held unchanged to the valuation horizon as a forecast proxy.", "Issued shares match the current ownership denominator better than historical weighted EPS shares.", "number_Of_Shares"),
            "non_operating_assets": ("Separate surplus-asset credit", "Explicit saved assumption for separately valued assets outside operating enterprise value.", "Credit assets only when separately supportable; do not add all provider financial_Assets as surplus value.", None),
        }
        for field, (label, definition, reason, metric) in definitions.items():
            selected = bridge[field]
            if field == "pensions":
                verified = calculation("operating_roic", current=True)
                capital_id = verified["inputs"]["invested_capital_end"]["id"].split("#")[0]
                current_pension = next(c for c in calculations if c["id"] == capital_id)["inputs"]["net_pension_liability"]
                if normalized(current_pension) != normalized(selected):
                    raise ValueError("Pension decision differs from preserved claim")
                selected = dict(selected, report_type=current_pension["report_type"], period_end=current_pension["period_end"],
                                year=current_pension["year"], period=current_pension["period"],
                                basis=current_pension["basis"], evidence=current_pension["evidence"],
                                note="Closing-date metadata verified from current report fact; the original frozen input remains unchanged")
            candidates = [compare(selected, provider(metric, "quarter"), "Same closing date; compare the selected claim/share convention, not a universal provider formula.")] if metric else []
            limits = []
            if field == "current_financial_net_debt":
                limits = ["Displayed gross debt less cash/receivables less leases leaves a one-MSEK residual; retain displayed total.", "Earlier years used different provider debt conventions; this selection is scoped to the current period."]
            elif field == "nci_value":
                limits = ["Book equity is not observed fair value; unchanged future NCI is a scenario assumption."]
            elif field == "forecast_shares":
                limits = ["Current treasury holdings and future dilution are not independently established; weighted-average EPS shares have another purpose."]
            add(field.replace("_", "-"), label, definition, selected, ["Enterprise value to common equity bridge"], reason,
                candidates=candidates, limits=limits, status="not_comparable" if selected.get("kind") == "assumption" else "matched")
        cash = calculation("group_cash_conversion", current=True)
        for field, label, meaning, reason in (
            ("cfo", "R12 statutory CFO", "Cash flow from operating activities after working-capital movement and cash tax; consolidated group scope.", "Use statutory CFO for the cash bridge, distinct from the issuer's similarly named operating-cash-flow APM."),
            ("cash_capex", "R12 cash capex", "Cash expenditure on property, equipment and intangible assets as a positive outflow magnitude.", "Subtract actual cash capex, not total investing cash flow, which may include acquisitions or disposals."),
            ("group_net_income", "R12 group profit", "Consolidated reported profit after financing and tax, including NCI.", "Match the group cash numerator; parent-owner profit is a different ownership scope."),
            ("net_interest_cash_outside_cfo", "R12 signed net cash interest", "Financing cash interest paid and received combined, signed; annual plus current YTD less prior YTD.", "Show this known intermediate separately; it cannot substitute for gross cash interest paid in the primary conversion."),
        ):
            selected = cash["inputs"].get(field)
            if selected is None:
                continue
            candidates = []
            reconciliation = "derived_match" if field in {"cfo", "net_interest_cash_outside_cfo"} else "matched"
            if field == "group_net_income":
                candidates = [compare(selected, provider("profit_To_Equity_Holders"), "Different group/parent attribution scopes; residual is arithmetic, not a reconciliation failure.")]
                candidates[0]["reconciliation_status"] = "not_comparable"
            evidence = []
            if field == "cfo":
                quarter_evidence = report_evidence(21, "Operating activities")
                annual_evidence = report_evidence(16, "Cash flow from operating activities")
                quarters = re.findall(r"-?\d[\d,]*", quarter_evidence["quote"])
                annual_ytd = re.findall(r"-?\d[\d,]*", annual_evidence["quote"])
                if len(quarters) != 9 or len(annual_ytd) != 5:
                    raise ValueError("Unexpected report cash-flow table extraction")
                quarters = [value.replace(",", "") for value in quarters[:4]]
                annual_ytd = [value.replace(",", "") for value in annual_ytd]
                quarter_sum = report_derivation("cfo-four-quarters", quarter_evidence, quarters,
                                               ["Q3 2026", "Q2 2026", "Q1 2026", "Q4 2025"], [1, 1, 1, 1], selected)
                alternative = report_derivation("cfo-annual-ytd", annual_evidence,
                                                [annual_ytd[4], annual_ytd[2], annual_ytd[3]],
                                                ["FY2025", "Jan–Sep2026", "Jan–Sep2025"], [1, 1, -1], selected)
                candidates = [compare(selected, quarter_sum, "Exact sum of the four displayed statutory quarterly CFO rows.", "documented"),
                              compare(selected, alternative, "Annual plus current YTD less prior YTD; displayed rounding leaves a retained residual.", "documented")]
                reconciliation = "derived_match" if any(item["reconciliation_status"] == "matched" for item in candidates) else "disagrees"
                if selected.get("provider") != "borsdata":
                    reason = "Use the explicitly selected report CFO; preserve both report derivations and the provider quarter-sum candidate with their residuals. " + reason
                    candidates.append(compare(selected, provider("cash_Flow_From_Operating_Activities"),
                                              "Retained provider R12 CFO, independent of the explicit report override."))
                evidence = [quarter_evidence, annual_evidence]
            add(field.replace("_", "-"), label, meaning, selected, ["Cash-quality diagnostic; retained-cash forecast challenge"], reason,
                candidates=candidates, status=reconciliation,
                limits=["The primary post-lease conversion remains unavailable until gross outside-CFO interest and cash lease principal are verified."], evidence=evidence)
        for key, label in (("interest_paid_outside_cfo", "Fresh gross cash interest"), ("lease_principal_outside_cfo", "Fresh cash lease principal")):
            add(key.replace("_", "-"), label, "The specific cash outflow required by the adopted group cash-conversion formula.", None,
                ["Primary post-lease group cash conversion"], "Keep missing: combined net interest and aggregate loan repayment do not establish this cash component.",
                status="not_comparable", evidence=[dict(report_id="granges-q3-2026", page=16, row="Financing cash flow", sha256=catalogue["granges-q3-2026"]["source_sha256"])])
        roic = calculation("operating_roic", current=True)
        add("operating-tax", "Operating tax assumption", "Explicit assumed tax rate on operating earnings; not the measured consolidated effective tax rate.", roic["inputs"]["operating_tax_rate"],
            ["R12 operating NOPAT and ROIC"], "Retain the disclosed operating-tax proxy and annual tax reconciliation as context; the R12 EBIT and capital balances are current.",
            status="not_comparable", limits=["An older annual source can support an explicit assumption without turning it into a measured current rate."])
        for calc in [c for c in calculations if c["formula"] == "invested_capital" and c.get("display_role") == "current"]:
            closing = calc["period_end"]
            for field, selected in calc["inputs"].items():
                add("capital-" + closing + "-" + field.replace("_", "-"), closing + " · " + field.replace("_", " "),
                    selected["basis"], selected, ["Matched opening/closing capital for R12 operating ROIC"],
                    "Use the same capital convention at both R12 endpoints. Group equity contains goodwill/NCI; gross debt contains leases; associates/JV are deducted once.",
                    limits=["Two closing balances do not measure intra-year capital peaks; carrying values are classification proxies."])
        for calc in [c for c in calculations if c["formula"] == "working_capital_to_sales"]:
            if calc.get("display_role") != "current" and "trade" not in calc["label"]:
                continue
            for field in ("balance_start", "balance_end"):
                selected = calc["inputs"][field]
                add("working-" + selected["metric"] + "-" + selected["period_end"], selected["metric"].replace("_", " ") + " · " + selected["period_end"],
                    selected["basis"], selected, [calc["label"]],
                    "Use actual operating balances and a matching annual/R12 sales denominator; do not substitute aggregate receivables or all current liabilities.",
                    limits=[] if calc.get("display_role") == "current" else ["Annual-only fallback: the latest interim does not disclose the separate trade balance."])
        for calc in [c for c in calculations if c["formula"] in {"volume_ebit", "valuation_case"}]:
            case = calc["label"].split()[1]
            fields = ("sales_volume", "ebit_per_tonne") if calc["formula"] == "volume_ebit" else ("exit_multiple", "annual_retained_cash")
            for field in fields:
                mechanism = narrative("**" + case.title() + ":**")
                support = narrative("The profit-per-tonne assumptions") if field in {"sales_volume", "ebit_per_tonne"} else (
                    narrative("The multiples are chosen") if field == "exit_multiple" else narrative("These amounts are **after**"))
                reason = mechanism.replace("**", "") + " " + support.replace("**", "")
                add(case + "-" + field.replace("_", "-"), case.title() + " · " + field.replace("_", " "),
                    "Saved scenario assumption, not a Börsdata observation or a reported financial result.", calc["inputs"][field],
                    [calc["label"]], reason,
                    status="not_comparable", limits=["Conditional scenario input; its precision does not establish forecast accuracy."],
                    evidence=[rationale_evidence(mechanism), rationale_evidence(support)])
        for field in ("years", "required_return", "annual_dividend_per_share"):
            add("common-" + field.replace("_", "-"), field.replace("_", " ").title(),
                "Explicit common assumption in the saved valuation; the annual dividend is a future annual payment, not a sum of repeated quarterly provider fields.", bridge[field],
                ["Scenario target and present-value timing"], "Preserve the existing horizon, discount and distribution assumptions; separate them from measured financial history.", status="not_comparable")
        ev = calculation("ev_ebit")
        ev_candidate = [r for r in store.query_financials(426, "r12", ["kpi_49"], 200)
                        if r.get("year") == 2026 and r.get("period") == 3 and r.get("basis") == "year/mean"]
        if len(ev_candidate) != 1 or ev_candidate[0]["value"] != ev["inputs"]["enterprise_value"]["value"]:
            raise ValueError("Saved EV interpretation differs from frozen KPI candidate")
        add("provider-ev", "Provider-convention EV", "Provider EV used for a separate market-multiple sanity check; not the full scenario enterprise-to-equity convention.", ev["inputs"]["enterprise_value"],
            ["EV/EBIT sanity check"], "Keep the explicit MSEK unit interpretation and observed net-debt-only convention separate from the full scenario claims bridge.",
            candidates=[compare(ev["inputs"]["enterprise_value"], ev_candidate[0], "Same raw numeric value under an explicit MSEK interpretation; economic valuation date and provider unit metadata are unresolved.")],
            status="not_comparable", limits=["Provider KPI unit metadata and exact valuation date were unresolved in this frozen capture; current refers to the R12 earnings denominator, not a verified live EV."])
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate material input decision")
    return rows


def render_notes(review, rows):
    lines = ["# Material input decisions", "", "Frozen analysis date: " + review["frozen_analysis_date"] + ". Original valuation and scenario assumptions are preserved.",
             "", "Definition status and numeric reconciliation are separate. Provider definitions remain scoped; a matching value does not prove a universal formula.", ""]
    for row in rows:
        selected = row["selected"]
        lines += ["## " + row["label"], "", row["definition"], "",
                  "Selected: " + (f"{selected['value']} × {selected['scale']} {selected['unit']}; {selected.get('period_start') or ''} to {selected.get('period_end') or 'scenario horizon'}; `{selected['id']}`" if selected else "Unavailable"),
                  "", "Why: " + row["selection_reason"], "", "Use: " + "; ".join(row["valuation_uses"]),
                  "", "Definition: " + row["definition_status"] + "; reconciliation: " + row["reconciliation_status"] + "."]
        lines += ["- " + limit for limit in row["limitations"]]
        for item in row["evidence"]:
            if item.get("report_id"):
                lines.append("- Evidence: " + item["report_id"] + ", physical page " + str(item.get("page", "")) + "; " + str(item.get("row", "")))
            else:
                lines.append("- Saved analysis: " + str(item.get("source_id", "")) + "; " + str(item.get("section", "")))
        for candidate in row["candidates"]:
            r = candidate["record"]
            lines.append(f"- Candidate `{r['id']}`: {r['value']} × {r['scale']} {r['unit']}; definition {candidate['definition_status']}; numeric {candidate['reconciliation_status']}. " + candidate["comparison_basis"])
            if candidate["residual"]:
                residual = candidate["residual"]
                lines.append(f"  Residual: {residual['value']} {residual['unit']}; {residual['formula']}.")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output_dir = checked_path(args.output)
    if output_dir.exists():
        parser.error("Output must be a new directory")
    private = ROOT / "data"
    if not output_dir.is_relative_to(private) or output_dir.is_relative_to(private / "bf-borsdata-research"):
        parser.error("Exact material decisions belong in ignored private data storage")
    review = json.loads(args.review.read_text())
    rows = build_material_inputs(review, args.packet.resolve())
    review["material_inputs"] = rows
    review["material_inputs_sha256"] = canonical_hash(rows)
    review["material_inputs_reviewed_at"] = datetime.now(timezone.utc).isoformat()
    output_dir.mkdir(parents=True)
    (output_dir / "review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    (output_dir / "material-inputs.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    (output_dir / "material-inputs.md").write_text(render_notes(review, rows))
    print("Saved scoped material decisions and unchanged valuation results")


if __name__ == "__main__":
    main()
