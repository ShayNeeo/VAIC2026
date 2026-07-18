"""Persistent, fail-closed case document intake and profile confirmation workflow."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.config import settings
from app.intake.extractor import classify_document, detect_needs, extract_document_fields
from app.knowledge.ocr import OcrUnavailableError
from app.knowledge.parsers import UnsupportedDocumentError, extraction_quality, ocr_pdf_sections, parse_document_bytes
from app.safety.input_guardrails_v2 import screen_input
from app.schemas.v2.intake import (
    CustomerBusinessSnapshot,
    DocumentJobStatus,
    ExtractedField,
    FieldConflict,
    FieldValidationStatus,
    IntakeDocument,
    IntakeSession,
    IntakeStatus,
    ProfileChange,
)
from app.storage.repository import StateConflictError, StoredIntake, V2Repository


class IntakeValidationError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class IntakeService:
    def __init__(self, repository: V2Repository) -> None:
        self.repository = repository

    def create(
        self,
        *,
        employee_id: str,
        session_id: str,
        customer_id: Optional[str],
        manual_input: Dict[str, Any],
        crm_attributes: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None,
    ) -> StoredIntake:
        from app.context.customer_resolver import CustomerResolver, ResolutionStatus

        resolver = CustomerResolver(self.repository)
        resolution = resolver.resolve_customer(customer_id, manual_input, employee_id)
        
        if resolution.status == ResolutionStatus.ACCESS_DENIED:
            raise IntakeValidationError("ACCESS_DENIED", resolution.message, status_code=403)

        resolved_customer_id = resolution.customer_id
        
        now = _now()
        case_id = case_id or f"CASE-{uuid.uuid4().hex[:12].upper()}"
        session = IntakeSession(
            intake_id=f"INTAKE-{uuid.uuid4().hex[:12].upper()}",
            case_id=case_id,
            employee_id=employee_id,
            session_id=session_id,
            customer_id=resolved_customer_id,
            status=IntakeStatus.DRAFT,
            version=1,
            manual_input=manual_input,
            extracted_fields=self._initial_fields(manual_input, crm_attributes or {}),
            audit_events=[
                _event(employee_id, "sales_case_draft_created", {"case_id": case_id}),
                _event(employee_id, "customer_resolved", {"status": resolution.status.value, "customer_id": resolved_customer_id})
            ],
            created_at=now,
            updated_at=now,
        )
        session.profile = self._build_profile(session)
        
        # If we have existing inventory, we could attach it to session or handle it later
        
        return self.repository.create_intake(session)

    def add_document(
        self,
        stored: StoredIntake,
        *,
        filename: str,
        mime_type: str,
        data: bytes,
    ) -> tuple[StoredIntake, IntakeDocument, bool]:
        session = stored.session
        if session.status == IntakeStatus.CANCELLED:
            raise IntakeValidationError("INVALID_INTAKE_STATE", "Phiên intake đã bị hủy", status_code=409)
        safe_name = Path(filename or "upload").name
        if len(data) > settings.MAX_UPLOAD_BYTES:
            raise IntakeValidationError("FILE_TOO_LARGE", "Tệp vượt quá giới hạn cho phép", status_code=413)
        if not data:
            raise IntakeValidationError("EMPTY_FILE", "Tệp không có nội dung")
        suffix = Path(safe_name).suffix.lower()
        if suffix not in {".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv", ".json"}:
            raise IntakeValidationError("UNSUPPORTED_FILE", f"Chưa hỗ trợ định dạng {suffix or 'không xác định'}")
        if suffix == ".pdf" and not data.startswith(b"%PDF"):
            raise IntakeValidationError("MIME_MISMATCH", "Nội dung tệp không khớp định dạng PDF")
        if suffix in {".docx", ".xlsx"} and not data.startswith(b"PK"):
            raise IntakeValidationError("MIME_MISMATCH", "Nội dung tệp Office không hợp lệ")
        digest = hashlib.sha256(data).hexdigest()
        existing = self.repository.find_intake_document_by_hash(session.intake_id, digest)
        if existing is not None:
            return stored, existing, True
        try:
            sections = parse_document_bytes(safe_name, data)
        except (UnsupportedDocumentError, UnicodeDecodeError, ValueError, OSError) as exc:
            raise IntakeValidationError("DOCUMENT_PARSE_FAILED", f"Không đọc được tệp: {type(exc).__name__}") from exc
        from app.intake.document_assurance import DocumentAssuranceService, AssessmentStatus
        
        assurance_service = DocumentAssuranceService()
        assessment = assurance_service.evaluate(f"DOC-{uuid.uuid4().hex[:12].upper()}", data, "general_document")

        if assessment.status != AssessmentStatus.PASS:
            status = DocumentJobStatus.QUARANTINED
            error_code = assessment.status.value
            quality = {"publishable": False, "reason": assessment.reason}
        else:
            quality = extraction_quality(sections)
            # OCR fallback: pypdf's text-layer extraction found nothing
            # usable (a scanned/image PDF). Try local Tesseract OCR before
            # giving up to NEEDS_OCR -- but only accept the OCR result if
            # its own extraction_quality AND mean confidence clear the
            # configured floor; otherwise fall through to the exact same
            # NEEDS_OCR/OCR_REQUIRED path as before OCR existed. Never
            # silently accepts low-confidence OCR noise as real text.
            if not quality.get("publishable") and suffix == ".pdf" and settings.OCR_ENABLED:
                try:
                    ocr_sections = ocr_pdf_sections(data)
                except OcrUnavailableError:
                    ocr_sections = []
                if ocr_sections:
                    ocr_quality = extraction_quality(ocr_sections)
                    confidences = [s.metadata.get("ocr_confidence", 0.0) for s in ocr_sections]
                    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    if ocr_quality.get("publishable") and mean_confidence >= settings.OCR_MIN_CONFIDENCE:
                        sections = ocr_sections
                        quality = {**ocr_quality, "ocr_used": True, "ocr_mean_confidence": round(mean_confidence, 4)}
                    else:
                        quality = {
                            **quality, "ocr_attempted": True, "ocr_mean_confidence": round(mean_confidence, 4),
                        }
            combined = "\n".join(item.text for item in sections)
            screened = screen_input(combined)
            status = DocumentJobStatus.UPLOADED
            error_code = None
            if not screened.safe:
                status = DocumentJobStatus.QUARANTINED
                error_code = "PROMPT_INJECTION_SUSPECTED"
            elif not quality.get("publishable"):
                status = DocumentJobStatus.NEEDS_OCR
                error_code = "OCR_REQUIRED"

        now = _now()
        document = IntakeDocument(
            document_id=assessment.document_id,
            case_id=session.case_id,
            filename=safe_name,
            mime_type=mime_type or "application/octet-stream",
            size_bytes=len(data),
            sha256=digest,
            status=status,
            quality={**quality, "assurance_scores": {"fraud": assessment.fraud_score, "completeness": assessment.completeness_score, "relevance": assessment.relevance_score}},
            error_code=error_code,
            created_at=now,
            updated_at=now,
        )
        self.repository.save_intake_document(session.intake_id, document, [item.model_dump(mode="json") for item in sections])
        session.status = IntakeStatus.FILES_UPLOADED
        session.profile = session.profile.model_copy(update={"rm_confirmed": False, "confirmed_by": None, "confirmed_at": None}) if session.profile else None
        session.audit_events.append(
            _event(
                session.employee_id,
                "case_document_uploaded" if status == DocumentJobStatus.UPLOADED else "case_document_quarantined",
                {"document_id": document.document_id, "filename": safe_name, "status": status.value},
            )
        )
        updated = self.repository.save_intake(session, expected_version=stored.version)
        return updated, document, False

    def process(self, stored: StoredIntake) -> StoredIntake:
        session = stored.session
        documents = self.repository.list_intake_documents(session.intake_id, include_sections=True)
        if not documents:
            raise IntakeValidationError("NO_DOCUMENTS", "Chưa có tài liệu để xử lý", status_code=409)
        session.status = IntakeStatus.DOCUMENT_PROCESSING
        session.audit_events.append(_event("DocumentIntake", "document_processing_started", {"count": len(documents)}))
        document_ids = {item[0].document_id for item in documents}
        session.extracted_fields = [
            item for item in session.extracted_fields if item.source_document_id not in document_ids
        ]
        completed = 0
        for document, sections in documents:
            if document.status in {DocumentJobStatus.QUARANTINED, DocumentJobStatus.NEEDS_OCR, DocumentJobStatus.DEAD_LETTER}:
                self.repository.save_processing_job(
                    session.intake_id,
                    document.document_id,
                    stage="blocked",
                    status=document.status.value,
                    error_code=document.error_code,
                )
                continue
            document.status = DocumentJobStatus.PROCESSING
            document.updated_at = _now()
            self.repository.update_intake_document(session.intake_id, document)
            self.repository.save_processing_job(session.intake_id, document.document_id, stage="extract", status="processing")
            combined = "\n".join(str(item.get("text") or "") for item in sections)
            document_type, classification_confidence = classify_document(document.filename, combined)
            document.document_type = document_type
            fields = extract_document_fields(
                document_id=document.document_id,
                document_type=document_type,
                sections=sections,
            )
            session.extracted_fields.extend(fields)
            document.status = DocumentJobStatus.COMPLETED
            document.quality = {**document.quality, "classification_confidence": classification_confidence, "field_count": len(fields)}
            document.updated_at = _now()
            self.repository.update_intake_document(session.intake_id, document)
            self.repository.save_document_extractions(document.document_id, sections)
            self.repository.save_processing_job(session.intake_id, document.document_id, stage="complete", status="completed")
            completed += 1
        if completed == 0:
            session.status = IntakeStatus.PROCESSING_FAILED
            session.audit_events.append(_event("DocumentIntake", "document_processing_failed", {"reason": "no_processable_documents"}))
        else:
            session.status = IntakeStatus.EXTRACTION_COMPLETED
            session.conflicts = self._detect_conflicts(session.extracted_fields)
            session.profile = self._build_profile(session)
            session.status = IntakeStatus.PROFILE_REVIEW_REQUIRED
            session.audit_events.append(
                _event(
                    "DocumentIntake",
                    "intake_extraction_completed",
                    {"processed": completed, "fields": len(session.extracted_fields), "conflicts": len(session.conflicts)},
                )
            )
            self.repository.replace_extracted_fields(session.intake_id, session.extracted_fields)
            self.repository.replace_field_conflicts(session.intake_id, session.conflicts)
            if session.profile:
                self.repository.save_profile_draft(session.intake_id, session.profile)
        return self.repository.save_intake(session, expected_version=stored.version)

    def patch_profile(
        self,
        stored: StoredIntake,
        *,
        changes: Iterable[ProfileChange],
        employee_id: str,
    ) -> StoredIntake:
        session = stored.session
        if session.status not in {IntakeStatus.PROFILE_REVIEW_REQUIRED, IntakeStatus.EXTRACTION_COMPLETED}:
            raise IntakeValidationError("PROFILE_NOT_EDITABLE", "Hồ sơ không ở trạng thái cho phép chỉnh sửa", status_code=409)
        now = _now()
        for change in changes:
            current = self._resolved_fields(session.extracted_fields).get(change.field_name)
            session.extracted_fields.append(
                ExtractedField(
                    field_id=f"FIELD-{uuid.uuid4().hex[:12].upper()}",
                    field_name=change.field_name,
                    value=change.value,
                    normalized_value=change.value,
                    source_document_id="RM_CONFIRMATION",
                    source_section="profile_review",
                    source_text_span=change.reason,
                    extraction_method="human_correction",
                    confidence=1.0,
                    validation_status=FieldValidationStatus.VALID,
                    decision_impact=current.decision_impact if current else "high",
                    confirmed_by_rm=True,
                    original_value=current.value if current else None,
                    edited_value=change.value,
                    edited_by=employee_id,
                    edited_at=now,
                )
            )
            for conflict in session.conflicts:
                if conflict.field_name == change.field_name and conflict.requires_confirmation:
                    conflict.requires_confirmation = False
                    conflict.resolved_value = change.value
                    conflict.resolved_by = employee_id
                    conflict.resolved_at = now
            session.audit_events.append(
                _event(employee_id, "profile_field_corrected", {"field": change.field_name, "reason": change.reason})
            )
        session.profile = self._build_profile(session)
        self.repository.replace_extracted_fields(session.intake_id, session.extracted_fields)
        self.repository.replace_field_conflicts(session.intake_id, session.conflicts)
        if session.profile:
            self.repository.save_profile_draft(session.intake_id, session.profile)
        return self.repository.save_intake(session, expected_version=stored.version)

    def confirm(self, stored: StoredIntake, *, employee_id: str, attestation: bool) -> StoredIntake:
        session = stored.session
        if not attestation:
            raise IntakeValidationError("ATTESTATION_REQUIRED", "RM phải xác nhận đã kiểm tra hồ sơ")
        if session.status != IntakeStatus.PROFILE_REVIEW_REQUIRED:
            raise IntakeValidationError("PROFILE_NOT_READY", "Hồ sơ chưa sẵn sàng xác nhận", status_code=409)
        blockers = [item.field_name for item in session.conflicts if item.requires_confirmation and item.decision_impact == "high"]
        if blockers:
            raise IntakeValidationError("UNRESOLVED_BLOCKERS", f"Còn xung đột cần xử lý: {', '.join(blockers)}", status_code=409)
        if session.profile is None:
            raise IntakeValidationError("PROFILE_NOT_READY", "Chưa có Customer Business Snapshot", status_code=409)
        name = session.profile.company_identity.get("name")
        if not name:
            raise IntakeValidationError("COMPANY_NAME_REQUIRED", "Thiếu tên doanh nghiệp")
        now = _now()
        profile = session.profile.model_copy(
            update={
                "rm_confirmed": True,
                "confirmed_by": employee_id,
                "confirmed_at": now,
            }
        )
        profile.snapshot_hash = _profile_hash(profile)
        session.profile = profile
        session.status = IntakeStatus.PROFILE_CONFIRMED
        session.audit_events.append(
            _event(employee_id, "customer_profile_confirmed", {"snapshot_id": profile.snapshot_id, "snapshot_hash": profile.snapshot_hash})
        )
        self.repository.save_profile_draft(session.intake_id, profile)
        return self.repository.save_intake(session, expected_version=stored.version)

    @staticmethod
    def public_document(document: IntakeDocument) -> Dict[str, Any]:
        return document.model_dump(mode="json")

    @staticmethod
    def _initial_fields(manual: Dict[str, Any], crm: Dict[str, Any]) -> List[ExtractedField]:
        now = _now()
        fields: List[ExtractedField] = []

        def add(name: str, value: Any, source: str, confidence: float, confirmed: bool, impact: str) -> None:
            if value is None or value == "" or value == []:
                return
            fields.append(
                ExtractedField(
                    field_id=f"FIELD-{uuid.uuid4().hex[:12].upper()}",
                    field_name=name,
                    value=value,
                    normalized_value=value,
                    source_document_id=source,
                    source_section="case_form" if source == "RM_INPUT" else "crm_profile",
                    source_text_span=str(value)[:300],
                    extraction_method="manual_input" if source == "RM_INPUT" else "crm_context",
                    confidence=1.0 if confirmed else confidence,
                    validation_status=FieldValidationStatus.VALID,
                    decision_impact=impact,
                    confirmed_by_rm=confirmed,
                    edited_at=now if confirmed else None,
                )
            )

        add("company_identity.name", manual.get("company_name"), "RM_INPUT", 1.0, True, "high")
        add("company_identity.tax_code", manual.get("tax_code"), "RM_INPUT", 1.0, True, "high")
        add("company_identity.industry", manual.get("industry"), "RM_INPUT", 1.0, True, "medium")
        add("explicit_needs", detect_needs(str(manual.get("need_text") or "")), "RM_INPUT", 1.0, True, "medium")
        add("business_profile.employees_count", crm.get("employees_count"), "CRM_PROFILE", 0.9, False, "high")
        add("business_profile.annual_revenue", crm.get("annual_revenue"), "CRM_PROFILE", 0.9, False, "high")
        add("business_profile.operating_years", crm.get("operating_years"), "CRM_PROFILE", 0.9, False, "high")
        add("business_profile.account_or_unit_count", crm.get("account_or_unit_count"), "CRM_PROFILE", 0.9, False, "high")
        add("legal_profile.ubo_status", crm.get("ubo_status"), "CRM_PROFILE", 0.85, False, "high")
        add("financing_profile.has_bad_debt_12m", crm.get("has_bad_debt_12m"), "CRM_PROFILE", 0.9, False, "high")
        add("cash_flow_profile.current_status", crm.get("cash_flow_status"), "CRM_PROFILE", 0.85, False, "medium")
        return fields

    def _build_profile(self, session: IntakeSession) -> CustomerBusinessSnapshot:
        resolved = self._resolved_fields(session.extracted_fields)
        sections: Dict[str, Dict[str, Any]] = {
            "company_identity": {},
            "business_profile": {},
            "operating_model": {},
            "transaction_profile": {},
            "collection_profile": {},
            "payment_profile": {},
            "payroll_profile": {},
            "cash_flow_profile": {},
            "technology_profile": {},
            "financing_profile": {},
            "legal_profile": {},
        }
        source_map: Dict[str, str] = {}
        confidence: Dict[str, float] = {}
        explicit_needs: List[str] = []
        pain_points: List[str] = []
        for name, field in resolved.items():
            source_map[name] = field.source_document_id
            confidence[name] = field.confidence
            if name == "explicit_needs":
                explicit_needs.extend(field.value if isinstance(field.value, list) else [str(field.value)])
                continue
            if name == "pain_points":
                pain_points.extend(field.value if isinstance(field.value, list) else [str(field.value)])
                continue
            if "." in name:
                section, leaf = name.split(".", 1)
                if section in sections:
                    sections[section][leaf] = field.value
        missing: List[str] = []
        if not sections["company_identity"].get("tax_code"):
            missing.append("company_identity.tax_code")
        if not explicit_needs:
            missing.append("explicit_needs")
        now = _now()
        revision = (session.profile.revision + 1) if session.profile else 1
        profile = CustomerBusinessSnapshot(
            snapshot_id=f"SNAP-{uuid.uuid4().hex[:12].upper()}",
            revision=revision,
            snapshot_hash="pending",
            **sections,
            explicit_needs=list(dict.fromkeys(explicit_needs)),
            pain_points=list(dict.fromkeys(pain_points)),
            missing_information=missing,
            source_map=source_map,
            confidence_summary=confidence,
            rm_confirmed=False,
            created_at=now,
        )
        profile.snapshot_hash = _profile_hash(profile)
        return profile

    @staticmethod
    def _resolved_fields(fields: Iterable[ExtractedField]) -> Dict[str, ExtractedField]:
        priority = {"RM_CONFIRMATION": 5, "RM_INPUT": 4, "CRM_PROFILE": 2}
        resolved: Dict[str, ExtractedField] = {}
        for field in fields:
            score = priority.get(field.source_document_id, 3) + (1 if field.confirmed_by_rm else 0)
            current = resolved.get(field.field_name)
            current_score = priority.get(current.source_document_id, 3) + (1 if current.confirmed_by_rm else 0) if current else -1
            if current is None or score > current_score or (score == current_score and field.confidence >= current.confidence):
                resolved[field.field_name] = field
        return resolved

    @staticmethod
    def _detect_conflicts(fields: Iterable[ExtractedField]) -> List[FieldConflict]:
        grouped: Dict[str, List[ExtractedField]] = {}
        for field in fields:
            grouped.setdefault(field.field_name, []).append(field)
        conflicts: List[FieldConflict] = []
        for name, candidates in grouped.items():
            distinct: Dict[str, ExtractedField] = {}
            for item in candidates:
                key = json.dumps(item.normalized_value, ensure_ascii=False, sort_keys=True, default=str)
                distinct[key] = item
            if len(distinct) < 2:
                continue
            values = list(distinct.values())
            impact = "high" if any(item.decision_impact == "high" for item in values) else "medium"
            rm_confirmed = next((item for item in values if item.confirmed_by_rm), None)
            conflicts.append(
                FieldConflict(
                    conflict_id=f"CONFLICT-{uuid.uuid4().hex[:12].upper()}",
                    field_name=name,
                    candidates=[
                        {"value": item.value, "source_id": item.source_document_id, "confidence": item.confidence}
                        for item in values
                    ],
                    decision_impact=impact,
                    requires_confirmation=impact == "high" and rm_confirmed is None,
                    resolved_value=rm_confirmed.value if rm_confirmed else None,
                    resolved_by=rm_confirmed.edited_by if rm_confirmed else None,
                    resolved_at=rm_confirmed.edited_at if rm_confirmed else None,
                )
            )
        return conflicts


def _profile_hash(profile: CustomerBusinessSnapshot) -> str:
    payload = profile.model_dump(mode="json", exclude={"snapshot_hash"})
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event(actor: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"actor": actor, "action": action, "at": _now().isoformat(), "payload": payload}
