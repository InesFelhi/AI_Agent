"""
Workflow Planner — AGENT 1 (Autonomous Decomposition)

Responsibilities:
- Receive raw user request
- Load available tasks from TaskRegistry
- Call LLM to decompose request into execution steps
- Parse and validate the plan
- Return structured plan JSON

Why this is an AGENT:
    ✓ Autonomous step: analyzes user intent BEFORE generation
    ✓ Autonomous choice: decides which 120 tasks to use
    ✓ Autonomous estimation: estimates confidence in plan
    ✓ Not rule-based: uses LLM reasoning, not hardcoded logic
"""

import json
import time
from typing import Dict, Any, Optional, List
from qdrant_client import QdrantClient

from src.llm import LLMClient
from src.workflow.task_registry import TaskRegistry
from src.prompts.planner_prompt import build_planner_prompt
from src.utilities.logger import get_module_logger

logger = get_module_logger("workflow_planner")


class WorkflowPlanner:
    """
    AGENT 1: Autonomous workflow planner.
    
    Analyzes user request and produces a detailed execution plan
    before any JSON generation happens.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        qdrant_client: QdrantClient,
        collection_name: str = "andromate_docs"
    ) -> None:
        """
        Args:
            llm_client: LLM client for reasoning
            qdrant_client: Qdrant client for task registry
            collection_name: Qdrant collection name
        """
        self.llm = llm_client
        self.task_registry = TaskRegistry(
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            cache_ttl_seconds=600  # 10 min cache
        )
        logger.info("WorkflowPlanner initialized")

    def plan(self, user_request: str, suggested_tasks: List[str] = None) -> Dict[str, Any]:
        """
        Autonomous planning step: decompose user request into execution plan.

        Args:
            user_request: raw user input (any language potentially)
            suggested_tasks: task names suggested by QueryRewriter (optional)

        Returns:
            {
                "success": bool,
                "plan": dict | None,  # structured plan
                "confidence": int (0-100),
                "ambiguities": [list of unclear points],
                "error": str | None
            }

        Never raises — returns error dict on failure.
        """
        if not user_request or not user_request.strip():
            logger.warning("[PLANNER] Empty request received")
            return self._error_response("Empty request")

        logger.info("[PLANNER] Planning request: %.80s", user_request)
        if suggested_tasks:
            logger.info("[PLANNER] Received suggested tasks from Rewriter: %s", suggested_tasks)
        start_time = time.time()

        try:
            # Step 1: Load all available tasks
            task_names = self.task_registry.get_task_names()
            if not task_names:
                logger.warning("[PLANNER] No tasks loaded from registry")
                task_names = self._get_fallback_tasks()

            # Step 1b: Load task descriptions DYNAMICALLY from Qdrant
            logger.info("[PLANNER] Loading task descriptions...")
            task_descriptions = self.task_registry.get_task_descriptions()
            if not task_descriptions:
                logger.warning("[PLANNER] No task descriptions loaded")
                task_descriptions = {}

            # Step 2: Build system prompt with task list, descriptions, and suggestions (DYNAMIC)
            system_prompt = build_planner_prompt(
                task_names, 
                task_descriptions,
                suggested_tasks=suggested_tasks
            )

            # Step 3: Call LLM for autonomous decomposition
            logger.info("[PLANNER] Calling LLM for decomposition...")
            response = self.llm.complete(
                system=system_prompt,
                user=user_request.strip(),
                max_tokens=1500,
                temperature=0.1  # Low temp for consistency
            )

            # Step 4: Parse plan JSON
            plan = self._parse_plan_response(response)

            # Step 5: Clean up required_tasks — remove workflow control tasks (Start, End, etc.)
            if plan.get("is_valid") and plan.get("required_tasks"):
                original_tasks = plan.get("required_tasks", [])
                cleaned_tasks = self._filter_control_tasks(original_tasks)
                
                if cleaned_tasks != original_tasks:
                    logger.info(
                        "[PLANNER] Filtered control tasks: %s → %s",
                        original_tasks,
                        cleaned_tasks
                    )
                    plan["required_tasks"] = cleaned_tasks
                else:
                    logger.info("[PLANNER] No control tasks found in required_tasks")

            elapsed = time.time() - start_time
            logger.info(
                "[PLANNER] [OK] Plan generated in %.2fs - confidence: %d%%",
                elapsed,
                plan.get("confidence", 0)
            )

            return {
                "success": True,
                "plan": plan,
                "confidence": plan.get("confidence", 0),
                "ambiguities": plan.get("ambiguities", []),
                "error": None
            }

        except Exception as e:
            logger.exception("[PLANNER] Planning failed: %s", str(e))
            return self._error_response(f"Planning error: {str(e)}")

    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate LLM response as plan JSON.

        Returns:
            Parsed plan dict or empty plan on error
        """
        if not response or not response.strip():
            logger.error("[PLANNER] Empty LLM response")
            return self._empty_plan()

        # Extract JSON from potential markdown
        response = self._extract_json(response)

        try:
            plan = json.loads(response)
            
            # Validate required fields
            if not isinstance(plan, dict):
                logger.error("[PLANNER] Plan is not a JSON object")
                return self._empty_plan()

            # Enrich with metadata
            plan["timestamp"] = time.time()
            plan["is_valid"] = self._validate_plan(plan)

            return plan

        except json.JSONDecodeError as e:
            logger.error("[PLANNER] JSON parse error: %s", str(e))
            logger.debug("[PLANNER] Response: %.200s", response)
            return self._empty_plan()

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text, handling markdown fences."""
        # Remove markdown fences if present
        if "```" in text:
            start = text.find("```")
            end = text.rfind("```")
            if start != -1 and end != -1 and end > start:
                text = text[start + 3:end].strip()
                # Remove language tag if present
                if text.startswith("json"):
                    text = text[4:].strip()

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]

        return text

    @staticmethod
    def _validate_plan(plan: Dict) -> bool:
        """
        Validate plan structure.

        Returns True if plan has minimum required fields.
        """
        required_fields = ["user_intention", "steps", "required_tasks", "confidence"]
        
        for field in required_fields:
            if field not in plan:
                logger.warning("[PLANNER] Missing required field: %s", field)
                return False

        if not isinstance(plan.get("steps"), list) or len(plan["steps"]) == 0:
            logger.warning("[PLANNER] Steps must be non-empty list")
            return False

        return True

    @staticmethod
    def _empty_plan() -> Dict[str, Any]:
        """Return empty plan structure."""
        return {
            "user_intention": "",
            "steps": [],
            "required_tasks": [],
            "confidence": 0,
            "ambiguities": ["Failed to generate plan"],
            "is_valid": False
        }

    @staticmethod
    def _filter_control_tasks(task_names: List[str]) -> List[str]:
        """
        Filter out workflow control tasks that are implicit/mandatory.
        
        Control tasks like Tasks Overview are not "required tasks"
        — they are implicit in every workflow and should not be listed.
        Start and End tasks are kept as they are considered required.
        
        Args:
            task_names: List of task names from LLM plan
            
        Returns:
            Filtered list with control tasks removed
        """
        # Tasks to exclude (case-insensitive)
        control_tasks = {"Tasks Overview"}
        
        filtered = [
            task for task in task_names
            if task not in control_tasks
        ]
        
        return filtered

    @staticmethod
    def _error_response(error_msg: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            "success": False,
            "plan": None,
            "confidence": 0,
            "ambiguities": [],
            "error": error_msg
        }

    @staticmethod
    def _get_fallback_tasks() -> List[str]:
        """Fallback task list if registry fails."""
        return [
            "CmdStage",
            "AppStage",
            "HttpRequest",
            "Sleep",
            "CompareStrings",
            "CompareNumber",
            "IntegerSingleOps",
            "ScreenAutomator",
            "TextReport",
            "SetVariable",
            "GetCurrentLocation",
            "DnsLookup",
            "AndromateException"
        ]
