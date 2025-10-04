"""Tests for validation error handling."""

from unittest.mock import MagicMock, patch

import pytest
from slack_lists_mcp.slack_client import SlackListsClient


@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    with patch("slack_lists_mcp.slack_client.WebClient") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_validation_error_missing_column_id(mock_slack_client):
    """Test validation error when column_id is missing."""
    client = SlackListsClient()
    client.client = mock_slack_client

    with pytest.raises(ValueError, match="Each field must have a 'column_id'"):
        await client.add_item(
            list_id="F123",
            initial_fields=[
                {
                    "text": "Task without column_id",  # Missing column_id
                },
            ],
        )


@pytest.mark.asyncio
async def test_validation_error_missing_value(mock_slack_client):
    """Test validation error when field has no value."""
    client = SlackListsClient()
    client.client = mock_slack_client

    with pytest.raises(ValueError, match="must have a value"):
        await client.add_item(
            list_id="F123",
            initial_fields=[
                {
                    "column_id": "Col123",
                    # No value field
                },
            ],
        )


@pytest.mark.asyncio
async def test_validation_success_with_valid_fields(mock_slack_client):
    """Test that valid fields pass validation."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # This should not raise an exception
    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "text": "Valid task",
            },
            {
                "column_id": "Col456",
                "user": ["U123456"],
            },
        ],
    )

    assert result["id"] == "Rec123"
