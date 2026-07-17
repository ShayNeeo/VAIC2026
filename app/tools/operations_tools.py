"""Deterministic SOP helpers. All data is synthetic demo data."""

from __future__ import annotations

from typing import Dict, Iterable, List

from app.tools.product_tools import SHB_PRODUCT_CATALOG


SLA_HOURS = {"missing_information": 24, "open_service": 48, "credit_review": 72}


def get_required_documents(product_ids: Iterable[str]) -> List[str]:
    documents: List[str] = []
    for product_id in product_ids:
        product = SHB_PRODUCT_CATALOG.get(product_id, {})
        documents.extend(product.get("required_documents", []))
    return list(dict.fromkeys(documents))


def check_document_completeness(required: Iterable[str], uploaded_documents: Iterable[Dict]) -> List[str]:
    available = " ".join(str(doc.get("doc_type", "")) for doc in uploaded_documents).lower()
    return [item for item in required if item.lower() not in available]


def draft_customer_email(company_name: str, missing_documents: Iterable[str]) -> Dict[str, str]:
    missing = list(dict.fromkeys(item for item in missing_documents if item))
    bullets = "\n".join(f"- {item}" for item in missing) or "- Không có tài liệu cần bổ sung"
    return {
        "subject": f"[SHB] Yêu cầu bổ sung hồ sơ doanh nghiệp - {company_name}",
        "body": (
            f"Kính gửi Quý khách hàng {company_name},\n\n"
            "Để tiếp tục xử lý nhu cầu dịch vụ, kính đề nghị Quý khách bổ sung:\n"
            f"{bullets}\n\n"
            "Đây là email nháp và chỉ được gửi sau khi RM kiểm tra, phê duyệt.\nTrân trọng,\nSHB"
        ),
    }
