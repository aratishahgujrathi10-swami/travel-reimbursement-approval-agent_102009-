from __future__ import annotations

import argparse
import json
from typing import Any

from agent.agent import AgentConfig, TravelReimbursementAgent
from agent.policy_store import PolicyStore
from agent.schema import Claim


def _load_previous_claims_if_exists() -> list[dict[str, Any]]:
    # Optional mock dataset for duplicate detection
    try:
        with open("data/previous_claims.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Travel Reimbursement Approval Agent (prototype)")
    parser.add_argument("--claim", required=True, help="Path to claim JSON file")
    parser.add_argument("--index", type=int, default=0, help="Index if claim file contains a list")
    args = parser.parse_args()

    with open(args.claim, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        claim_obj = payload[args.index]
    else:
        claim_obj = payload

    claim = Claim.model_validate(claim_obj)

    policy_store = PolicyStore(policy_dir="policy")
    agent = TravelReimbursementAgent(policy_store=policy_store, previous_claims=_load_previous_claims_if_exists(), config=AgentConfig())

    result = agent.evaluate_claim(claim)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
