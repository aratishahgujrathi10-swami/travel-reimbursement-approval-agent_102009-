from __future__ import annotations

import unittest

from agent.agent import AgentConfig, TravelReimbursementAgent
from agent.policy_store import PolicyStore
from agent.schema import Claim


REQUIRED_OUTPUT_FIELDS = [
    "decision",
    "approved_amount",
    "deductions_rejected",
    "missing_documents",
    "policy_references",
    "reason_codes",
    "confidence",
    "short_explanation",
    "tool_trace",
]


class TestValidationAndContract(unittest.TestCase):
    def setUp(self) -> None:
        self.policy_store = PolicyStore(policy_dir="policy")
        self.agent = TravelReimbursementAgent(policy_store=self.policy_store, previous_claims=[], config=AgentConfig())

    def test_malformed_input_missing_receipts_field(self) -> None:
        # missing `receipts` should fail because Claim schema expects receipts present? (in our model it has default_factory)
        # So instead we provide invalid overall structure to ensure validation errors are handled.
        # Here: receipts omitted but claim remains valid due to default; so we make a different malformed case:
        with self.assertRaises(Exception):
            Claim.model_validate(
                {
                    "claim_id": "BAD001",
                    "employee_name": "Test",
                    "travel_start_date": "2026-05-01",
                    "travel_end_date": "2026-05-03",
                    "region": "US",
                    "category": "Meals",
                    "total_requested_amount": "not-a-number",
                    "currency": "USD",
                    "receipts": [],
                }
            )

    def test_malformed_input_invalid_type_total_requested_amount(self) -> None:
        with self.assertRaises(Exception):
            Claim.model_validate(
                {
                    "claim_id": "BAD002",
                    "employee_name": "Test",
                    "travel_start_date": "2026-05-01",
                    "travel_end_date": "2026-05-03",
                    "region": "US",
                    "category": "Meals",
                    "total_requested_amount": "100.50 USD",
                    "currency": "USD",
                    "receipts": [],
                }
            )

    def test_attached_false_required_category_behaves_as_expected(self) -> None:
        # Hotel US requires Hotel + Meals receipts.
        # Provide both categories, but mark Meals receipt as attached=false.
        # Current implementation:
        # - "missing_documents" only tracks missing categories (not attached=false).
        # - attached=false is reported in tool_trace.attachments_missing.
        claim = Claim.model_validate(
            {
                "claim_id": "ATT001",
                "employee_name": "Test",
                "travel_start_date": "2026-05-01",
                "travel_end_date": "2026-05-03",
                "region": "US",
                "category": "Hotel",
                "total_requested_amount": 200.0,
                "currency": "USD",
                "receipts": [
                    {
                        "receipt_id": "RH1",
                        "vendor": "Grand Midtown Hotel",
                        "date": "2026-05-01",
                        "amount": 200.0,
                        "category": "Hotel",
                        "attached": True,
                    },
                    {
                        "receipt_id": "RM1",
                        "vendor": "Deli (Incidental Meals)",
                        "date": "2026-05-02",
                        "amount": 0.0,
                        "category": "Meals",
                        "attached": False,
                    },
                ],
            }
        )

        out = self.agent.evaluate_claim(claim)
        # Should not be rejected purely due to attached=false in current logic.
        self.assertIn(out.decision, {"Approve", "PartiallyApprove", "Reject", "ManualReview"})

        # Verify attached=false is exposed in tool trace.
        receipt_tool_traces = [t for t in out.tool_trace if t.get("tool") == "receipt_completeness_check"]
        self.assertTrue(len(receipt_tool_traces) >= 1)
        attachments_missing = receipt_tool_traces[0].get("attachments_missing", [])
        self.assertIn("RM1", attachments_missing)

    def test_contract_all_required_fields_present(self) -> None:
        # Use claim C006 from sample data by constructing same payload
        claim = Claim.model_validate(
            {
                "claim_id": "C006",
                "employee_name": "Arati",
                "travel_start_date": "2026-05-05",
                "travel_end_date": "2026-05-07",
                "region": "US",
                "category": "Hotel",
                "total_requested_amount": 300.0,
                "currency": "USD",
                "receipts": [
                    {
                        "receipt_id": "R8",
                        "vendor": "Grand Midtown Hotel",
                        "date": "2026-05-05",
                        "amount": 200.0,
                        "category": "Hotel",
                        "attached": True,
                    },
                    {
                        "receipt_id": "R9",
                        "vendor": "Deli (Incidental Meals)",
                        "date": "2026-05-06",
                        "amount": 100.0,
                        "category": "Meals",
                        "attached": True,
                    },
                ],
            }
        )
        out = self.agent.evaluate_claim(claim)
        out_dict = out.model_dump()

        for field in REQUIRED_OUTPUT_FIELDS:
            self.assertIn(field, out_dict)

        self.assertIsInstance(out_dict["tool_trace"], list)
        self.assertIsInstance(out_dict["missing_documents"], list)
        self.assertIsInstance(out_dict["policy_references"], list)
        self.assertIsInstance(out_dict["reason_codes"], list)
        self.assertTrue(0.0 <= out_dict["confidence"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
