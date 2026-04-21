"""
JSON Validator for AI Agent workflow post-processing.

Responsibilities:
- Syntactic validation: json.loads() with precise error capture
- Structural validation: workflow-specific business rules
  1. Start node with id "-1000" exists
  2. At least one End node exists
  3. All ids in Links exist in declared nodes
  4. All variables in tasks start with "$"
  5. All variables used in tasks are declared in Start
  6. Every node except End has at least one outgoing link
  7. All node IDs are unique across the workflow
  8. End node IDs are less than -1000 (e.g., "-2000")

Why this module exists:
    json.loads() only catches syntax errors.
    A workflow can be valid JSON but logically broken:
    - A Link pointing to a non-existent node id
    - A variable "$RESULT" used in CmdStage but missing from Start variables
    - A node with no outgoing link (workflow would hang on Android)
    These errors are invisible to json.loads() but cause silent failures
    during execution on the Android mobile application.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.utilities.logger import get_module_logger

logger = get_module_logger("json_validator")

# Node types that are NOT End nodes
EXECUTION_NODE_TYPES = {
    "CmdStage",
    "AppStage",
    "CompareStrings",
    "CompareNumber",
    "IntegerSingleOps",
    "Start",
}

# Reserved ids
START_ID = "-1000"


@dataclass
class ValidationResult:
    """
    Result of a validation pass.

    Attributes:
        is_valid:   True if all checks passed
        errors:     List of human-readable error messages
        parsed:     Parsed JSON dict if syntax valid, else None
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    parsed: Optional[Dict[str, Any]] = None

    def add_error(self, message: str) -> None:
        self.is_valid = False
        self.errors.append(message)


