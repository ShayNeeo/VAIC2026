"""Scope RAG MCP service/transport tests to the deterministic ``local``
embedding provider.

These tests assert ACL/transport/exact-match behaviour, not semantic recall,
so they must not depend on a remote embedding model (gemini/openai) or an API
key. The key-free ``local`` provider keeps them offline and reproducible.
"""

import os

# Force the key-free "local" provider for these ACL/transport tests so they
# stay offline and provider-independent (they assert access-control and wire
# behaviour, not semantic recall). This intentionally overrides any gemini/
# openai provider set by the outer CI environment.
os.environ["RAG_MCP_EMBEDDING_PROVIDER"] = "local"
os.environ["KNOWLEDGE_EMBEDDING_PROVIDER"] = "local"
