from __future__ import annotations

import json

from agent.agent import AgentConfig, TravelReimbursementAgent
from agent.policy_store import PolicyStore
from agent.schema import Claim


def load_claims() -> list[dict]:
    with open("data/sample_claims.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("data/sample_claims.json must be a list of claim objects")
    return payload


def main() -> None:
    claims_raw = load_claims()
    policy_store = PolicyStore(policy_dir="policy")

    # Optional previous claims for duplicate detection
    try:
        with open("data/previous_claims.json", "r", encoding="utf-8") as f:
            previous_claims = json.load(f)
    except FileNotFoundError:
        previous_claims = []

    agent = TravelReimbursementAgent(
        policy_store=policy_store,
        previous_claims=previous_claims,
        config=AgentConfig(),
    )

    outputs = []
    for i, cr in enumerate(claims_raw):
        claim = Claim.model_validate(cr)
        result = agent.evaluate_claim(claim)
        outputs.append(result.model_dump())

        print(f"\n=== Claim #{i} ({claim.claim_id}) ===")
        print(result.model_dump_json(indent=2))

    # Also write a combined artifact
    with open("data/sample_outputs.json", "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)


if __name__ == "__main__":
    main()
