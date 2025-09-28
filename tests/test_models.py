"""Tests for data models."""

import pytest
from pydantic import ValidationError

from slack_lists_mcp.models import (
    AddItemRequest,
    DeleteItemRequest,
    ErrorResponse,
    GetItemRequest,
    ListItemsRequest,
    UpdateItemRequest,
)


class TestAddItemRequest:
    """Tests for AddItemRequest model."""

    def test_valid_request(self):
        """Test creating a valid AddItemRequest."""
        request = AddItemRequest(
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
                                        {"type": "text", "text": "Test"},
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        )

        assert request.list_id == "F123"
        assert len(request.initial_fields) == 1
        # initial_fields contains FieldData objects
        assert request.initial_fields[0].column_id == "Col123"

    def test_missing_required_fields(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValidationError):
            AddItemRequest()

    def test_empty_initial_fields(self):
        """Test that empty initial_fields is valid."""
        request = AddItemRequest(
            list_id="F123",
            initial_fields=[],
        )
        assert request.list_id == "F123"
        assert request.initial_fields == []


class TestUpdateItemRequest:
    """Tests for UpdateItemRequest model."""

    def test_valid_request(self):
        """Test creating a valid UpdateItemRequest."""
        request = UpdateItemRequest(
            list_id="F123",
            cells=[
                {
                    "row_id": "Rec123",
                    "column_id": "Col123",
                    "text": "Updated",
                },
            ],
        )

        assert request.list_id == "F123"
        assert len(request.cells) == 1
        # cells contains CellData objects
        assert request.cells[0].row_id == "Rec123"

    def test_multiple_cells(self):
        """Test updating multiple cells."""
        request = UpdateItemRequest(
            list_id="F123",
            cells=[
                {
                    "row_id": "Rec123",
                    "column_id": "Col123",
                    "text": "Updated 1",
                },
                {
                    "row_id": "Rec123",
                    "column_id": "Col456",
                    "checkbox": True,
                },
            ],
        )

        assert len(request.cells) == 2
        # cells contains CellData objects
        assert request.cells[1].checkbox is True


class TestDeleteItemRequest:
    """Tests for DeleteItemRequest model."""

    def test_valid_request(self):
        """Test creating a valid DeleteItemRequest."""
        request = DeleteItemRequest(
            list_id="F123",
            item_id="Rec123",
        )

        assert request.list_id == "F123"
        assert request.item_id == "Rec123"

    def test_missing_fields(self):
        """Test that missing fields raises validation error."""
        with pytest.raises(ValidationError):
            DeleteItemRequest(list_id="F123")

        with pytest.raises(ValidationError):
            DeleteItemRequest(item_id="Rec123")


class TestGetItemRequest:
    """Tests for GetItemRequest model."""

    def test_valid_request(self):
        """Test creating a valid GetItemRequest."""
        request = GetItemRequest(
            list_id="F123",
            item_id="Rec123",
        )

        assert request.list_id == "F123"
        assert request.item_id == "Rec123"

    def test_with_include_subscribed(self):
        """Test with include_is_subscribed parameter."""
        request = GetItemRequest(
            list_id="F123",
            item_id="Rec123",
            include_is_subscribed=True,
        )

        assert request.include_is_subscribed is True

    def test_default_include_subscribed(self):
        """Test default value for include_is_subscribed."""
        request = GetItemRequest(
            list_id="F123",
            item_id="Rec123",
        )

        assert request.include_is_subscribed is False


class TestListItemsRequest:
    """Tests for ListItemsRequest model."""

    def test_valid_request(self):
        """Test creating a valid ListItemsRequest."""
        request = ListItemsRequest(
            list_id="F123",
        )

        assert request.list_id == "F123"
        assert request.limit == 100  # Default
        assert request.cursor is None
        assert request.archived is None
        assert request.completed_only is None
        assert request.assignee is None

    def test_with_all_parameters(self):
        """Test with all parameters specified."""
        request = ListItemsRequest(
            list_id="F123",
            limit=50,
            cursor="page_token",
            archived=True,
            completed_only=True,
            assignee="U123",
            sort_by="created_at",
            sort_order="desc",
        )

        assert request.limit == 50
        assert request.cursor == "page_token"
        assert request.archived is True
        assert request.completed_only is True
        assert request.assignee == "U123"
        assert request.sort_by == "created_at"
        assert request.sort_order == "desc"

    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Valid limits
        request = ListItemsRequest(list_id="F123", limit=1)
        assert request.limit == 1

        request = ListItemsRequest(list_id="F123", limit=1000)
        assert request.limit == 1000

        # Invalid limits
        with pytest.raises(ValidationError):
            ListItemsRequest(list_id="F123", limit=0)

        with pytest.raises(ValidationError):
            ListItemsRequest(list_id="F123", limit=1001)

    def test_sort_parameters(self):
        """Test sort parameters."""
        request = ListItemsRequest(
            list_id="F123",
            sort_by="updated_at",
            sort_order="asc",
        )

        assert request.sort_by == "updated_at"
        assert request.sort_order == "asc"

        # Test defaults
        request2 = ListItemsRequest(list_id="F123")
        assert request2.sort_by is None
        assert request2.sort_order is None


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_simple_error(self):
        """Test creating a simple error response."""
        error = ErrorResponse(
            error="Something went wrong",
        )

        assert error.error == "Something went wrong"
        assert error.error_code is None
        assert error.details is None

    def test_detailed_error(self):
        """Test creating a detailed error response."""
        error = ErrorResponse(
            error="API Error",
            error_code="list_not_found",
            details={
                "list_id": "F123",
                "message": "The specified list does not exist",
            },
        )

        assert error.error == "API Error"
        assert error.error_code == "list_not_found"
        assert error.details["list_id"] == "F123"

    def test_json_serialization(self):
        """Test JSON serialization of error response."""
        error = ErrorResponse(
            error="Test error",
            error_code="test_code",
            details={"key": "value"},
        )

        json_data = error.model_dump_json()
        assert "test_code" in json_data
        assert "Test error" in json_data