class JSONValidator:
    """
    Two-level validator for LLM-generated workflow JSON.

    Level 1 — Syntactic: is the string valid JSON ?
    Level 2 — Structural: does it respect workflow business rules ?
    """

    def validate(self, json_string: str) -> ValidationResult:
        """
        Run full validation pipeline on a JSON string.

        Args:
            json_string: clean JSON string from JSONExtractor

        Returns:
            ValidationResult with is_valid flag, error list, parsed dict
        """
        logger.info("[VALIDATOR] Starting validation")

        # Level 1 — Syntactic
        result = self._validate_syntax(json_string)
        if not result.is_valid:
            logger.warning("[VALIDATOR] Syntax validation failed: %s", result.errors)
            return result

        # Level 2 — Structural (only if syntax passed)
        self._validate_structure(result)

        if result.is_valid:
            logger.info("[VALIDATOR] Validation passed — workflow is valid")
        else:
            logger.warning(
                "[VALIDATOR] Structural validation failed (%d errors): %s",
                len(result.errors),
                result.errors
            )

        return result

    # --------------------------------------------------
    # Level 1 — Syntactic validation
    # --------------------------------------------------
    def _validate_syntax(self, json_string: str) -> ValidationResult:
        """
        Attempt json.loads() and capture precise error.
        """
        result = ValidationResult(is_valid=True)

        try:
            parsed = json.loads(json_string)
            result.parsed = parsed
            logger.debug("[VALIDATOR] Syntax OK")
        except json.JSONDecodeError as e:
            result.add_error(
                f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}"
            )

        return result

    # --------------------------------------------------
    # Level 2 — Structural validation
    # --------------------------------------------------
    def _validate_structure(self, result: ValidationResult) -> None:
        """
        Run all structural checks on the parsed workflow dict.
        Mutates result in place — adds errors if checks fail.
        """
        workflow = result.parsed

        if not isinstance(workflow, dict):
            result.add_error("Workflow must be a JSON object (dict), not a list or primitive.")
            return

        # Collect all declared node ids across all node types
        declared_ids, total_nodes = self._collect_all_ids(workflow)
        if len(declared_ids) != total_nodes:
            result.add_error("Duplicate node IDs found. All node IDs must be unique.")
        logger.debug("[VALIDATOR] Declared node ids: %s", declared_ids)

        # Check 1 — Start node with id -1000
        self._check_start_node(workflow, result)

        # Check 2 — At least one End node
        self._check_end_nodes(workflow, result)

        # Check 3 — All ids in Links exist
        self._check_links_integrity(workflow, declared_ids, result)

        # Check 4 & 5 — Variables start with $ and are declared in Start
        self._check_variables(workflow, result)

        # Check 6 — Every non-End node has at least one outgoing link
        self._check_outgoing_links(workflow, declared_ids, result)

    # --------------------------------------------------
    # Check 1 — Start node
    # --------------------------------------------------
    def _check_start_node(self, workflow: Dict, result: ValidationResult) -> None:
        start_nodes = workflow.get("Start", [])

        if not start_nodes:
            result.add_error(
                'Missing "Start" node. Every workflow must have exactly one Start node.'
            )
            return

        if len(start_nodes) > 1:
            result.add_error(
                f'Found {len(start_nodes)} Start nodes. Exactly one is required.'
            )

        start = start_nodes[0]
        if start.get("id") != START_ID:
            result.add_error(
                f'Start node id must be "{START_ID}", found "{start.get("id")}".'
            )

        if "variables" not in start:
            result.add_error('Start node is missing "variables" array.')
        elif not isinstance(start["variables"], list):
            result.add_error('"variables" in Start must be an array.')

        logger.debug("[VALIDATOR] Check 1 (Start node) done")

    # --------------------------------------------------
    # Check 2 — End nodes
    # --------------------------------------------------
    def _check_end_nodes(self, workflow: Dict, result: ValidationResult) -> None:
        end_nodes = workflow.get("End", [])

        if not end_nodes:
            result.add_error(
                'Missing "End" node. Every workflow must have at least one End node.'
            )
            return

        for end in end_nodes:
            end_id = end.get("id")
            if not end_id:
                result.add_error('An End node is missing its "id" field.')
                continue
            # Check that End ID is less than -1000 (lower than task IDs)
            try:
                if int(end_id) >= -1000:
                    result.add_error(
                        f'End node ID "{end_id}" must be less than -1000 '
                        f'(e.g., "-2000"). Task IDs start at -1001.'
                    )
            except ValueError:
                result.add_error(
                    f'End node ID "{end_id}" is not a valid integer string.'
                )

        logger.debug("[VALIDATOR] Check 2 (End nodes) done")

    # --------------------------------------------------
    # Check 3 — Links integrity
    # --------------------------------------------------
    def _check_links_integrity(
        self,
        workflow: Dict,
        declared_ids: set,
        result: ValidationResult
    ) -> None:
        links = workflow.get("Links", [])

        if not links:
            result.add_error(
                '"Links" array is missing or empty. '
                'Workflow has no connections between nodes.'
            )
            return

        for i, link in enumerate(links):
            # Check "from" exists
            from_id = link.get("from")
            if not from_id:
                result.add_error(f'Link at index {i} is missing "from" field.')
                continue

            if from_id not in declared_ids:
                result.add_error(
                    f'Link at index {i}: "from" id "{from_id}" '
                    f'does not match any declared node.'
                )

            # Check all destination ids (to, true, false)
            for dest_key in ("to", "true", "false"):
                dest_id = link.get(dest_key)
                if dest_id and dest_id not in declared_ids:
                    result.add_error(
                        f'Link at index {i}: "{dest_key}" id "{dest_id}" '
                        f'does not match any declared node.'
                    )

        logger.debug("[VALIDATOR] Check 3 (Links integrity) done")

    # --------------------------------------------------
    # Check 4 & 5 — Variables
    # --------------------------------------------------
    def _check_variables(self, workflow: Dict, result: ValidationResult) -> None:
        """
        Check 4: All variable names start with "$"
        Check 5: All variables used in tasks are declared in Start
        """
        # Collect declared variable names from Start
        start_nodes = workflow.get("Start", [{}])
        start_variables = set()

        if start_nodes:
            for var in start_nodes[0].get("variables", []):
                name = var.get("variableName", "")
                if name:
                    # Check 4 — must start with $
                    if not name.startswith("$"):
                        result.add_error(
                            f'Variable "{name}" in Start does not start with "$". '
                            f'All variable names must begin with "$".'
                        )
                    else:
                        start_variables.add(name)

        # Scan all task nodes for variable references
        variable_fields = {
            "CmdStage": ["cmd_result_output", "cmd_error_output"],
            "IntegerSingleOps": ["var_n1", "var_n2", "ops_output"],
            "CompareStrings": ["var_x", "var_y"],
            "CompareNumber": ["num_x", "num_y"],
        }

        for node_type, fields in variable_fields.items():
            for node in workflow.get(node_type, []):
                for field_name in fields:
                    value = node.get(field_name, "")
                    if isinstance(value, str) and value.startswith("$"):
                        if value not in start_variables:
                            result.add_error(
                                f'Variable "{value}" used in {node_type} '
                                f'(id={node.get("id")}) is not declared in Start variables.'
                            )

        logger.debug("[VALIDATOR] Check 4 & 5 (Variables) done")

    # --------------------------------------------------
    # Check 6 — Outgoing links
    # --------------------------------------------------
    def _check_outgoing_links(
        self,
        workflow: Dict,
        declared_ids: set,
        result: ValidationResult
    ) -> None:
        """
        Every node except End must have at least one outgoing link.
        A node with no outgoing link means the workflow hangs on Android.
        """
        links = workflow.get("Links", [])
        end_ids = {end.get("id") for end in workflow.get("End", [])}

        # Collect all ids that have at least one outgoing link
        ids_with_outgoing = {link.get("from") for link in links if link.get("from")}

        for node_id in declared_ids:
            if node_id in end_ids:
                continue  # End nodes don't need outgoing links
            if node_id not in ids_with_outgoing:
                result.add_error(
                    f'Node id "{node_id}" has no outgoing link in Links. '
                    f'Every non-End node must have at least one outgoing connection.'
                )

        logger.debug("[VALIDATOR] Check 6 (Outgoing links) done")

    # --------------------------------------------------
    # Helper — collect all declared ids
    # --------------------------------------------------
    def _collect_all_ids(self, workflow: Dict) -> tuple[set, int]:
        """
        Collect all node ids across Start, End, and all task types.
        Returns the set of unique ids and the total count of nodes.
        """
        all_ids = []
        skip_keys = {"Links"}

        for key, nodes in workflow.items():
            if key in skip_keys:
                continue
            if isinstance(nodes, list):
                for node in nodes:
                    if isinstance(node, dict) and "id" in node:
                        all_ids.append(node["id"])

        declared_ids = set(all_ids)
        return declared_ids, len(all_ids)