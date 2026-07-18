"""Server-side style allowlist enforcement for expert tools.

The gateway is used for local adapters and mirrors the same identity/profile
boundary expected from the external MCP server. Prompt text is never treated
as authorization.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from app.agents.contracts import AgentManifest
from app.agents.manifests import TOOL_POLICY_VERSION


class ToolPermissionError(PermissionError):
    pass


class ToolNotRegisteredError(LookupError):
    pass


@dataclass
class ToolCallTrace:
    called: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)


class AgentToolGateway:
    def __init__(self, manifest: AgentManifest, tools: Dict[str, Callable[..., Any]]) -> None:
        self.manifest = manifest
        self._tools = dict(tools)
        self.policy_version = TOOL_POLICY_VERSION
        self.trace = ToolCallTrace()

    def reset_trace(self) -> None:
        self.trace = ToolCallTrace()

    async def call(self, tool_name: str, /, **kwargs: Any) -> Any:
        if tool_name not in self.manifest.allowed_tools:
            self.trace.denied.append(tool_name)
            raise ToolPermissionError(
                f"{self.manifest.agent_type.value} is not authorized for tool {tool_name!r}"
            )
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotRegisteredError(f"authorized tool {tool_name!r} has no runtime adapter")
        if len(self.trace.called) >= self.manifest.max_tool_calls:
            raise ToolPermissionError(
                f"{self.manifest.agent_type.value} exceeded max_tool_calls={self.manifest.max_tool_calls}"
            )
        self.trace.called.append(tool_name)
        result = tool(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

