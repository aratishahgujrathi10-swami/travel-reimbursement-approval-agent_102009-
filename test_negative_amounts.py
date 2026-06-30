from __future__ import annotations

import unittest

from agent.agent import AgentConfig, TravelReimbursementAgent
from agent.policy_store import PolicyStore
from agent.schema import Claim


class TestNegativeAmounts(unittest.TestCase):
    def test_requested_amount_cannot_be_negative(self) -> None:
        policy_store = PolicyStore(policy_dir="policy")
        agent = TravelReimbursementAgent(policy_store=policy_store, previous_claims=[], config=AgentConfig())

        claim = Claim.model_validate(
            {
                "claim_id": "NEG001",
                "employee_name": "Test",
                "travel_start_date": "2026-05-01",
                "travel_end_date": "2026-05-03",
                "region": "US",
                "category": "Meals",
                "total_requested_amount": -10.0,
                "currency": "USD",
                "receipts": [
                    {
                        "receipt_id": "R_NEG_1",
                        "vendor": "Diner",
                        "date": "2026-05-01",
                        "amount": -10.0,
                        "category": "Meals",
                        "attached": True,
                    }
                ],
            }
        )

        out = agent.evaluate_claim(claim)

        self.assertIn(out.decision, {"Approve", "PartiallyApprove", "Reject", "ManualReview"})
        self.assertGreaterEqual(out.approved_amount, 0.0)
        self.assertGreaterEqual(out.deductions_rejected, 0.0)


if __name__ == "__main__":
    unittest.main()
