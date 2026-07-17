"""Re-export of the canonical Product Matcher (single source of truth).

The real implementation lives in ``servers.v3_product_agent.product.matcher``.
This shim keeps legacy import paths working without forking logic.
"""

from servers.v3_product_agent.product.matcher import (  # noqa: F401
    ProductMatcher,
)

__all__ = ["ProductMatcher"]
