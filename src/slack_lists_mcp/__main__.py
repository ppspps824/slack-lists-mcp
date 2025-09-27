"""Entry point for the Slack Lists MCP server."""

import logging
import sys

from .config import get_settings
from .server import mcp


def main():
    """Main entry point for the Slack Lists MCP server."""
    try:
        # Get settings to validate environment variables
        settings = get_settings()

        # Log startup information
        logging.info(
            f"Starting {settings.mcp_server_name} v{settings.mcp_server_version}",
        )

        # Run the MCP server with stdio transport
        mcp.run()
    except Exception as e:
        logging.exception(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
