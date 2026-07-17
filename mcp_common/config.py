"""MCP Common configuration from environment - V3 aligned."""

import os
from pydantic import BaseModel
from functools import lru_cache


class Settings(BaseModel):
    # LLM (Google AI Studio / Gemini)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemma-4-31b-it")
    GOOGLE_ENDPOINT: str = os.getenv("GOOGLE_ENDPOINT", "https://generativelanguage.googleapis.com")
    # Full generateContent URL: {GOOGLE_ENDPOINT}/v1beta/models/{GOOGLE_MODEL}:generateContent?key={GOOGLE_API_KEY}

    # VPS / SSH
    VPS_HOST: str = os.getenv("VPS_HOST", "sgp1.w9.nu")
    VPS_PORT: int = int(os.getenv("VPS_PORT", "2204"))
    VPS_USER: str = os.getenv("VPS_USER", "root")
    VPS_SSH_PORT: int = int(os.getenv("VPS_SSH_PORT", "2204"))
    VPS_IPV6: str = os.getenv("VPS_IPV6", "")

    # MCP Server ports (one per agent)
    PRODUCT_AGENT_PORT: int = int(os.getenv("PRODUCT_AGENT_PORT", "8004"))
    LEGAL_AGENT_PORT: int = int(os.getenv("LEGAL_AGENT_PORT", "8005"))
    OPERATIONS_AGENT_PORT: int = int(os.getenv("OPERATIONS_AGENT_PORT", "8006"))
    APPROVAL_AGENT_PORT: int = int(os.getenv("APPROVAL_AGENT_PORT", "8007"))
    ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "8000"))

    # Network binding (IPv6 dual-stack)
    BIND_HOST: str = os.getenv("BIND_HOST", "::")

    # App (FastAPI orchestrator)
    APPROVAL_SECRET: str = os.getenv("APPROVAL_SECRET", "demo-only-change-me")
    APPROVAL_TOKEN_TTL_SECONDS: int = int(os.getenv("APPROVAL_TOKEN_TTL_SECONDS", "300"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # RAG
    RAG_DENSE_WEIGHT: float = float(os.getenv("RAG_DENSE_WEIGHT", "0.6"))
    RAG_SPARSE_WEIGHT: float = float(os.getenv("RAG_SPARSE_WEIGHT", "0.4"))
    RAG_THRESHOLD: float = float(os.getenv("RAG_THRESHOLD", "0.35"))
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # LLM Client
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "5.0"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "1"))
    LLM_MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "256"))

    # Embedding (phase 2: sentence-transformers e5)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "128"))
    USE_REAL_EMBEDDING: bool = os.getenv("USE_REAL_EMBEDDING", "false").lower() == "true"

    # Feature flags (default false for offline/safe mode)
    USE_GEMMA_FOR_GUARDRAILS: bool = os.getenv("USE_GEMMA_FOR_GUARDRAILS", "false").lower() == "true"
    USE_GEMMA_FOR_VERIFY: bool = os.getenv("USE_GEMMA_FOR_VERIFY", "false").lower() == "true"
    USE_GEMMA_FOR_REASON: bool = os.getenv("USE_GEMMA_FOR_REASON", "false").lower() == "true"
    USE_GEMMA_FOR_INJECTION: bool = os.getenv("USE_GEMMA_FOR_INJECTION", "false").lower() == "true"
    EVIDENCE_SEMANTIC_THRESHOLD: float = float(os.getenv("EVIDENCE_SEMANTIC_THRESHOLD", "0.6"))

    # V3 Confidence Policy (§6.3)
    CONFIDENCE_AUTHENTICATED: float = 1.00
    CONFIDENCE_WORKSPACE: float = 1.00
    CONFIDENCE_FRESH_CRM: float = 0.98
    CONFIDENCE_USER_EXPLICIT: float = 0.95
    CONFIDENCE_WORKFLOW_STATE: float = 0.95
    CONFIDENCE_LLM_INFERENCE: float = 0.70
    CONFIDENCE_AUTO_CONTINUE: float = 0.90
    CONFIDENCE_SHOW_PREVIEW: float = 0.70
    CONFIDENCE_ASK_CLARIFY: float = 0.70

    # V3 Evidence thresholds
    EVIDENCE_EXACT_MATCH_REQUIRED: bool = True
    EVIDENCE_SEMANTIC_THRESHOLD: float = 0.60

    # V3 Data tier defaults (§9.2)
    DEFAULT_DATA_TIER: str = "A"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()