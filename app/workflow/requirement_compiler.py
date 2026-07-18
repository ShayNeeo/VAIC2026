"""Requirement Compiler for generating the dynamic Case Checklist.

Implements Phase 3 of the SHB Corporate Sales Copilot End-to-End Workflow.
Takes the outputs of Product, Legal/Eligibility, and Operations agents and
deduplicates/compiles them into a single, comprehensive Case Checklist.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.v2.metadata import MetadataObject, MetadataType, MetadataVersion


class RequirementStatus(str, Enum):
    MISSING = "MISSING"
    RECEIVED_UNVERIFIED = "RECEIVED_UNVERIFIED"
    SATISFIED_VERIFIED = "SATISFIED_VERIFIED"
    EXPIRED = "EXPIRED"
    INCONSISTENT = "INCONSISTENT"


@dataclass
class ChecklistItem:
    item_id: str
    code: str
    description: str
    source_agent: str
    status: RequirementStatus
    evidence_refs: List[str] = field(default_factory=list)
    reason_code: Optional[str] = None


@dataclass
class CaseChecklist:
    checklist_id: str
    case_id: str
    items: List[ChecklistItem]
    created_at: datetime
    version: int


class RequirementCompiler:
    def compile(self, case_id: str, product_output: Dict[str, Any], eligibility_output: Dict[str, Any], ops_output: Dict[str, Any], existing_inventory: List[Dict[str, Any]]) -> CaseChecklist:
        """Compiles requirements from all agent outputs into a deduplicated checklist."""
        
        items_map: Dict[str, ChecklistItem] = {}
        
        # Helper to process requirements from an agent
        def process_requirements(agent_name: str, output: Dict[str, Any]):
            if not output:
                return
            reqs = output.get("requirements", [])
            for req in reqs:
                code = req.get("code")
                if not code:
                    continue
                
                # Deduplication logic (if already requested by another agent)
                if code not in items_map:
                    items_map[code] = ChecklistItem(
                        item_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
                        code=code,
                        description=req.get("description", code),
                        source_agent=agent_name,
                        status=RequirementStatus.MISSING
                    )
        
        # Extract requirements from standard agent outputs
        process_requirements("Product", product_output)
        process_requirements("Legal", eligibility_output)
        process_requirements("Operations", ops_output)
        
        # Check against existing inventory
        inventory_codes = {inv.get("code") for inv in existing_inventory if inv.get("is_valid")}
        
        for code, item in items_map.items():
            if code in inventory_codes:
                item.status = RequirementStatus.SATISFIED_VERIFIED
                item.evidence_refs = [inv.get("evidence_id") for inv in existing_inventory if inv.get("code") == code]

        return CaseChecklist(
            checklist_id=f"CHK-{uuid.uuid4().hex[:12].upper()}",
            case_id=case_id,
            items=list(items_map.values()),
            created_at=datetime.utcnow(),
            version=1
        )
