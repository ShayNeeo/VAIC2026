"""Re-export of the canonical Product Retriever (single source of truth).

The real implementation lives in ``servers.v3_product_agent.rag.retriever``.
This shim keeps legacy import paths working without forking logic.
"""

from servers.v3_product_agent.rag.retriever import (  # noqa: F401
    ProductRetriever,
    ProductRetrievalResult,
)

__all__ = ["ProductRetriever", "ProductRetrievalResult"]
