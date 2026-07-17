"""Central allowlist for agent tool permissions."""

from __future__ import annotations

from typing import Any, Callable, Dict


class ToolPermissionError(PermissionError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._allowlist: Dict[str, set[str]] = {}

    def register(self, name: str, function: Callable[..., Any], *owners: str) -> None:
        self._tools[name] = function
        self._allowlist[name] = set(owners)

    def call(self, owner: str, name: str, **kwargs: Any) -> Any:
        if name not in self._tools or owner not in self._allowlist.get(name, set()):
            raise ToolPermissionError(f"{owner} không được phép gọi tool {name}")
        return self._tools[name](**kwargs)

