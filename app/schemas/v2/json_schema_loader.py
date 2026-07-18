"""Loads the V2 JSON Schema contracts from plan_v2/contracts and validates instances.

plan_v2/contracts/*.json is the source of truth per plan_v2/03_SHARED_CONTRACTS.md
("JSON schemas ... la source of truth. Module plan chi giai thich cach dung.").
This module reads those files directly instead of duplicating them under app/, so
the schema used at runtime/tests can never drift from the authored contract.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

__all__ = [
    "ValidationError",
    "contracts_dir",
    "load_schema",
    "load_tool_contracts",
    "validate_instance",
    "action_input_schema",
    "action_output_schema",
]


def _find_contracts_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "plan_v2" / "contracts"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("plan_v2/contracts not found above app/schemas/v2/json_schema_loader.py")


@lru_cache(maxsize=1)
def contracts_dir() -> Path:
    return _find_contracts_dir()


def _without_id(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Drop "$id" so relative "$ref" resolution never anchors on it.

    Every contract file declares an absolute "$id" for documentation/versioning,
    but the "$ref" values used between files (e.g. "intent_result.schema.json")
    are plain sibling filenames. Keeping "$id" would make jsonschema resolve
    those relative refs against the id's URI instead of the registry's
    filename keys, so both the registry entries and the root schema handed to
    the validator are stripped of "$id" and looked up purely by filename.
    """
    return {key: value for key, value in schema.items() if key != "$id"}


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resources: list[tuple[str, Resource]] = []
    for path in contracts_dir().glob("*.schema.json"):
        schema = _without_id(json.loads(path.read_text(encoding="utf-8")))
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        # Sibling-relative "$ref": "foo.schema.json" values resolve against this
        # bare-filename key because the resource itself carries no "$id".
        resources.append((path.name, resource))
    return Registry().with_resources(resources)


@lru_cache(maxsize=None)
def load_schema(filename: str) -> Mapping[str, Any]:
    """Load one *.schema.json file from plan_v2/contracts by filename."""
    path = contracts_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(f"Unknown contract schema: {filename}")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_tool_contracts() -> Mapping[str, Any]:
    """tool_contracts.json is a tool registry document, not itself an instance schema."""
    path = contracts_dir() / "tool_contracts.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_instance(instance: Any, filename: str) -> None:
    """Validate instance against plan_v2/contracts/<filename>, resolving cross-file $ref.

    Raises jsonschema.exceptions.ValidationError on the first violation.
    """
    schema = _without_id(load_schema(filename))
    validator = Draft202012Validator(schema, registry=_registry(), format_checker=FormatChecker())
    validator.validate(instance)


def action_input_schema() -> Mapping[str, Any]:
    """tool_contracts.json#/$defs/actionInput as a standalone validatable schema."""
    tool_contracts = load_tool_contracts()
    return {"$defs": tool_contracts["$defs"], "$ref": "#/$defs/actionInput"}


def action_output_schema() -> Mapping[str, Any]:
    tool_contracts = load_tool_contracts()
    return {"$defs": tool_contracts["$defs"], "$ref": "#/$defs/actionOutput"}
