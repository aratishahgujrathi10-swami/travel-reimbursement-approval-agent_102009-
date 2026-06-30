from __future__ import annotations

import json

from agent.agent import AgentConfig, TravelReimbursementAgent
from agent.policy_store import PolicyStore
from agent.schema import Claim


def run_cases() -> None:
    policy_store = PolicyStore(policy_dir="policy")
    agent = TravelReimbursementAgent(
        policy_store=policy_store,
        previous_claims=[
            {
                "claim_id": "C099",
                "possible_duplicate_of": None,
                "receipts": [
                    {
                        "receipt_id": "P1",
                        "vendor": "Fast Cab",
                        "date": "2026-04-20",
                        "amount": 50.0,
                        "category": "Taxi",
                    }
                ],
            }
        ],
        config=AgentConfig(manual_review_confidence_threshold=0.55),
    )

    # Critical path samples from repository
    with open("data/sample_claims.json", "r", encoding="utf-8") as f:
        sample_claims = json.load(f)

    print("== Running sample claims (critical-path) ==")
    for cr in sample_claims:
        claim = Claim.model_validate(cr)
        out = agent.evaluate_claim(claim)
        assert out.decision in {"Approve", "PartiallyApprove", "Reject", "ManualReview"}
        # Basic schema sanity
        assert isinstance(out.approved_amount, float)
        assert isinstance(out.deductions_rejected, float)
        assert isinstance(out.missing_documents, list)
        assert isinstance(out.policy_references, list)
        assert isinstance(out.reason_codes, list)
        assert 0.0 <= out.confidence <= 1.0
        assert isinstance(out.short_explanation, str)
        assert isinstance(out.tool_trace, list)
        print(f"{claim.claim_id}: {out.decision} approved={out.approved_amount} missing={len(out.missing_documents)}")

    print("\n== Running edge cases ==")

    edge_claims = [
        # invalid date range (end < start) => ManualReview
        {
            "claim_id": "E001",
            "employee_name": "Test",
            "travel_start_date": "2026-05-03",
            "travel_end_date": "2026-05-01",
            "region": "US",
            "category": "Meals",
            "total_requested_amount": 60.0,
            "currency": "USD",
            "receipts": [{"receipt_id": "R10", "vendor": "Diner", "date": "2026-05-03", "amount": 60.0, "category": "Meals", "attached": True}],
        },
        # missing receipts list entirely (empty list default) => ManualReview
        {
            "claim_id": "E002",
            "employee_name": "Test",
            "travel_start_date": "2026-05-01",
            "travel_end_date": "2026-05-02",
            "region": "US",
            "category": "Hotel",
            "total_requested_amount": 300.0,
            "currency": "USD",
            "receipts": [],
        },
        # attached=false receipt => completeness should treat as missing doc for that category
        {
            "claim_id": "E003",
            "employee_name": "Test",
            "travel_start_date": "2026-05-01",
            "travel_end_date": "2026-05-02",
            "region": "US",
            "category": "Taxi",
            "total_requested_amount": 40.0,
            "currency": "USD",
            "receipts": [{"receipt_id": "R11", "vendor": "City Taxi", "date": "2026-05-01", "amount": 40.0, "category": "Taxi", "attached": False}],
        },
        # negative requested amount => should not break; deterministic cap logic will clamp to min
        {
            "claim_id": "E004",
            "employee_name": "Test",
            "travel_start_date": "2026-05-01",
            "travel_end_date": "2026-05-03",
            "region": "US",
            "category": "Meals",
            "total_requested_amount": -10.0,
            "currency": "USD",
            "receipts": [{"receipt_id": "R12", "vendor": "Diner", "date": "2026-05-01", "amount": -10.0, "category": "Meals", "attached": True}],
        },
        # unknown category for US => expected Reject via default policy (eligibility false)
        {
            "claim_id": "E005",
            "employee_name": "Test",
            "travel_start_date": "2026-05-01",
            "travel_end_date": "2026-05-03",
            "region": "US",
            "category": "Laundry",
            "total_requested_amount": 25.0,
            "currency": "USD",
            "receipts": [{"receipt_id": "R13", "vendor": "Cleaners", "date": "2026-05-01", "amount": 25.0, "category": "Laundry", "attached": True}],
        },
        # duplicate signature match (same signature as previous_claims C099)
        {
            "claim_id": "E006",
            "employee_name": "Test",
            "travel_start_date": "2026-04-20",
            "travel_end_date": "2026-04-20",
            "region": "US",
            "category": "Taxi",
            "total_requested_amount": 50.0,
            "currency": "USD",
            "receipts": [{"receipt_id": "R14", "vendor": "Fast Cab", "date": "2026-04-20", "amount": 50.0, "category": "Taxi", "attached": True}],
        },
    ]

    for cr in edge_claims:
        claim = Claim.model_validate(cr)
        out = agent.evaluate_claim(claim)
        assert out.decision in {"Approve", "PartiallyApprove", "Reject", "ManualReview"}
        assert 0.0 <= out.confidence <= 1.0
        print(f"{claim.claim_id}: {out.decision} reasons={out.reason_codes} missing={out.missing_documents} approved={out.approved_amount}")


if __name__ == "__main__":
    run_cases()
