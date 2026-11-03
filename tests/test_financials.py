from decimal import Decimal
import unittest

from betaforge.financials import FORMULAS, evaluate


class FinancialFormulaTests(unittest.TestCase):
    def value(self, result, key=None):
        value = result["outputs"][key or result["primary_output"]]["value"]
        return Decimal(value) if value is not None else None

    def case(self):
        return {"forecast_ebit": "2520000000", "exit_multiple": "11",
                "current_financial_net_debt": "4987000000", "annual_retained_cash": "350000000",
                "years": "3", "additional_leases": "247000000", "pensions": "229000000",
                "nci_value": "651000000", "non_operating_assets": "0", "forecast_shares": "106594428",
                "annual_dividend_per_share": "3.40", "required_return": "0.10", "price": "172.20"}

    def test_one_case_preserves_saved_base_valuation_and_dividend_accounting(self):
        result = evaluate("valuation_case", self.case())
        self.assertEqual(self.value(result, "future_financial_net_debt"), Decimal("3937000000"))
        self.assertEqual(self.value(result, "common_equity"), Decimal("22656000000"))
        self.assertEqual(self.value(result), Decimal("168.1427067831807167247976810184844809024"))
        self.assertEqual(self.value(result, "dividend_pv"), Decimal("8.455296769346356123215627347858752817431"))
        self.assertEqual(len(result["outputs"]), 9)

    def test_missing_claims_do_not_default_to_zero_and_negative_equity_is_not_a_quote(self):
        values = self.case()
        del values["nci_value"]
        result = evaluate("valuation_case", values)
        self.assertIsNone(self.value(result))
        self.assertIn("nci_value", result["missing_inputs"])
        self.assertIn("enterprise_value", result["outputs"])
        values = self.case()
        values["current_financial_net_debt"] = "50000000000"
        result = evaluate("valuation_case", values)
        self.assertLess(self.value(result, "common_equity"), 0)
        self.assertNotIn("future_target", result["outputs"])
        self.assertIsNone(self.value(result))

    def test_cash_conversion_subtracts_outside_cfo_interest_and_lease_once(self):
        inputs = {"cfo": "1000", "cash_capex": "200", "interest_paid_outside_cfo": "50",
                  "lease_principal_outside_cfo": "30", "group_net_income": "600", "noncash_sbc_addback": "15"}
        result = evaluate("group_cash_conversion", inputs)
        self.assertEqual(self.value(result, "cash_after_debt_like_service"), 720)
        self.assertEqual(self.value(result), 120)
        self.assertEqual(self.value(result, "noncash_sbc_addback"), 15)
        inputs["interest_paid_outside_cfo"] = "0"
        self.assertEqual(self.value(evaluate("group_cash_conversion", inputs), "cash_after_debt_like_service"), 770)
        with self.assertRaisesRegex(ValueError, "Unknown input"):
            evaluate("group_cash_conversion", dict(inputs, working_capital="10"))

    def test_missing_lease_and_gross_interest_leave_known_cash_outputs(self):
        result = evaluate("group_cash_conversion", {"cfo": "473", "cash_capex": "183",
                          "net_interest_cash_outside_cfo": "-51", "group_net_income": "388"})
        self.assertEqual(self.value(result, "cash_after_capex"), 290)
        self.assertEqual(self.value(result, "cash_after_capex_and_net_interest"), 239)
        self.assertIsNone(self.value(result))
        self.assertEqual(set(result["missing_inputs"]), {"interest_paid_outside_cfo", "lease_principal_outside_cfo"})
        with self.assertRaisesRegex(ValueError, "positive outflow"):
            evaluate("group_cash_conversion", {"cash_capex": "-100"})

    def test_loss_conversion_and_scope_mismatch_do_not_create_misleading_yield(self):
        result = evaluate("group_cash_conversion", {"cfo": "-10", "cash_capex": "5", "interest_paid_outside_cfo": "0",
                          "lease_principal_outside_cfo": "0", "group_net_income": "-2"})
        self.assertIsNone(self.value(result))
        mismatch = evaluate("fcf_yield", {"free_cash_flow": "20", "valuation_denominator": "100"},
                            {"cash_flow_scope": "group", "denominator_scope": "market_cap"})
        self.assertIsNone(self.value(mismatch))
        burn = evaluate("fcf_yield", {"free_cash_flow": "-20", "valuation_denominator": "100"},
                        {"cash_flow_scope": "parent_common", "denominator_scope": "market_cap"})
        self.assertEqual(self.value(burn), -20)

    def test_capital_does_not_add_goodwill_nci_or_leases_twice(self):
        inputs = {"group_equity": "100", "gross_debt_including_leases": "50", "net_pension_liability": "5",
                  "cash": "10", "non_operating_assets": "2"}
        self.assertEqual(self.value(evaluate("invested_capital", inputs)), 143)
        for field in ("goodwill", "nci_value", "lease_liabilities"):
            with self.assertRaisesRegex(ValueError, "Unknown input"):
                evaluate("invested_capital", dict(inputs, **{field: "5"}))

    def test_operating_roic_uses_explicit_fractional_tax_and_average_capital(self):
        inputs = {"ebit": "20", "operating_tax_rate": "0.2", "invested_capital_start": "100", "invested_capital_end": "150"}
        result = evaluate("operating_roic", inputs)
        self.assertEqual(self.value(result), Decimal("12.8"))
        self.assertEqual(self.value(result, "nopat"), 16)
        with self.assertRaisesRegex(ValueError, "fraction"):
            evaluate("operating_roic", dict(inputs, operating_tax_rate="20"))
        self.assertIsNone(self.value(evaluate("operating_roic", dict(inputs, invested_capital_start="-150"))))
        self.assertTrue(any("tax benefit" in w for w in evaluate("operating_roic", dict(inputs, ebit="-20"))["warnings"]))

    def test_incremental_margin_requires_comparable_basis_and_exposes_deltas(self):
        inputs = {"ebit_current": "12", "ebit_previous": "10", "revenue_current": "110", "revenue_previous": "100"}
        result = evaluate("incremental_ebit_margin", inputs)
        self.assertIsNone(self.value(result))
        self.assertEqual(self.value(result, "ebit_change"), 2)
        self.assertEqual(self.value(evaluate("incremental_ebit_margin", inputs, {"comparable_periods": True})), 20)
        zero = evaluate("incremental_ebit_margin", dict(inputs, revenue_current="100"), {"comparable_periods": True})
        self.assertIsNone(self.value(zero))

    def test_balance_average_and_closing_are_explicit(self):
        inputs = {"balance_start": "10", "balance_end": "20", "revenue": "100"}
        self.assertEqual(self.value(evaluate("working_capital_to_sales", inputs)), 15)
        self.assertEqual(self.value(evaluate("working_capital_to_sales", inputs, {"balance_basis": "closing"})), 20)
        result = evaluate("working_capital_to_sales", {"balance_end": "20", "revenue": "100"})
        self.assertIsNone(self.value(result))
        self.assertIn("balance_start", result["missing_inputs"])

    def test_nonfinite_values_and_percentage_in_forecast_fraction_are_rejected(self):
        for bad in (True, "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                evaluate("ebit_margin", {"ebit": bad, "revenue": "100"})
        with self.assertRaisesRegex(ValueError, "fraction"):
            evaluate("revenue_ebit", {"revenue": "100", "ebit_margin": "10"})
        for name, values in (("pe", {"price": "10", "diluted_eps": "-2"}),
                             ("ev_ebit", {"enterprise_value": "100", "ebit": "0"})):
            self.assertIsNone(self.value(evaluate(name, values)))
        self.assertEqual(FORMULAS["volume_ebit"]["required_fields"]["sales_volume"], "tonnes")

    def test_probabilities_weight_cash_flows_without_averaging_returns(self):
        values = {"bear_weight": "0.2", "base_weight": "0.5", "bull_weight": "0.3", "years": "3"}
        for case, target, present, dividend in (("bear", 50, 40, 1), ("base", 120, 100, 3), ("bull", 200, 160, 5)):
            values.update({case + "_future_target": target, case + "_present_value": present,
                           case + "_annual_dividend_per_share": dividend})
        result = evaluate("scenario_weighted_values", values)
        self.assertEqual(self.value(result), 106)
        self.assertEqual(self.value(result, "expected_future_target"), 130)
        self.assertEqual(self.value(result, "expected_annual_dividend_per_share"), Decimal("3.2"))
        for weights in ({"bear_weight": "0.1"}, {"bear_weight": "-0.1", "bull_weight": "0.6"}):
            with self.assertRaises(ValueError):
                evaluate("scenario_weighted_values", dict(values, **weights))

    def test_expected_cashflow_irr_payment_timing_losses_and_bounded_solver(self):
        values = {"price": 100, "expected_annual_dividend_per_share": 10, "expected_future_target": 100, "years": 3}
        result = evaluate("expected_cashflow_irr", values)
        self.assertAlmostEqual(self.value(result), Decimal(10), places=30)
        self.assertEqual(self.value(result, "initial_cash_flow"), -100)
        self.assertEqual(self.value(result, "terminal_cash_flow"), 110)
        loss = evaluate("expected_cashflow_irr", dict(values, expected_annual_dividend_per_share=0, expected_future_target=25, years=2))
        self.assertAlmostEqual(self.value(loss), Decimal(-50), places=30)
        no_receipts = evaluate("expected_cashflow_irr", dict(values, expected_annual_dividend_per_share=0, expected_future_target=0))
        self.assertIsNone(self.value(no_receipts))
        with self.assertRaises(ValueError):
            evaluate("expected_cashflow_irr", dict(values, expected_future_target=-10))
        with self.assertRaises(ValueError):
            evaluate("expected_cashflow_irr", dict(values, price=0))


if __name__ == "__main__":
    unittest.main()
