"""Integration tests for Slack Lists MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastmcp import Client

from slack_lists_mcp.server import mcp


class TestSlackListsIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_item_lifecycle(self):
        """Test complete lifecycle: create, read, update, delete."""
        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            # Setup mock responses for the complete workflow
            mock_client.add_item = AsyncMock(
                return_value={
                    "id": "Rec123",
                    "list_id": "F123",
                    "fields": [
                        {"column_id": "Col123", "text": "Initial Item"},
                        {"column_id": "Col456", "select": ["status1"]},
                    ],
                }
            )
            
            mock_client.get_item = AsyncMock(
                return_value={
                    "item": {  # Changed from "record" to "item"
                        "id": "Rec123",
                        "fields": [
                            {"column_id": "Col123", "text": "Initial Item"},
                            {"column_id": "Col456", "select": ["status1"]},
                        ],
                    },
                    "list": {"list_metadata": {"schema": []}},
                    "subtasks": [],
                }
            )
            
            mock_client.update_item = AsyncMock(
                return_value={"success": True}
            )
            
            mock_client.delete_item = AsyncMock(
                return_value=True
            )
            
            async with Client(mcp) as client:
                # 1. Create item
                create_result = await client.call_tool(
                    "add_list_item",
                    {
                        "list_id": "F123",
                        "initial_fields": [
                            {
                                "column_id": "Col123",
                                "rich_text": [
                                    {
                                        "type": "rich_text",
                                        "elements": [
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {"type": "text", "text": "Initial Item"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                )
                
                assert create_result.data["success"] is True
                assert create_result.data["item"]["id"] == "Rec123"
                
                # 2. Read item
                read_result = await client.call_tool(
                    "get_list_item",
                    {
                        "list_id": "F123",
                        "item_id": "Rec123",
                    },
                )
                
                assert read_result.data["success"] is True
                assert read_result.data["item"]["id"] == "Rec123"
                
                # 3. Update item
                update_result = await client.call_tool(
                    "update_list_item",
                    {
                        "list_id": "F123",
                        "cells": [
                            {
                                "row_id": "Rec123",
                                "column_id": "Col456",
                                "select": ["status2"],
                            }
                        ],
                    },
                )
                
                assert update_result.data["success"] is True
                
                # 4. Delete item
                delete_result = await client.call_tool(
                    "delete_list_item",
                    {
                        "list_id": "F123",
                        "item_id": "Rec123",
                    },
                )
                
                assert delete_result.data["success"] is True
                assert delete_result.data["deleted"] is True
    
    @pytest.mark.asyncio
    async def test_list_with_filters_workflow(self):
        """Test listing items with various filter combinations."""
        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            # Setup items with different attributes
            all_items = [
                {
                    "id": "Rec1",
                    "fields": [
                        {"key": "name", "text": "Task 1"},
                        {"key": "status", "select": ["active"]},
                        {"key": "completed", "checkbox": False},
                    ],
                },
                {
                    "id": "Rec2",
                    "fields": [
                        {"key": "name", "text": "Task 2"},
                        {"key": "status", "select": ["completed"]},
                        {"key": "completed", "checkbox": True},
                    ],
                },
                {
                    "id": "Rec3",
                    "fields": [
                        {"key": "name", "text": "Project 1"},
                        {"key": "status", "select": ["active"]},
                        {"key": "completed", "checkbox": False},
                    ],
                },
            ]
            
            mock_client.list_items = AsyncMock(
                return_value={
                    "items": all_items,
                    "has_more": False,
                    "next_cursor": None,
                    "total": 3,
                }
            )
            
            async with Client(mcp) as client:
                # Test 1: Filter by name containing "Task"
                result = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "filters": {"name": {"contains": "Task"}},
                    },
                )
                
                assert result.data["success"] is True
                # The client will filter client-side, so check the mock was called
                mock_client.list_items.assert_called_with(
                    list_id="F123",
                    limit=100,  # Server passes limit directly to client
                    cursor=None,
                    archived=None,
                    filters={"name": {"contains": "Task"}},
                )
                
                # Test 2: Filter by status equals "active"
                result = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "filters": {"status": {"equals": "active"}},
                    },
                )
                
                assert result.data["success"] is True
                
                # Test 3: Multiple filters
                result = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "filters": {
                            "status": {"equals": "active"},
                            "completed": {"equals": False},
                        },
                    },
                )
                
                assert result.data["success"] is True
    
    @pytest.mark.asyncio
    async def test_structure_aware_operations(self):
        """Test operations that depend on understanding list structure."""
        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            # Mock getting list structure
            mock_client.list_items = AsyncMock(
                return_value={
                    "items": [{"id": "Rec1"}],
                }
            )
            
            mock_client.get_item = AsyncMock(
                return_value={
                    "list": {
                        "list_metadata": {
                            "schema": [
                                {
                                    "id": "Col123",
                                    "name": "Title",
                                    "key": "title",
                                    "type": "text",
                                    "is_primary_column": True,
                                },
                                {
                                    "id": "Col456",
                                    "name": "Status",
                                    "key": "status",
                                    "type": "select",
                                    "options": {
                                        "choices": [
                                            {"value": "opt1", "label": "To Do"},
                                            {"value": "opt2", "label": "Done"},
                                        ]
                                    },
                                },
                                {
                                    "id": "Col789",
                                    "name": "Assignee",
                                    "key": "assignee",
                                    "type": "user",
                                },
                            ],
                            "views": [],
                        }
                    },
                    "record": {"id": "Rec1", "fields": []},
                }
            )
            
            mock_client.add_item = AsyncMock(
                return_value={
                    "id": "Rec2",
                    "fields": [
                        {"column_id": "Col123", "text": "New Task"},
                        {"column_id": "Col456", "select": ["opt1"]},
                        {"column_id": "Col789", "user": ["U123"]},
                    ],
                }
            )
            
            async with Client(mcp) as client:
                # 1. Get structure first
                structure_result = await client.call_tool(
                    "get_list_structure",
                    {"list_id": "F123"},
                )
                
                assert structure_result.data["success"] is True
                columns = structure_result.data["structure"]["columns"]
                assert "Col123" in columns
                assert columns["Col123"]["name"] == "Title"
                
                # 2. Create item with proper field types based on structure
                create_result = await client.call_tool(
                    "add_list_item",
                    {
                        "list_id": "F123",
                        "initial_fields": [
                            {
                                "column_id": "Col123",
                                "rich_text": [
                                    {
                                        "type": "rich_text",
                                        "elements": [
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {"type": "text", "text": "New Task"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "column_id": "Col456",
                                "select": ["opt1"],
                            },
                            {
                                "column_id": "Col789",
                                "user": ["U123"],
                            },
                        ],
                    },
                )
                
                assert create_result.data["success"] is True
                assert create_result.data["item"]["id"] == "Rec2"
    
    @pytest.mark.asyncio
    async def test_pagination_handling(self):
        """Test pagination handling for large lists."""
        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            # First page
            mock_client.list_items = AsyncMock(
                side_effect=[
                    {
                        "items": [
                            {"id": f"Rec{i}", "fields": []}
                            for i in range(10)
                        ],
                        "has_more": True,
                        "next_cursor": "cursor_page2",
                        "total": 25,
                    },
                    {
                        "items": [
                            {"id": f"Rec{i}", "fields": []}
                            for i in range(10, 20)
                        ],
                        "has_more": True,
                        "next_cursor": "cursor_page3",
                        "total": 25,
                    },
                    {
                        "items": [
                            {"id": f"Rec{i}", "fields": []}
                            for i in range(20, 25)
                        ],
                        "has_more": False,
                        "next_cursor": None,
                        "total": 25,
                    },
                ]
            )
            
            async with Client(mcp) as client:
                # Page 1
                result1 = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "limit": 10,
                    },
                )
                
                assert result1.data["success"] is True
                assert len(result1.data["items"]) == 10
                assert result1.data["has_more"] is True
                assert result1.data["next_cursor"] == "cursor_page2"
                
                # Page 2
                result2 = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "limit": 10,
                        "cursor": "cursor_page2",
                    },
                )
                
                assert result2.data["success"] is True
                assert len(result2.data["items"]) == 10
                assert result2.data["has_more"] is True
                
                # Page 3 (last)
                result3 = await client.call_tool(
                    "list_items",
                    {
                        "list_id": "F123",
                        "limit": 10,
                        "cursor": "cursor_page3",
                    },
                )
                
                assert result3.data["success"] is True
                assert len(result3.data["items"]) == 5
                assert result3.data["has_more"] is False
                assert result3.data["next_cursor"] is None
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error handling and recovery."""
        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            # Simulate various error conditions
            mock_client.add_item = AsyncMock(
                side_effect=[
                    Exception("Network error"),
                    {"id": "Rec123", "fields": []},  # Success on retry
                ]
            )
            
            async with Client(mcp) as client:
                # First attempt fails
                result1 = await client.call_tool(
                    "add_list_item",
                    {
                        "list_id": "F123",
                        "initial_fields": [
                            {"column_id": "Col123", "text": "Test"}
                        ],
                    },
                )
                
                assert result1.data["success"] is False
                assert "Network error" in result1.data["error"]
                
                # Simulate retry - should succeed
                mock_client.add_item.side_effect = None
                mock_client.add_item.return_value = {
                    "id": "Rec123",
                    "fields": [],
                }
                
                result2 = await client.call_tool(
                    "add_list_item",
                    {
                        "list_id": "F123",
                        "initial_fields": [
                            {"column_id": "Col123", "text": "Test"}
                        ],
                    },
                )
                
                assert result2.data["success"] is True
