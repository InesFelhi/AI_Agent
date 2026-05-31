#!/usr/bin/env python3
from src.workflow.json_validator import JSONValidator

def test_duplicate_ids():
    validator = JSONValidator()
    json_str = '{"Start": [{"id": "-1000", "variables": []}], "CmdStage": [{"id": "-1001"}, {"id": "-1001"}], "End": [{"id": "-2000"}], "Links": []}'
    result = validator.validate(json_str)
    print('Duplicate IDs test:', result.is_valid, result.errors)
    assert not result.is_valid
    assert any('Duplicate node IDs' in error for error in result.errors)

def test_invalid_end_id():
    validator = JSONValidator()
    json_str = '{"Start": [{"id": "-1000", "variables": []}], "End": [{"id": "-999"}], "Links": []}'
    result = validator.validate(json_str)
    print('Invalid End ID test:', result.is_valid, result.errors)
    assert not result.is_valid
    assert any('must be less than -1000' in error for error in result.errors)

def test_valid_workflow():
    validator = JSONValidator()
    json_str = '{"Start": [{"id": "-1000", "variables": []}], "CmdStage": [{"id": "-1001"}], "End": [{"id": "-2000"}], "Links": [{"from": "-1000", "to": "-1001"}, {"from": "-1001", "to": "-2000"}]}'
    result = validator.validate(json_str)
    print('Valid workflow test:', result.is_valid, result.errors)
    assert result.is_valid

if __name__ == '__main__':
    test_duplicate_ids()
    test_invalid_end_id()
    test_valid_workflow()
    print('All tests passed!')