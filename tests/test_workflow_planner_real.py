"""
Real Integration Test for Workflow Planner (Phase 1 Agent)

Tests the planner with REAL:
- Real Qdrant connection
- Real LLM connection
- Real task registry
- Realistic user requests

Displays human-readable output (not pytest format)
"""

import json
import sys
from pprint import pprint

from src.workflow.workflow_planner import WorkflowPlanner
from src.llm import create_llm_client
from qdrant_client import QdrantClient
from src.config import config
from src.utilities.logger import get_module_logger

logger = get_module_logger("real_test_planner")


def print_section(title):
    """Print a nice section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(result):
    """Pretty print the planner result"""
    if not result["success"]:
        print(f"❌ ERROR: {result['error']}")
        return
    
    print("✅ SUCCESS\n")
    
    plan = result["plan"]
    confidence = result["confidence"]
    ambiguities = result["ambiguities"]
    
    # Confidence level
    if confidence >= 80:
        confidence_level = "🟢 HIGH"
    elif confidence >= 60:
        confidence_level = "🟡 MEDIUM"
    else:
        confidence_level = "🔴 LOW"
    
    print(f"Confidence: {confidence_level} ({confidence}%)")
    print(f"\nUser Intention:")
    print(f"  {plan.get('user_intention', 'N/A')}")
    
    print(f"\nComplexity: {plan.get('complexity', 'N/A')}")
    print(f"Has Conditions: {plan.get('has_conditions', False)}")
    print(f"Has Loops: {plan.get('has_loops', False)}")
    
    print(f"\nRequired Tasks ({len(plan.get('required_tasks', []))} total):")
    for task in plan.get('required_tasks', []):
        print(f"  • {task}")
    
    print(f"\nExecution Steps ({len(plan.get('steps', []))} total):")
    for i, step in enumerate(plan.get('steps', []), 1):
        print(f"\n  Step {i}: {step.get('action', 'N/A')}")
        tasks = step.get('task_types_needed', [])
        print(f"    Tasks: {', '.join(tasks)}")
        outputs = step.get('output_variables', [])
        if outputs:
            print(f"    Outputs: {', '.join(outputs)}")
        rationale = step.get('rationale', '')
        if rationale:
            print(f"    Rationale: {rationale}")
    
    print(f"\nDeclared Variables:")
    variables = plan.get('declared_variables', [])
    if variables:
        for var in variables:
            print(f"  • {var}")
    else:
        print("  (none)")
    
    if ambiguities and ambiguities[0] != "":
        print(f"\n⚠️  Ambiguities Detected:")
        for amb in ambiguities:
            print(f"  • {amb}")
    
    print("\n" + "-" * 80)
    print("Full Plan JSON:")
    print("-" * 80)
    print(json.dumps(plan, indent=2))


def test_real_scenario_1():
    """
    TEST 1: Execute shell command (CmdStage)
    
    User: "Run a ping command to test network connectivity to 8.8.8.8"
    Expected: Simple workflow with 1 step (CmdStage task)
    Tasks used: CmdStage
    """
    print_section("TEST 1: Execute Shell Command (Ping)")
    
    try:
        # Create real connections
        llm_client = create_llm_client(provider=config.LLM_PROVIDER)
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        
        # Create planner
        planner = WorkflowPlanner(llm_client, qdrant_client, config.QDRANT_COLLECTION_NAME)
        
        # REAL question based on CmdStage task
        user_request = "Execute a shell command to ping 8.8.8.8 (Google DNS) and save the output to a variable"
        
        print(f"\n📝 User Request:")
        print(f"  \"{user_request}\"")
        
        print(f"\n⏳ Planning...")
        result = planner.plan(user_request)
        
        print_result(result)
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        logger.exception("Test 1 failed")
        return False


def test_real_scenario_2():
    """
    TEST 2: HTTP Request (GET request to API)
    
    User: "Send an HTTP GET request to an API endpoint and store the response"
    Expected: Simple workflow with 1 step (HttpRequest task)
    Tasks used: HttpRequest
    """
    print_section("TEST 2: HTTP GET Request to API")
    
    try:
        # Create real connections
        llm_client = create_llm_client(provider=config.LLM_PROVIDER)
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        
        # Create planner
        planner = WorkflowPlanner(llm_client, qdrant_client, config.QDRANT_COLLECTION_NAME)
        
        # REAL question based on HttpRequest task
        user_request = "Send an HTTP GET request to https://api.github.com/status and capture the HTTP response code and body"
        
        print(f"\n📝 User Request:")
        print(f"  \"{user_request}\"")
        
        print(f"\n⏳ Planning...")
        result = planner.plan(user_request)
        
        print_result(result)
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        logger.exception("Test 2 failed")
        return False


def test_real_scenario_3():
    """
    TEST 3: Conditional workflow with comparison
    
    User: "Compare two numbers and branch based on result"
    Expected: Workflow with 2-3 steps (Execute → CompareNumber → Branches)
    Tasks used: CmdStage, CompareNumber
    """
    print_section("TEST 3: Conditional Comparison (CompareNumber)")
    
    try:
        # Create real connections
        llm_client = create_llm_client(provider=config.LLM_PROVIDER)
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        
        # Create planner
        planner = WorkflowPlanner(llm_client, qdrant_client, config.QDRANT_COLLECTION_NAME)
        
        # REAL question based on CompareNumber task
        user_request = "Execute a command to get battery level, then compare it with 20. If battery is below 20%, log a warning, otherwise log success"
        
        print(f"\n📝 User Request:")
        print(f"  \"{user_request}\"")
        
        print(f"\n⏳ Planning...")
        result = planner.plan(user_request)
        
        print_result(result)
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        logger.exception("Test 3 failed")
        return False


def test_real_scenario_4():
    """
    TEST 4: Download file with error handling
    
    User: "Download a file and handle errors if download fails"
    Expected: Workflow with DownloadFile + Exception handling
    Tasks used: DownloadFile, AndromateException, TextReport
    """
    print_section("TEST 4: Download File with Error Handling")
    
    try:
        # Create real connections
        llm_client = create_llm_client(provider=config.LLM_PROVIDER)
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        
        # Create planner
        planner = WorkflowPlanner(llm_client, qdrant_client, config.QDRANT_COLLECTION_NAME)
        
        # REAL question based on DownloadFile and exception handling
        user_request = "Download a file from https://example.com/data.zip. If the download fails, catch the error and generate a text report with error details"
        
        print(f"\n📝 User Request:")
        print(f"  \"{user_request}\"")
        
        print(f"\n⏳ Planning...")
        result = planner.plan(user_request)
        
        print_result(result)
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        logger.exception("Test 4 failed")
        return False


def test_real_scenario_5():
    """
    TEST 5: Send SMS with confirmation
    
    User: "Send an SMS message and wait for a response"
    Expected: Workflow with SendSms + WaitSms
    Tasks used: SendSms, WaitSms, TextReport
    """
    print_section("TEST 5: Send SMS and Wait for Response")
    
    try:
        # Create real connections
        llm_client = create_llm_client(provider=config.LLM_PROVIDER)
        qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        
        # Create planner
        planner = WorkflowPlanner(llm_client, qdrant_client, config.QDRANT_COLLECTION_NAME)
        
        # REAL question based on SendSms and WaitSms tasks
        user_request = "Send an SMS message to a contact saying 'Workflow started', then wait for a response with a 30-second timeout. Log the response to a text report"
        
        print(f"\n📝 User Request:")
        print(f"  \"{user_request}\"")
        
        print(f"\n⏳ Planning...")
        result = planner.plan(user_request)
        
        print_result(result)
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        logger.exception("Test 5 failed")
        return False


def main():
    """Run all real integration tests"""
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  WORKFLOW PLANNER - REAL INTEGRATION TESTS (Phase 1 Agent)".center(78) + "║")
    print("║" + "  Testing with REAL Qdrant + LLM connections".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = []
    
    try:
        # Run all tests
        results.append(("Execute Shell Command (Ping)", test_real_scenario_1()))
        results.append(("HTTP GET Request to API", test_real_scenario_2()))
        results.append(("Conditional Comparison (CompareNumber)", test_real_scenario_3()))
        results.append(("Download File with Error Handling", test_real_scenario_4()))
        results.append(("Send SMS and Wait for Response", test_real_scenario_5()))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        logger.exception("Unexpected error in tests")
        sys.exit(1)
    
    # Summary
    print_section("TEST SUMMARY")
    print()
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
