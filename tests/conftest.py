"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Set test environment variables
os.environ["SLACK_BOT_TOKEN"] = "test-token"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "test-token")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    yield


@pytest.fixture
def sample_list_schema():
    """Sample list schema for testing."""
    return [
        {
            "id": "Col123",
            "name": "Name",
            "key": "name",
            "type": "text",
            "is_primary_column": True,
        },
        {
            "id": "Col456",
            "name": "Status",
            "key": "status",
            "type": "select",
            "is_primary_column": False,
            "options": {
                "choices": [
                    {"value": "opt1", "label": "To Do", "color": "red"},
                    {"value": "opt2", "label": "In Progress", "color": "yellow"},
                    {"value": "opt3", "label": "Done", "color": "green"},
                ],
                "format": "single_select",
            },
        },
        {
            "id": "Col789",
            "name": "Assignee",
            "key": "assignee",
            "type": "user",
            "is_primary_column": False,
            "options": {
                "format": "single_entity",
                "show_member_name": True,
            },
        },
        {
            "id": "Col101",
            "name": "Due Date",
            "key": "due_date",
            "type": "date",
            "is_primary_column": False,
        },
        {
            "id": "Col102",
            "name": "Completed",
            "key": "completed",
            "type": "checkbox",
            "is_primary_column": False,
        },
    ]


@pytest.fixture
def sample_items():
    """Sample list items for testing."""
    return [
        {
            "id": "Rec1",
            "list_id": "F123",
            "fields": [
                {"key": "name", "column_id": "Col123", "text": "First Task"},
                {"key": "status", "column_id": "Col456", "select": ["opt1"]},
                {"key": "assignee", "column_id": "Col789", "user": ["U123"]},
                {"key": "completed", "column_id": "Col102", "checkbox": False},
            ],
        },
        {
            "id": "Rec2",
            "list_id": "F123",
            "fields": [
                {"key": "name", "column_id": "Col123", "text": "Second Task"},
                {"key": "status", "column_id": "Col456", "select": ["opt2"]},
                {"key": "assignee", "column_id": "Col789", "user": ["U456"]},
                {"key": "completed", "column_id": "Col102", "checkbox": False},
            ],
        },
        {
            "id": "Rec3",
            "list_id": "F123",
            "fields": [
                {"key": "name", "column_id": "Col123", "text": "Completed Task"},
                {"key": "status", "column_id": "Col456", "select": ["opt3"]},
                {"key": "assignee", "column_id": "Col789", "user": ["U123"]},
                {"key": "completed", "column_id": "Col102", "checkbox": True},
            ],
        },
    ]


@pytest.fixture
def rich_text_field():
    """Sample rich text field structure."""
    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "text", "text": "Sample text"}
                ],
            }
        ],
    }

