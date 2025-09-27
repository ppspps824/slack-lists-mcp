# Slack Lists MCP Server

An MCP (Model Context Protocol) server for managing Slack Lists. This server provides tools to create, read, update, and delete items in Slack Lists, with advanced filtering capabilities.

## Features

- ✨ Full CRUD operations for Slack List items
- 🔍 Advanced filtering with multiple operators
- 📑 Pagination support for large lists
- 🏗️ Dynamic column structure discovery
- 🎯 Type-safe operations with validation
- 🚀 Async/await support for better performance

## Installation

### Configure in Claude Desktop

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "slack-lists": {
      "command": "uvx",
      "args": ["slack-lists-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token"
      }
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | ✅ | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | ❌ | INFO |
| `SLACK_API_TIMEOUT` | Timeout for Slack API calls (seconds) | ❌ | 30 |
| `SLACK_RETRY_COUNT` | Number of retries for failed API calls | ❌ | 3 |
| `DEBUG_MODE` | Enable debug mode | ❌ | false |

### Setting up Slack Bot

1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Add the following OAuth scopes to your Bot Token:
   - `lists:read` - Read list items
   - `lists:write` - Create and update list items
3. Install the app to your workspace
4. Copy the Bot User OAuth Token (starts with `xoxb-`)

## Available Tools

### 1. `get_list_structure`
Get the column structure of a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list

**Returns:** Column definitions including IDs, names, types, and options

### 2. `add_list_item`
Add a new item to a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list
- `initial_fields` (required): Array of field objects with column_id and value

**Example:**
```json
{
  "list_id": "F1234567890",
  "initial_fields": [
    {
      "column_id": "Col123",
      "rich_text": [{
        "type": "rich_text",
        "elements": [{
          "type": "rich_text_section",
          "elements": [{"type": "text", "text": "Task Name"}]
        }]
      }]
    }
  ]
}
```

### 3. `update_list_item`
Update existing items in a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list
- `cells` (required): Array of cell objects with row_id, column_id, and value

**Example:**
```json
{
  "list_id": "F1234567890",
  "cells": [
    {
      "row_id": "Rec123",
      "column_id": "Col456",
      "checkbox": true
    }
  ]
}
```

### 4. `delete_list_item`
Delete an item from a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list
- `item_id` (required): The ID of the item to delete

### 5. `get_list_item`
Get a specific item from a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list
- `item_id` (required): The ID of the item
- `include_is_subscribed` (optional): Include subscription status

### 6. `list_items`
List all items in a Slack List with optional filtering.

**Parameters:**
- `list_id` (required): The ID of the list
- `limit` (optional): Maximum number of items (default: 100)
- `cursor` (optional): Pagination cursor
- `archived` (optional): Filter for archived items
- `filters` (optional): Column-based filters

**Filter Operators:**
- `equals`: Exact match
- `not_equals`: Not equal to value
- `contains`: Contains substring (case-insensitive)
- `not_contains`: Does not contain substring
- `in`: Value is in the provided list
- `not_in`: Value is not in the provided list

**Example with filters:**
```json
{
  "list_id": "F1234567890",
  "filters": {
    "name": {"contains": "Task"},
    "todo_completed": {"equals": false},
    "todo_assignee": {"in": ["U123", "U456"]}
  }
}
```

### 7. `get_list_info`
Get metadata about a Slack List.

**Parameters:**
- `list_id` (required): The ID of the list


## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ppspps824/slack-lists-mcp.git
cd slack-lists-mcp

# Install dependencies
uv sync
```

### Running in Development Mode

```bash
# Run with FastMCP dev mode (with auto-reload)
fastmcp dev slack_lists_mcp.server:mcp

# Or run directly
uv run slack-lists-mcp
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=slack_lists_mcp

# Run specific test file
uv run pytest tests/test_server.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- [GitHub Issues](https://github.com/yourusername/slack-lists-mcp/issues)
- [Slack API Documentation](https://api.slack.com/methods#lists)
- [MCP Documentation](https://modelcontextprotocol.io)
