"""
Test Workflow Planner — verify Phase 1 agent works correctly.

Tests:
1. Can load task registry
2. Can decompose simple request
3. Can decompose complex request
4. Returns valid plan JSON
5. Confidence scoring works
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from src.workflow.workflow_planner import WorkflowPlanner


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = MagicMock()
    
    # Mock scroll response with task docs
    mock_points = [
        MagicMock(
            payload={
                "document_title": "CmdStage",
                "content": "Execute shell commands",
                "section_title": "System Tasks",
                "type_doc": "task_doc"
            }
        ),
        MagicMock(
            payload={
                "document_title": "AppStage",
                "content": "Install/launch apps",
                "section_title": "Android UI Tasks",
                "type_doc": "task_doc"
            }
        ),
        MagicMock(
            payload={
                "document_title": "CompareStrings",
                "content": "Compare two strings",
                "section_title": "Control Flow",
                "type_doc": "task_doc"
            }
        ),
    ]
    
    client.scroll.return_value = (mock_points, None)
    return client


def test_planner_loads_tasks(mock_llm_client, mock_qdrant_client):
    """Test that planner can load tasks from registry."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    tasks = planner.task_registry.get_task_names()
    
    assert len(tasks) >= 3
    assert "CmdStage" in tasks
    assert "AppStage" in tasks
    assert "CompareStrings" in tasks


def test_planner_simple_request(mock_llm_client, mock_qdrant_client):
    """Test planning a simple request."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    # Mock LLM response
    llm_response = """{
        "user_intention": "Check if google.com is reachable",
        "steps": [
            {
                "step_number": 1,
                "action": "Execute ping command",
                "task_types_needed": ["CmdStage"],
                "output_variables": ["$PING_OUTPUT"],
                "rationale": "CmdStage runs ping"
            }
        ],
        "required_tasks": ["CmdStage"],
        "declared_variables": ["$PING_OUTPUT"],
        "has_loops": false,
        "has_conditions": false,
        "complexity": "simple",
        "confidence": 95,
        "ambiguities": [],
        "notes": "Simple network test"
    }"""
    
    mock_llm_client.complete.return_value = llm_response
    
    # Run planner
    result = planner.plan("Test if google.com is reachable")
    
    # Verify result
    assert result["success"] is True
    assert result["plan"] is not None
    assert result["confidence"] == 95
    assert result["error"] is None
    
    # Verify plan structure
    plan = result["plan"]
    assert plan["user_intention"] == "Check if google.com is reachable"
    assert len(plan["steps"]) == 1
    assert plan["required_tasks"] == ["CmdStage"]


def test_planner_complex_request(mock_llm_client, mock_qdrant_client):
    """Test planning a complex conditional request."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    # Mock LLM response for conditional logic
    llm_response = """{
        "user_intention": "Check if app is installed, install if not",
        "steps": [
            {
                "step_number": 1,
                "action": "Check app installation",
                "task_types_needed": ["AppStage"],
                "output_variables": ["$APP_INSTALLED"],
                "rationale": "AppStage checks installation status"
            },
            {
                "step_number": 2,
                "action": "Compare status",
                "task_types_needed": ["CompareStrings"],
                "output_variables": [],
                "rationale": "Branch on true/false"
            }
        ],
        "required_tasks": ["AppStage", "CompareStrings"],
        "declared_variables": ["$APP_INSTALLED"],
        "has_loops": false,
        "has_conditions": true,
        "complexity": "medium",
        "confidence": 88,
        "ambiguities": ["Should we check for updates?"],
        "notes": "Conditional workflow with branching"
    }"""
    
    mock_llm_client.complete.return_value = llm_response
    
    # Run planner
    result = planner.plan("Check if app is installed, install if not")
    
    # Verify result
    assert result["success"] is True
    assert result["confidence"] == 88
    assert len(result["plan"]["steps"]) == 2
    assert result["plan"]["has_conditions"] is True
    assert len(result["ambiguities"]) > 0


def test_planner_handles_invalid_json(mock_llm_client, mock_qdrant_client):
    """Test that planner gracefully handles invalid JSON."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    # Mock invalid JSON response
    mock_llm_client.complete.return_value = "This is not JSON at all"
    
    # Run planner
    result = planner.plan("Some request")
    
    # Should not crash, return empty plan
    assert result["success"] is True  # Graceful handling
    assert result["plan"]["is_valid"] is False


def test_planner_handles_empty_request(mock_llm_client, mock_qdrant_client):
    """Test that planner handles empty requests."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    # Run planner with empty request
    result = planner.plan("")
    
    # Should return error
    assert result["success"] is False
    assert result["error"] is not None


def test_planner_confidence_scoring(mock_llm_client, mock_qdrant_client):
    """Test confidence score is properly extracted."""
    planner = WorkflowPlanner(mock_llm_client, mock_qdrant_client)
    
    test_cases = [
        (92, "High confidence simple task"),
        (70, "Medium confidence with some ambiguity"),
        (45, "Low confidence, needs clarification"),
    ]
    
    for confidence, description in test_cases:
        llm_response = f"""{{
            "user_intention": "{description}",
            "steps": [{{"step_number": 1, "action": "test", "task_types_needed": ["CmdStage"], "output_variables": []}}],
            "required_tasks": ["CmdStage"],
            "confidence": {confidence},
            "ambiguities": []
        }}"""
        
        mock_llm_client.complete.return_value = llm_response
        result = planner.plan("Test request")
        
        assert result["confidence"] == confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
