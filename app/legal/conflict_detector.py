"""Conflict Detector (L7).

Phát hiện sự không nhất quán giữa CRM data và tài liệu, hoặc giữa các chính sách
để flag ra trạng thái `pending_review` (cần con người can thiệp).
"""

from typing import Any, Dict, List

from .models import LegalProfile


class ConflictDetector:
    """Xác định mâu thuẫn dữ liệu hoặc chính sách."""

    def detect_conflicts(self, profile: LegalProfile, state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Phát hiện các xung đột và trả về danh sách cảnh báo."""
        conflicts = []
        
        # 1. CRM nói có UBO nhưng Document không có
        crm_ubo = profile.ubo.status
        has_ubo_doc = profile.ubo.doc_present
        if crm_ubo == "complete" and not has_ubo_doc:
            conflicts.append({
                "type": "data_conflict",
                "severity": "high",
                "field": "ubo",
                "message": "CRM ghi nhận UBO complete nhưng không tìm thấy tài liệu chứng minh.",
                "action": "pending_review"
            })
            
        # 2. CRM tên công ty khác trên ĐKKD
        crm_name = profile.company_name.lower().strip()
        doc_name = None
        for doc in profile.classified_documents:
            if doc.get("document_type_id") == "BUSINESS_REGISTRATION":
                doc_name = doc.get("extracted_company_name", "").lower().strip()
                break
                
        if doc_name and crm_name and doc_name != crm_name:
            # Simple check, in reality needs fuzzy matching
            if len(set(crm_name.split()).intersection(set(doc_name.split()))) < 2:
                conflicts.append({
                    "type": "data_conflict",
                    "severity": "high",
                    "field": "company_name",
                    "message": f"Tên công ty trên CRM ({profile.company_name}) khác biệt lớn với trên ĐKKD.",
                    "action": "pending_review"
                })

        # 3. CRM Tax Code khác với ĐKKD Tax Code
        # Đã được handle qua RULE-BUSINESS-REG-001 (business_reg_tax_mismatch)
        if profile.business_reg_tax_mismatch:
            conflicts.append({
                "type": "data_conflict",
                "severity": "high",
                "field": "tax_code",
                "message": "Mã số thuế trên CRM không khớp với ĐKKD.",
                "action": "pending_review"
            })

        return conflicts
