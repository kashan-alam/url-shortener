import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lambdas/redirect"))
os.environ["TABLE_NAME"] = "test-table"

from handler import lambda_handler

@patch("handler.table")
def test_redirect_valid_code(mock_table):
    """Valid code should return 301 redirect to original URL."""
    mock_table.get_item = MagicMock(return_value={
        "Item": {
            "code": "abc123",
            "original_url": "https://www.example.com/long/path"
        }
    })

    event = {"pathParameters": {"code": "abc123"}}
    result = lambda_handler(event, {})

    assert result["statusCode"] == 301
    assert result["headers"]["Location"] == "https://www.example.com/long/path"

@patch("handler.table")
def test_redirect_unknown_code(mock_table):
    """Unknown code should return 404."""
    mock_table.get_item = MagicMock(return_value={})  # No "Item" key

    event = {"pathParameters": {"code": "xxxxxx"}}
    result = lambda_handler(event, {})

    assert result["statusCode"] == 404

@patch("handler.table")
def test_redirect_missing_code(mock_table):
    """Missing code in path should return 400."""
    event = {"pathParameters": {}}
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400

@patch("handler.table")
def test_redirect_no_path_parameters(mock_table):
    """No pathParameters at all should return 400."""
    event = {}
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400