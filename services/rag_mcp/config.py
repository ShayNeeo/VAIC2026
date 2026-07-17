"""Environment-only configuration for the independent RAG MCP service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SERVICE_TOKEN = os.getenv("RAG_MCP_SERVICE_TOKEN", "local-rag-mcp-change-me")


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RagMCPSettings:
    host: str = os.getenv("RAG_MCP_HOST", "127.0.0.1")
    port: int = int(os.getenv("RAG_MCP_PORT", "8100"))
    url: str = os.getenv("RAG_MCP_URL", "http://127.0.0.1:8100/mcp")
    db_path: Path = Path(os.getenv("RAG_MCP_DB_PATH", str(ROOT / "data" / "rag_mcp" / "rag.sqlite3")))
    service_token: str = _DEFAULT_SERVICE_TOKEN
    product_token: str = os.getenv("RAG_MCP_PRODUCT_TOKEN", f"{_DEFAULT_SERVICE_TOKEN}-product")
    legal_token: str = os.getenv("RAG_MCP_LEGAL_TOKEN", f"{_DEFAULT_SERVICE_TOKEN}-legal")
    operations_token: str = os.getenv("RAG_MCP_OPERATIONS_TOKEN", f"{_DEFAULT_SERVICE_TOKEN}-operations")
    evidence_token: str = os.getenv("RAG_MCP_EVIDENCE_TOKEN", f"{_DEFAULT_SERVICE_TOKEN}-evidence")
    require_auth: bool = _bool("RAG_MCP_REQUIRE_AUTH", True)
    # Default is "gemini": embedding via Google AI Studio (GOOGLE_API_KEY, the
    # AI Studio key) using gemini-embedding-2, cached locally for offline reuse.
    # Set RAG_MCP_EMBEDDING_PROVIDER=local for a key-free deterministic run, or
    # "openai" to use an OpenAI embedding model as fallback.
    embedding_provider: str = os.getenv("RAG_MCP_EMBEDDING_PROVIDER", "gemini")
    top_k: int = int(os.getenv("RAG_MCP_TOP_K", "5"))
    # 0.35 is empirically chosen for OpenAI text-embedding-3-small to filter out noise.
    threshold: float = float(os.getenv("RAG_MCP_THRESHOLD", "0.35"))
    max_context_chars: int = int(os.getenv("RAG_MCP_MAX_CONTEXT_CHARS", "8000"))
    auto_seed: bool = _bool("RAG_MCP_AUTO_SEED", True)

    def profile_url(self, profile: str) -> str:
        base = self.url[: -len("/mcp")] if self.url.endswith("/mcp") else self.url.rstrip("/")
        suffix = {
            "admin": "/mcp",
            "product": "/mcp/product",
            "legal": "/mcp/legal",
            "operations": "/mcp/operations",
            "evidence": "/mcp/evidence",
        }.get(profile)
        if suffix is None:
            raise ValueError(f"unsupported MCP profile: {profile}")
        return f"{base}{suffix}"

    def profile_token(self, profile: str) -> str:
        tokens: Dict[str, str] = {
            "admin": self.service_token,
            "product": self.product_token,
            "legal": self.legal_token,
            "operations": self.operations_token,
            "evidence": self.evidence_token,
        }
        if profile not in tokens:
            raise ValueError(f"unsupported MCP profile: {profile}")
        return tokens[profile]

    def validate_runtime(self) -> None:
        if self.require_auth:
            for profile in ("admin", "product", "legal", "operations", "evidence"):
                if len(self.profile_token(profile)) < 16:
                    raise ValueError(f"RAG MCP {profile} token must contain at least 16 characters")
        if not 1 <= self.top_k <= 20:
            raise ValueError("RAG_MCP_TOP_K must be between 1 and 20")
        if not 0 <= self.threshold <= 1:
            raise ValueError("RAG_MCP_THRESHOLD must be between 0 and 1")


settings = RagMCPSettings()
