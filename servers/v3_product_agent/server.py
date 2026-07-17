"""V3 Product Agent MCP Server entrypoint.

Single implementation lives in ``servers.product_agent.server``. This module
re-exports it so legacy import paths (deploy doc, v3 tests) keep working
without forking the server logic.
"""

from servers.product_agent.server import (  # noqa: F401
    mcp,
    product_analyze,
    product_search,
    health_check,
    ProductAnalyzeRequest,
    ProductSearchRequest,
)

__all__ = [
    "mcp",
    "product_analyze",
    "product_search",
    "health_check",
    "ProductAnalyzeRequest",
    "ProductSearchRequest",
]
