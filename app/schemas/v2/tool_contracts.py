"""Pydantic mirror of plan_v2/contracts/tool_contracts.json.

Unlike the other three contracts, tool_contracts.json is not itself a JSON
Schema instance document -- it is a registry of tool definitions whose
individual input_schema/output_schema entries are JSON Schema fragments.
`load_tool_registry()` is the one place allowed to read that file
(plan_v2/INDEX.md section 3: "Tool input/output va quyen goi" -> this file).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .json_schema_loader import load_tool_contracts


class ToolRisk(str, Enum):
    READ_LOW = "read_low"
    READ_SENSITIVE = "read_sensitive"
    WRITE_HIGH = "write_high"
    EXTERNAL_COMMUNICATION = "external_communication"


class ActionInput(BaseModel):
    """$defs/actionInput -- every external-action tool call must carry this shape.

    plan_v2/00_AI_BUILD_PROTOCOL.md: "Moi write action can idempotency key";
    plan_v2/INDEX.md section 7: "Moi external action phai qua Approval Service
    va idempotency gate".
    """

    model_config = ConfigDict(extra="forbid")

    payload: Dict[str, Any]
    approval_token: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class ActionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    status: str = Field(pattern=r"^(accepted|completed|failed|unknown)$")


class ToolSpec(BaseModel):
    """One entry of tool_contracts.json#/tools."""

    model_config = ConfigDict(extra="allow")  # input/output_schema are raw JSON Schema fragments

    name: str
    allowed_callers: List[str]
    risk: ToolRisk
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout_ms: int = Field(gt=0)
    max_retries: int = Field(ge=0)
    approval_required: bool


class ToolRegistry(BaseModel):
    """Parsed tool_contracts.json, keyed for the "allowed caller" check that
    plan_v2/INDEX.md section 7 requires before any tool call ("Moi tool call
    phai qua Tool Registry")."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(pattern=r"^2\.0\.0$")
    tools: List[ToolSpec]

    def get(self, name: str) -> ToolSpec:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise KeyError(f"Unknown tool: {name}")

    def is_caller_allowed(self, tool_name: str, caller: str) -> bool:
        return caller in self.get(tool_name).allowed_callers


_cached_registry: Optional[ToolRegistry] = None


def load_tool_registry() -> ToolRegistry:
    global _cached_registry
    if _cached_registry is None:
        raw = load_tool_contracts()
        _cached_registry = ToolRegistry.model_validate(
            {"schema_version": raw["schema_version"], "tools": raw["tools"]}
        )
    return _cached_registry
