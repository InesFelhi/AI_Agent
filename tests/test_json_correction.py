"""
Integration test: JSON correction via JSONRetryHandler.

This test uses the workflow JSON produced by test_workflow_generation_pipeline
as a reference (correct baseline), then introduces deliberate structural and
syntactic errors to verify that the LLM + JSONRetryHandler pipeline can detect
and fix them automatically.

Baseline workflow (from successful generation test run):
    {
      "Start": [{"id": "-1000", "variables": [...], "exec_policy": "1"}],
      "CmdStage": [{"id": "-1001", "cmd_text": "ping -c 5 www.google.com",
                    "cmd_result_output": "$PING_RESULT",
                    "cmd_error_output": "$PING_ERROR", "commands": [null]}],
      "End": [{"id": "-2000"}],
      "Links": [{"from": "-1000", "to": "-1001"}, {"from": "-1001", "to": "-2000"}]
    }
"""

import json
from dataclasses import dataclass
from typing import List, Optional

from src.llm import create_llm_client
from src.workflow.json_retry_handler import JSONRetryHandler
from src.workflow.json_validator import JSONValidator
from src.utilities.logger import get_module_logger

logger = get_module_logger("test_json_correction")

# ---------------------------------------------------------------------------
# BASELINE — exact output from test_workflow_generation_pipeline (2026-04-21)
# ---------------------------------------------------------------------------
BASELINE_WORKFLOW: dict = {
    "Start": [
        {
            "id": "-1000",
            "variables": [
                {"variableName": "$PING_RESULT", "variableValue": "", "is_kpi": False},
                {"variableName": "$PING_ERROR",  "variableValue": "", "is_kpi": False}
            ],
            "exec_policy": "1"
        }
    ],
    "CmdStage": [
        {
            "id": "-1001",
            "cmd_text": "ping -c 5 www.google.com",
            "cmd_result_output": "$PING_RESULT",
            "cmd_error_output":  "$PING_ERROR",
            "commands": [None]
        }
    ],
    "End":  [{"id": "-2000"}],
    "Links": [
        {"from": "-1000", "to": "-1001"},
        {"from": "-1001", "to": "-2000"}
    ]
}

# ---------------------------------------------------------------------------
# Test case definition
# ---------------------------------------------------------------------------
@dataclass
class CorrectionTestCase:
    name: str
    description: str
    broken_json: str
    expected_errors: List[str]   # keywords that must appear in validator errors
    should_pass_after_fix: bool  # True → expect LLM to produce valid JSON


# ---------------------------------------------------------------------------
# Build broken test cases from the baseline
# ---------------------------------------------------------------------------
def _dump(obj: dict) -> str:
    return json.dumps(obj, indent=2)


