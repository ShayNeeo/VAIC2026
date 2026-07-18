"""Customer Resolver and Evidence Inventory loader.

Implements Phase 2 of the SHB Corporate Sales Copilot End-to-End Workflow.
Identifies customer status (new/existing) and loads their prior verified evidence
to prevent redundant requests for already-collected documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.v2.metadata import AccessControl, MetadataObject, MetadataVersion
from app.storage.repository import V2Repository


class ResolutionStatus(str, Enum):
    EXISTING_CONFIRMED = "EXISTING_CONFIRMED"
    EXISTING_POSSIBLE_MATCH = "EXISTING_POSSIBLE_MATCH"
    NEW_CUSTOMER = "NEW_CUSTOMER"
    ACCESS_DENIED = "ACCESS_DENIED"
    DUPLICATE_SUSPECTED = "DUPLICATE_SUSPECTED"


@dataclass
class ResolutionResult:
    status: ResolutionStatus
    customer_id: Optional[str]
    customer_metadata: Optional[MetadataObject]
    customer_version: Optional[MetadataVersion]
    evidence_inventory: List[Dict[str, Any]]
    confidence: float
    message: str


class CustomerResolver:
    def __init__(self, repository: V2Repository) -> None:
        self.repository = repository

    def resolve_customer(self, customer_id: Optional[str], provided_info: Dict[str, Any], employee_id: str) -> ResolutionResult:
        """Determines customer status and loads any existing profile/evidence."""
        if customer_id:
            return self._fetch_existing_customer(customer_id, employee_id)
        
        # Simple heuristic for MVP: if name has SHB, it's a possible match
        name = provided_info.get("customer_name", "").upper()
        tax_id = provided_info.get("tax_id")
        
        if tax_id and tax_id.startswith("SHB-"):
            # Mocking existing match
            return self._fetch_existing_customer(f"COMP-{tax_id[-4:]}", employee_id)
            
        return ResolutionResult(
            status=ResolutionStatus.NEW_CUSTOMER,
            customer_id=None,
            customer_metadata=None,
            customer_version=None,
            evidence_inventory=[],
            confidence=1.0,
            message="No existing customer ID provided and no strong signals matched."
        )

    def _fetch_existing_customer(self, customer_id: str, employee_id: str) -> ResolutionResult:
        # In a real system, we'd check employee_id against access_control
        
        # We query the metadata repository for the customer profile
        # For MVP, we'll try to find a metadata object where ID == customer_id (or lookup index)
        # Assuming object_id == customer_id for simplicity in this pilot
        
        obj = self.repository.get_metadata_object(customer_id)
        if obj:
            # Check access
            if employee_id not in obj.access_control.allowed_roles and "RM" not in obj.access_control.allowed_roles:
                return ResolutionResult(
                    status=ResolutionStatus.ACCESS_DENIED,
                    customer_id=customer_id,
                    customer_metadata=None,
                    customer_version=None,
                    evidence_inventory=[],
                    confidence=1.0,
                    message="Employee lacks permission to view this customer's data."
                )

            version = self.repository.get_metadata_version(obj.current_version_id)
            
            # Fetch evidence inventory
            # (In MVP, we would query metadata_relations for EXTRACTED_FROM or similar, 
            # but for now we'll just mock an empty inventory if none exist)
            inventory = self._fetch_evidence_inventory(customer_id)
            
            return ResolutionResult(
                status=ResolutionStatus.EXISTING_CONFIRMED,
                customer_id=customer_id,
                customer_metadata=obj,
                customer_version=version,
                evidence_inventory=inventory,
                confidence=1.0,
                message="Successfully resolved existing customer."
            )
            
        return ResolutionResult(
            status=ResolutionStatus.NEW_CUSTOMER,
            customer_id=customer_id,
            customer_metadata=None,
            customer_version=None,
            evidence_inventory=[],
            confidence=1.0,
            message=f"Customer ID {customer_id} provided but not found. Treating as new."
        )

    def _fetch_evidence_inventory(self, customer_id: str) -> List[Dict[str, Any]]:
        """Mock method for retrieving previously verified documents/facts."""
        return []
