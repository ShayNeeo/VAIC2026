"""mcp_common - Shared schemas, config, and LLM client for all MCP servers."""

from mcp_common.config import Settings, get_settings, settings
from mcp_common.llm_client import GemmaClient, get_gemma_client, LLMClientError
from mcp_common.schemas import (
    SharedCaseState,
    EvidenceItem,
    TaskItem,
    OperationsResult,
    ApprovalToken,
    CreateCaseRequest,
    ResumeCaseRequest,
    ApproveCaseRequest,
    RejectCaseRequest,
)

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "GemmaClient",
    "get_gemma_client",
    "LLMClientError",
    "SharedCaseState",
    "EvidenceItem",
    "TaskItem",
    "OperationsResult",
    "ApprovalToken",
    "CreateCaseRequest",
    "ResumeCaseRequest",
    "ApproveCaseRequest",
    "RejectCaseRequest",
]