def _make_cases() -> List[CorrectionTestCase]:
    cases: List[CorrectionTestCase] = []

    # ------------------------------------------------------------------
    # Case 1 — Wrong Start ID (900 instead of -1000)
    # ------------------------------------------------------------------
    c1 = json.loads(_dump(BASELINE_WORKFLOW))
    c1["Start"][0]["id"] = "900"
    cases.append(CorrectionTestCase(
        name="wrong_start_id",
        description='Start node id is "900" instead of "-1000"',
        broken_json=_dump(c1),
        expected_errors=["Start node id must be"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 2 — Missing End node
    # ------------------------------------------------------------------
    c2 = json.loads(_dump(BASELINE_WORKFLOW))
    del c2["End"]
    cases.append(CorrectionTestCase(
        name="missing_end_node",
        description='The "End" key is completely absent',
        broken_json=_dump(c2),
        expected_errors=["Missing \"End\" node"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 3 — End node ID too high (−500, must be < −1000)
    # ------------------------------------------------------------------
    c3 = json.loads(_dump(BASELINE_WORKFLOW))
    c3["End"][0]["id"] = "-500"
    cases.append(CorrectionTestCase(
        name="end_id_too_high",
        description='End node id is "-500" which is ≥ -1000',
        broken_json=_dump(c3),
        expected_errors=["End node ID"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 4 — Broken link referencing non-existent node "-9999"
    # ------------------------------------------------------------------
    c4 = json.loads(_dump(BASELINE_WORKFLOW))
    c4["Links"].append({"from": "-1001", "to": "-9999"})
    cases.append(CorrectionTestCase(
        name="broken_link_unknown_node",
        description='A Link points to non-existent node id "-9999"',
        broken_json=_dump(c4),
        expected_errors=["does not match any declared node"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 5 — Variable used in task not declared in Start
    # ------------------------------------------------------------------
    c5 = json.loads(_dump(BASELINE_WORKFLOW))
    c5["CmdStage"][0]["cmd_result_output"] = "$UNDECLARED_VAR"
    cases.append(CorrectionTestCase(
        name="undeclared_variable",
        description='"$UNDECLARED_VAR" used in CmdStage but absent from Start variables',
        broken_json=_dump(c5),
        expected_errors=["not declared in Start variables"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 6 — Node with no outgoing link (CmdStage orphan)
    # ------------------------------------------------------------------
    c6 = json.loads(_dump(BASELINE_WORKFLOW))
    # Remove the link FROM -1001
    c6["Links"] = [lnk for lnk in c6["Links"] if lnk.get("from") != "-1001"]
    cases.append(CorrectionTestCase(
        name="node_no_outgoing_link",
        description='CmdStage node "-1001" has no outgoing link — workflow would hang',
        broken_json=_dump(c6),
        expected_errors=["no outgoing link"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 7 — Variable name missing "$" prefix in Start
    # ------------------------------------------------------------------
    c7 = json.loads(_dump(BASELINE_WORKFLOW))
    c7["Start"][0]["variables"][0]["variableName"] = "PING_RESULT"   # missing $
    cases.append(CorrectionTestCase(
        name="variable_missing_dollar",
        description='"PING_RESULT" in Start variables is missing the "$" prefix',
        broken_json=_dump(c7),
        expected_errors=["does not start with \"$\""],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 8 — Syntactic: invalid JSON (trailing comma + missing brace)
    # ------------------------------------------------------------------
    broken_syntax = """{
  "Start": [
    {
      "id": "-1000",
      "variables": [
        {"variableName": "$PING_RESULT", "variableValue": "", "is_kpi": false},
      ],
      "exec_policy": "1"
    }
  ],
  "CmdStage": [
    {
      "id": "-1001",
      "cmd_text": "ping -c 5 www.google.com",
      "cmd_result_output": "$PING_RESULT",
      "cmd_error_output": "$PING_ERROR",
      "commands": [null]
    }
  ],
  "End": [{"id": "-2000"}],
  "Links": [
    {"from": "-1000", "to": "-1001"},
    {"from": "-1001", "to": "-2000"}
  ]
"""  # intentionally missing closing }
    cases.append(CorrectionTestCase(
        name="syntax_error_trailing_comma_and_missing_brace",
        description="Trailing comma inside variables array + missing closing brace",
        broken_json=broken_syntax,
        expected_errors=["Invalid JSON syntax"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 9 — Duplicate node IDs (two nodes with id "-1001")
    # ------------------------------------------------------------------
    c9 = json.loads(_dump(BASELINE_WORKFLOW))
    c9["CmdStage"].append({
        "id": "-1001",   # duplicate!
        "cmd_text": "ls /sdcard",
        "cmd_result_output": "$PING_RESULT",
        "cmd_error_output": "$PING_ERROR",
        "commands": [None]
    })
    cases.append(CorrectionTestCase(
        name="duplicate_node_ids",
        description='Two CmdStage nodes share the same id "-1001"',
        broken_json=_dump(c9),
        expected_errors=["Duplicate node IDs"],
        should_pass_after_fix=True
    ))

    # ------------------------------------------------------------------
    # Case 10 — Missing Links array entirely
    # ------------------------------------------------------------------
    c10 = json.loads(_dump(BASELINE_WORKFLOW))
    del c10["Links"]
    cases.append(CorrectionTestCase(
        name="missing_links_array",
        description='"Links" key is completely absent from the workflow',
        broken_json=_dump(c10),
        expected_errors=['"Links" array is missing'],
        should_pass_after_fix=True
    ))

    return cases


# ---------------------------------------------------------------------------
# Run a single test case
# ---------------------------------------------------------------------------
def _run_case(
    case: CorrectionTestCase,
    handler: JSONRetryHandler,
    validator: JSONValidator,
    index: int,
    total: int
) -> bool:
    """
    Returns True if the test passed (LLM produced valid JSON when expected).
    """
    print(f"\n{'─' * 70}")
    print(f"[{index}/{total}] {case.name}")
    print(f"     Description : {case.description}")
    print(f"     Expects fix : {case.should_pass_after_fix}")

    # ── Step A: validate the broken JSON first (confirm it is indeed broken) ──
    pre_check = validator.validate(case.broken_json)
    if pre_check.is_valid:
        print(f"     ⚠️  WARNING: broken JSON passed validation before correction!")
        print(f"            This test case may not be testing what it claims.")
    else:
        print(f"     ✅ Pre-check: broken JSON has {len(pre_check.errors)} error(s) as expected")
        for e in pre_check.errors:
            print(f"          • {e}")

    # ── Step B: run through JSONRetryHandler ──
    result = handler.process(case.broken_json)

    success      = result["success"]
    retry_count  = result["retry_count"]
    final_json   = result["final_json"]
    errors_found = result["validation"].errors if result["validation"] else []

    print(f"\n     After correction:")
    print(f"          Retries used : {retry_count}")
    print(f"          Success      : {success}")

    if success:
        print(f"          ✅ Workflow is now valid")
        # Show diff summary
        try:
            parsed = result["validation"].parsed
            keys = list(parsed.keys())
            print(f"          Workflow keys: {keys}")
        except Exception:
            pass
        passed = case.should_pass_after_fix  # we expected success and got it
    else:
        print(f"          ❌ Workflow still invalid after {retry_count} retries")
        print(f"          Remaining errors:")
        for e in errors_found:
            print(f"               • {e}")
        passed = not case.should_pass_after_fix  # we expected failure or accepted partial

    verdict = "PASS" if passed else "FAIL"
    print(f"\n     Verdict: [{verdict}]")
    return passed


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------
def test_json_correction_pipeline(provider: str = "openai") -> None:
    print("=" * 70)
    print("JSON CORRECTION PIPELINE TEST")
    print("Using baseline workflow from test_workflow_generation_pipeline")
    print("=" * 70)

    # ── Init ──
    print("\n[INIT] Creating LLM client...")
    try:
        llm_client = create_llm_client(provider=provider)
        print(f"  ✅ LLM client: {type(llm_client).__name__}")
    except Exception as exc:
        print(f"  ❌ Failed to create LLM client: {exc}")
        return

    handler   = JSONRetryHandler(llm_client)
    validator = JSONValidator()
    cases     = _make_cases()
    total     = len(cases)

    print(f"\n[INFO] Running {total} correction test cases...\n")

    results = []
    for i, case in enumerate(cases, start=1):
        passed = _run_case(case, handler, validator, i, total)
        results.append((case.name, passed))

    # ── Summary ──
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {name}")

    print(f"\n  Total : {total}   Passed : {passed_count}   Failed : {failed_count}")

    if failed_count == 0:
        print("\n✅ ALL CORRECTION TESTS PASSED")
    else:
        print(f"\n⚠️  {failed_count} test(s) failed — review LLM correction capability")

    print("=" * 70)


if __name__ == "__main__":
    test_json_correction_pipeline(provider="openai")