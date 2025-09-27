"""Tests for field normalization functionality."""

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
async def test_field_normalization_for_add_item(mock_slack_client):
    """Test field normalization when adding items."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with plain text that should be converted to rich_text
    # and select field as a single value that should be wrapped in array
    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "text": "Plain text task",  # Should be converted to rich_text
            },
            {
                "column_id": "Col456",
                "select": "OptABC",  # Should be wrapped in array
            },
            {
                "column_id": "Col789",
                "user": "U123",  # Should be wrapped in array
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify the API was called with normalized fields
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    # Check text was converted to rich_text
    assert "rich_text" in normalized_fields[0]
    assert "text" not in normalized_fields[0]
    assert (
        normalized_fields[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Plain text task"
    )

    # Check select was wrapped in array
    assert isinstance(normalized_fields[1]["select"], list)
    assert normalized_fields[1]["select"] == ["OptABC"]

    # Check user was wrapped in array
    assert isinstance(normalized_fields[2]["user"], list)
    assert normalized_fields[2]["user"] == ["U123"]


@pytest.mark.asyncio
async def test_field_normalization_for_update_item(mock_slack_client):
    """Test field normalization when updating items."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with plain text and single select value
    result = await client.update_item(
        list_id="F123",
        cells=[
            {
                "row_id": "Rec123",
                "column_id": "Col123",
                "text": "Updated text",  # Should be converted to rich_text
            },
            {
                "row_id": "Rec123",
                "column_id": "Col456",
                "select": "OptXYZ",  # Should be wrapped in array
            },
        ],
    )

    assert result["success"] is True

    # Verify the API was called with normalized cells
    actual_call = mock_slack_client.api_call.call_args
    normalized_cells = actual_call[1]["json"]["cells"]

    # Check text was converted to rich_text
    assert "rich_text" in normalized_cells[0]
    assert "text" not in normalized_cells[0]
    assert (
        normalized_cells[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Updated text"
    )

    # Check select was wrapped in array
    assert isinstance(normalized_cells[1]["select"], list)
    assert normalized_cells[1]["select"] == ["OptXYZ"]


@pytest.mark.asyncio
async def test_field_normalization_preserves_arrays(mock_slack_client):
    """Test that normalization doesn't modify fields already in correct format."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with fields already in correct format
    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "rich_text": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {"type": "text", "text": "Already formatted"}
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "column_id": "Col456",
                "select": ["OptABC", "OptDEF"],  # Already an array
            },
            {
                "column_id": "Col789",
                "user": ["U123", "U456"],  # Already an array
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify the API was called with fields unchanged
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    # Rich text should remain unchanged
    assert (
        normalized_fields[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Already formatted"
    )

    # Arrays should remain as arrays
    assert normalized_fields[1]["select"] == ["OptABC", "OptDEF"]
    assert normalized_fields[2]["user"] == ["U123", "U456"]


@pytest.mark.asyncio
async def test_field_normalization_handles_checkbox(mock_slack_client):
    """Test that checkbox fields are not modified."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "checkbox": True,  # Boolean values should remain as-is
            },
            {
                "column_id": "Col456",
                "checkbox": False,
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify checkbox fields remain as boolean
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert normalized_fields[0]["checkbox"] is True
    assert normalized_fields[1]["checkbox"] is False
