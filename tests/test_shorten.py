import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Make lambdas importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lambdas/shorten"))

# Set required environment variables before importing
os.environ["TABLE_NAME"] = "test-table"
os.environ["BASE_URL"] = "https://short.test"

from handler import lambda_handler, generate_code

# ─── Unit tests for generate_code ─────────────────────

def test_generate_code_length():
    """Code should be exactly 6 characters by default."""
    code = generate_code()
    assert len(code) == 6

def test_generate_code_is_alphanumeric():
    """Code should only contain letters and digits."""
    code = generate_code()
    assert code.isalnum()

def test_generate_code_custom_length():
    """Custom length should work."""
    code = generate_code(length=10)
    assert len(code) == 10

def test_generate_code_unique():
    """Two generated codes should not be the same (almost always)."""
    codes = {generate_code() for _ in range(100)}
    assert len(codes) > 90  # Allow a tiny collision chance

# ─── Unit tests for lambda_handler ────────────────────

@patch("handler.table")   # Replace real DynamoDB with a fake
def test_shorten_valid_url(mock_table):
    """A valid URL should return 200 with a short_url."""
    mock_table.put_item = MagicMock()

    event = {
        "body": json.dumps({"url": "https://www.example.com/some/long/path"})
    }

    result = lambda_handler(event, {})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "short_url" in body
    assert body["short_url"].startswith("https://short.test/")
    assert len(body["code"]) == 6
    mock_table.put_item.assert_called_once()   # DynamoDB was called

@patch("handler.table")
def test_shorten_missing_url(mock_table):
    """Missing url field should return 400."""
    event = {"body": json.dumps({})}
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400

@patch("handler.table")
def test_shorten_empty_url(mock_table):
    """Empty url should return 400."""
    event = {"body": json.dumps({"url": ""})}
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400

@patch("handler.table")
def test_shorten_invalid_url(mock_table):
    """URL not starting with http should return 400."""
    event = {"body": json.dumps({"url": "not-a-url"})}
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400

@patch("handler.table")
def test_shorten_saves_to_dynamodb(mock_table):
    """Verify the item saved to DynamoDB has correct fields."""
    mock_table.put_item = MagicMock()

    event = {"body": json.dumps({"url": "https://example.com"})}
    lambda_handler(event, {})

    call_args = mock_table.put_item.call_args[1]  # keyword args
    item = call_args["Item"]

    assert "code" in item
    assert item["original_url"] == "https://example.com"
    assert "created_at" in item