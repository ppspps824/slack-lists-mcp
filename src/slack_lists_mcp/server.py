"""FastMCP server for Slack Lists API operations."""

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fastmcp import Context, FastMCP

from slack_lists_mcp.config import get_settings
from slack_lists_mcp.slack_client import SlackListsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Configure logging level from settings
logging.getLogger().setLevel(getattr(logging, settings.log_level.upper()))

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version,
)

# Initialize Slack client
slack_client = SlackListsClient()


async def fetch_and_format_slack_documentation() -> str:
    """Slack APIドキュメントを動的に取得して整形する。

    Returns:
        整形されたドキュメント文字列

    """
    url = "https://docs.slack.dev/reference/methods/slackLists.items.create"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            formatted_doc = []

            # メインコンテンツを取得
            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", class_="content")
            )
            if not main_content:
                return "ドキュメントの取得に失敗しました。"

            # タイトルを抽出
            title = main_content.find("h1")
            if title:
                formatted_doc.append(f"# {title.get_text().strip()}")
                formatted_doc.append("")

            # 説明文を抽出
            first_p = main_content.find("p")
            if first_p:
                desc_text = first_p.get_text().strip()
                if desc_text:
                    formatted_doc.append("## 概要")
                    formatted_doc.append(desc_text)
                    formatted_doc.append("")

            # 見出しとその内容を抽出
            headings = main_content.find_all(["h2", "h3", "h4"])
            for heading in headings[:20]:  # 最初の20個の見出し
                heading_text = heading.get_text().strip()
                if heading_text:
                    level = int(heading.name[1])
                    formatted_doc.append(f"{'#' * level} {heading_text}")

                    # 見出しの後の要素（段落、リスト、コードブロック）を抽出
                    current = heading
                    content_count = 0
                    max_content = 3  # 各見出しで最大3つの要素まで

                    # 見出しの次の要素から開始
                    while current and content_count < max_content:
                        current = current.find_next_sibling()
                        if not current:
                            break

                        # 次の見出しに到達したら停止
                        if current.name in ["h1", "h2", "h3", "h4"]:
                            break

                        if current.name == "p":
                            p_text = current.get_text().strip()
                            if p_text and len(p_text) > 10:
                                formatted_doc.append(p_text)
                                content_count += 1
                        elif current.name == "div":
                            # Docusaurusのコードブロックを抽出
                            classes = " ".join(current.get("class", []))
                            if "codeBlockContainer" in classes:
                                code_elem = current.find("code")
                                if code_elem:
                                    code = code_elem.get_text().strip()
                                    if code and len(code) < 1000:
                                        # 言語を判定
                                        lang = "json" if "json" in classes else ""
                                        formatted_doc.append(f"```{lang}\n{code}\n```")
                                        content_count += 1
                        elif current.name == "pre":
                            # 通常のコードブロックを抽出
                            code = current.get_text().strip()
                            if code and len(code) < 1000:
                                formatted_doc.append(f"```\n{code}\n```")
                                content_count += 1
                        elif current.name in ["ul", "ol"]:
                            # リスト項目を抽出
                            items = current.find_all("li", recursive=False)
                            for item in items[:5]:
                                item_text = item.get_text().strip()
                                if item_text and len(item_text) < 200:
                                    formatted_doc.append(f"- {item_text}")
                            if items:
                                content_count += 1

                    formatted_doc.append("")

            return "\n".join(formatted_doc)

    except Exception as e:
        logger.error(f"ドキュメント取得エラー: {e}")
        return f"ドキュメントの取得に失敗しました: {e}"


