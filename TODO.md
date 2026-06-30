# Travel Reimbursement Approval Agent - TODO

## Step 1: Project scaffold
- [x] Create README
- [x] Create Python package/module layout under `agent/`
- [x] Add `main.py` CLI and `evaluate.py` runner

## Step 2: Data & policy
- [x] Add `policy/travel_policy.md`
- [x] Add `policy/approval_matrix.json`
- [x] Add `policy/limits.json`
- [x] Add `data/sample_claims.json`
- [x] (Optional) Add `data/sample_receipts.json` if needed by the completeness tool

## Step 3: Agent tools (at least 2)
- [x] Receipt completeness check tool
- [x] Policy lookup + per-diem/limits checker tool
- [x] (Optional but recommended) Duplicate detector tool

## Step 4: Deterministic rule core + LLM-style reasoning stub
- [x] Deterministic validators in `agent/rules.py`
- [x] Agent orchestration decides when to route to Manual Review
- [x] Structured JSON output schema enforced

## Step 5: Run & verify
- [x] Run `python evaluate.py` and verify sample outputs
- [x] Ensure outputs include:
  - decision, approved_amount, deductions_rejected, missing_documents
  - policy_references, confidence, reason_codes, short explanation
- [ ] Add any follow-up fixes if output schema differs
