"""Tests for schema-related tools."""

from unittest.mock import AsyncMock, patch

import pytest

from slack_lists_mcp.server import fetch_slack_documentation


class TestGetSchemaDocumentation:
    """Test get_schema_documentation tool."""

    @pytest.mark.asyncio
    async def test_fetch_documentation_success(self):
        """Test successful documentation fetch."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"<html>Test content</html>"
            mock_response.text = "<html>Test content</html>"
            mock_response.url = (
                "https://docs.slack.dev/reference/methods/slackLists.items.create/"
            )
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await fetch_slack_documentation(
                "https://docs.slack.dev/reference/methods/slackLists.items.create",
            )

            assert (
                result["url"]
                == "https://docs.slack.dev/reference/methods/slackLists.items.create/"
            )
            assert (
                result["original_url"]
                == "https://docs.slack.dev/reference/methods/slackLists.items.create"
            )
            assert result["status_code"] == 200
            assert "message" in result

    @pytest.mark.asyncio
    async def test_fetch_documentation_error(self):
        """Test documentation fetch with error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                Exception("Network error")
            )

            result = await fetch_slack_documentation(
                "https://docs.slack.dev/reference/methods/slackLists.items.create",
            )

            assert "error" in result
            assert "Network error" in result["error"]