@mcp.tool
async def add_list_item(
    initial_fields: list[dict[str, Any]],
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Add a new item to a Slack list.

    Args:
        initial_fields: List of field dictionaries. Each field needs:
                       - column_id: The column ID
                       - Value in appropriate format (rich_text, user, date, select, checkbox, etc.)
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
                 When DEFAULT_LIST_ID is set, you can omit this parameter entirely
        ctx: FastMCP context (automatically injected)

    Returns:
        The created item or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(
                f"Adding item to list {list_id} with {len(initial_fields)} fields",
            )

        result = await slack_client.add_item(
            list_id=list_id,
            initial_fields=initial_fields,
        )

        if ctx:
            await ctx.info(f"Successfully added item to list {list_id}")

        return {
            "success": True,
            "item": result,
        }

    except Exception as e:
        logger.error(f"Error adding item: {e}")
        if ctx:
            await ctx.error(f"Failed to add item: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def update_list_item(
    cells: list[dict[str, Any]],
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update items in a Slack list.

    Use get_list_structure first to understand the column IDs and types.

    Args:
        cells: List of cell dictionaries. Each cell needs:
               - row_id: The item ID to update
               - column_id: The column ID
               - Value in appropriate format (rich_text, user, date, select, checkbox, etc.)
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
                 When DEFAULT_LIST_ID is set, you can omit this parameter entirely
        ctx: FastMCP context (automatically injected)

    Returns:
        Success status or error information


    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Updating items in list {list_id} with {len(cells)} cells")

        result = await slack_client.update_item(
            list_id=list_id,
            cells=cells,
        )

        if ctx:
            await ctx.info(f"Successfully updated items in list {list_id}")

        return result

    except Exception as e:
        logger.error(f"Error updating items: {e}")
        if ctx:
            await ctx.error(f"Failed to update items: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def delete_list_item(
    item_id: str,
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an item from a Slack list.

    Args:
        item_id: The ID of the item to delete
        list_id: The ID of the list containing the item (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        Deletion confirmation or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Deleting item {item_id} from list {list_id}")

        await slack_client.delete_item(
            list_id=list_id,
            item_id=item_id,
        )

        if ctx:
            await ctx.info(f"Successfully deleted item {item_id}")

        return {
            "success": True,
            "deleted": True,
            "item_id": item_id,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error deleting list item: {e}")
        if ctx:
            await ctx.error(f"Failed to delete item: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_item(
    item_id: str,
    list_id: str | None = None,
    ctx: Context = None,
    include_is_subscribed: bool = False,
) -> dict[str, Any]:
    """Get a specific item from a Slack list.

    Args:
        item_id: The ID of the item to retrieve
        list_id: The ID of the list containing the item (optional, uses DEFAULT_LIST_ID env var if not provided)
        include_is_subscribed: Whether to include subscription status
        ctx: FastMCP context (automatically injected)

    Returns:
        The item data including list metadata and subtasks or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Retrieving item {item_id} from list {list_id}")

        result = await slack_client.get_item(
            list_id=list_id,
            item_id=item_id,
            include_is_subscribed=include_is_subscribed,
        )

        if ctx:
            await ctx.info(f"Successfully retrieved item {item_id}")

        return {
            "success": True,
            "item": result.get("item", {}),
            "list_metadata": result.get("list", {}).get("list_metadata", {}),
            "subtasks": result.get("subtasks", []),
        }

    except Exception as e:
        logger.error(f"Error getting list item: {e}")
        if ctx:
            await ctx.error(f"Failed to get item: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def list_items(
    list_id: str | None = None,
    limit: int | None = 100,
    cursor: str | None = None,
    archived: bool | None = None,
    filters: dict[str, dict[str, Any]] | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all items in a Slack list with optional filtering.

    Args:
        list_id: The ID of the list to retrieve items from (optional, uses DEFAULT_LIST_ID env var if not provided)
        limit: Maximum number of items to return (default: 100)
        cursor: Pagination cursor for next page
        archived: Whether to return archived items (True) or normal items (False/None)
        filters: Column filters. Keys are column IDs or keys, values are filter conditions.
                Supported operators: equals, not_equals, contains, not_contains, in, not_in
        ctx: FastMCP context (automatically injected)

    Returns:
        List of items with pagination info or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            filter_desc = f" with {len(filters)} filters" if filters else ""
            await ctx.info(f"Listing items from list {list_id}{filter_desc}")

        response = await slack_client.list_items(
            list_id=list_id,
            limit=limit or 100,
            cursor=cursor,
            archived=archived,
            filters=filters,
        )

        if ctx:
            await ctx.info(
                f"Retrieved {len(response.get('items', []))} items from list {list_id}",
            )

        return {
            "success": True,
            "items": response.get("items", []),
            "has_more": response.get("has_more", False),
            "next_cursor": response.get("next_cursor"),
            "total": response.get("total"),
        }

    except Exception as e:
        logger.error(f"Error listing items: {e}")
        if ctx:
            await ctx.error(f"Failed to list items: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_info(
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get information about a Slack list.

    Args:
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        The list information or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Retrieving information for list {list_id}")

        result = await slack_client.get_list(list_id=list_id)

        if ctx:
            await ctx.info("Successfully retrieved list information")

        return {
            "success": True,
            "list": result,
        }

    except Exception as e:
        logger.error(f"Error getting list info: {e}")
        if ctx:
            await ctx.error(f"Failed to get list info: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_structure(
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get the structure and column information of a Slack list.

    Args:
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        The list structure including columns and their configurations

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Analyzing structure for list {list_id}")

        # Get list items to find any item ID, then use items.info to get schema
        items_response = await slack_client.list_items(
            list_id=list_id,
            limit=1,  # We just need one item to get the schema
        )

        # If we have any item, use items.info to get the full schema
        if items_response.get("items") and len(items_response["items"]) > 0:
            first_item = items_response["items"][0]
            item_id = first_item.get("id")

            # Get item info which includes list metadata with schema
            item_info_response = await slack_client.get_item(
                list_id=list_id,
                item_id=item_id,
            )

            # Extract schema from list metadata
            list_data = item_info_response.get("list", {})
            list_metadata = list_data.get("list_metadata", {})
            schema = list_metadata.get("schema", [])

            # Build column mapping from schema
            columns = {}
            for column in schema:
                col_id = column.get("id")
                if col_id:
                    columns[col_id] = {
                        "id": col_id,
                        "name": column.get("name"),
                        "key": column.get("key"),
                        "type": column.get("type"),
                        "is_primary": column.get("is_primary_column", False),
                        "options": column.get("options", {}),
                    }

            # Find the name/title column
            name_column = None
            for col_id, col_info in columns.items():
                if col_info.get("is_primary") or col_info.get("key") in [
                    "name",
                    "title",
                    "todo_name",
                ]:
                    name_column = col_id
                    break

            if ctx:
                await ctx.info(f"Found {len(columns)} columns in list schema")

            return {
                "success": True,
                "structure": {
                    "list_id": list_id,
                    "metadata": {
                        "name": list_data.get("name", "Unknown"),
                        "title": list_data.get("title", "Unknown"),
                        "description": list_metadata.get("description", ""),
                    },
                    "schema": schema,
                    "columns": columns,
                    "name_column": name_column,
                    "views": list_metadata.get("views", []),
                    "todo_mode": list_metadata.get("todo_mode", False),
                },
            }
        # No items in the list, try to get basic info
        if ctx:
            await ctx.info("List has no items, returning basic structure")

        return {
            "success": True,
            "structure": {
                "list_id": list_id,
                "message": "List is empty. Add items to see full structure.",
                "columns": {},
            },
        }

    except Exception as e:
        logger.error(f"Error getting list structure: {e}")
        if ctx:
            await ctx.error(f"Failed to get list structure: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


# Add a resource to show server information
@mcp.resource("resource://server/info")
def get_server_info() -> dict[str, Any]:
    """Provide server configuration and status information."""
    return {
        "name": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "debug_mode": settings.debug_mode,
        "log_level": settings.log_level,
        "slack_api_timeout": settings.slack_api_timeout,
        "slack_retry_count": settings.slack_retry_count,
        "status": "running",
        "tools": [
            "add_list_item",
            "update_list_item",
            "delete_list_item",
            "get_list_item",
            "list_items",
            "get_list_info",
            "get_list_structure",
        ],
    }


# Add a prompt template for Slack API documentation
@mcp.prompt("slack-api-documentation")
async def slack_api_documentation() -> str:
    """Provide formatted Slack API documentation for system prompt usage."""
    # 動的にドキュメントを取得
    dynamic_doc = await fetch_and_format_slack_documentation()

    return f"""{dynamic_doc}

---

## 重要な注意事項

1. **リスト構造の理解**: アイテムを追加または更新する前に、`get_list_structure`を使用してリストの列構造を理解してください。

2. **DEFAULT_LIST_IDの活用**: 環境変数`DEFAULT_LIST_ID`が設定されている場合、すべてのツール呼び出しで`list_id`パラメータを省略できます。

## フィルター演算子

リストアイテムを検索する際に使用できる演算子：

- `equals`: 完全一致
- `not_equals`: 値が等しくない
- `contains`: 部分文字列を含む（大文字小文字を区別しない）
- `not_contains`: 部分文字列を含まない
- `in`: 指定されたリストに値が含まれる
- `not_in`: 指定されたリストに値が含まれない
"""
