import pytest
from src.workflow.json_validator import JSONValidator


class TestJSONValidator:
    """Tests for JSONValidator, including new uniqueness and End ID checks."""

    @pytest.fixture
    def validator(self):
        return JSONValidator()

    def test_duplicate_node_ids(self, validator):
        """Test that duplicate node IDs are detected."""
        json_str = '''{
            "Start": [{"id": "-1000", "variables": []}],
            "CmdStage": [{"id": "-1001"}, {"id": "-1001"}],
            "End": [{"id": "-2000"}],
            "Links": []
        }'''
        result = validator.validate(json_str)
        assert not result.is_valid
        assert any("Duplicate node IDs found" in error for error in result.errors)

    def test_invalid_end_id(self, validator):
        """Test that End IDs >= -1000 are rejected."""
        json_str = '''{
            "Start": [{"id": "-1000", "variables": []}],
            "End": [{"id": "-999"}],
            "Links": []
        }'''
        result = validator.validate(json_str)
        assert not result.is_valid
        assert any("must be less than -1000" in error for error in result.errors)

    def test_valid_end_id(self, validator):
        """Test that valid End IDs < -1000 are accepted."""
        json_str = '''{
            "Start": [{"id": "-1000", "variables": []}],
            "End": [{"id": "-2000"}],
            "Links": []
        }'''
        result = validator.validate(json_str)
        # Should fail due to missing links, but not due to End ID
        assert not result.is_valid  # Because of other checks
        assert not any("must be less than -1000" in error for error in result.errors)

    def test_unique_ids_valid_workflow(self, validator):
        """Test that a valid workflow with unique IDs passes."""
        json_str = '''{
            "Start": [{"id": "-1000", "variables": []}],
            "CmdStage": [{"id": "-1001"}],
            "End": [{"id": "-2000"}],
            "Links": [{"from": "-1000", "to": "-1001"}, {"from": "-1001", "to": "-2000"}]
        }'''
        result = validator.validate(json_str)
        assert result.is_valid
        assert not result.errors

    def test_non_integer_end_id(self, validator):
        """Test that non-integer End IDs are handled gracefully."""
        json_str = '''{
            "Start": [{"id": "-1000", "variables": []}],
            "End": [{"id": "invalid"}],
            "Links": []
        }'''
        result = validator.validate(json_str)
        assert not result.is_valid
        assert any("is not a valid integer string" in error for error in result.errors)