"""V3 Product Catalog - Tier A internal authoritative data (§9.2).

Single source of truth for product facts. Matcher, retriever and verifier
all read from here; no other module duplicates product data.

Invariants:
- Every entry carries ``source_metadata`` with document/section/version/owner/tier.
- ``category`` is one of the four product families in the blueprint.
- ``use_cases`` is the keyword vocabulary used by :data:`NEED_KEYWORDS`.
"""

from enum import Enum
from typing import Any, Dict, List, Mapping, Tuple

from mcp_common.schemas import DataTier, ProductFeeLimit, ProductPrerequisite


class ProductNeed(str, Enum):
    """Business needs the Product Agent can resolve (blueprint B3/PR1)."""

    PAYROLL = "payroll"
    CASH_MANAGEMENT = "cash_management"
    COLLECTION = "collection"
    WORKING_CAPITAL = "working_capital"


#: Need -> signal keywords. ``select_needs`` matches these against the request.
NEED_KEYWORDS: Dict[ProductNeed, Tuple[str, ...]] = {
    ProductNeed.PAYROLL: ("payroll", "chi lương", "trả lương", "lương"),
    ProductNeed.CASH_MANAGEMENT: ("cash_management", "dòng tiền", "tài khoản phụ", "đối soát", "cash"),
    ProductNeed.COLLECTION: ("collection", "thu hộ", "chi hộ", "virtual_account", "đối soát", "thu/chi hộ"),
    ProductNeed.WORKING_CAPITAL: ("working_capital", "vốn lưu động", "thấu chi", "tín dụng", "vốn", "hạn mức"),
}


#: Bundle compatibility graph. A product is only bundled with compatible peers.
COMPATIBILITY_GRAPH: Dict[str, Dict[str, List[str]]] = {
    "PROD-PAYROLL": {"compatible": ["PROD-CASH-MGMT", "PROD-COLLECTION"], "exclusion": []},
    "PROD-CASH-MGMT": {"compatible": ["PROD-PAYROLL", "PROD-COLLECTION", "PROD-WORKING-CAPITAL"], "exclusion": []},
    "PROD-COLLECTION": {"compatible": ["PROD-CASH-MGMT", "PROD-PAYROLL"], "exclusion": []},
    "PROD-WORKING-CAPITAL": {"compatible": ["PROD-CASH-MGMT"], "exclusion": []},
}


# V3 Product Catalog — Tier A (Internal Authoritative) per §9.2
V3_PRODUCT_CATALOG: Mapping[str, Mapping[str, Any]] = {
    "PROD-PAYROLL": {
        "product_id": "PROD-PAYROLL",
        "name": "SHB Payroll",
        "description": "Giải pháp chi trả lương tự động, tích hợp kế toán, tính thuế TNCN.",
        "segment": "corporate",
        "category": "payroll",
        "fees_limits": [
            ProductFeeLimit(name="transaction_fee", value=0, unit="VND", condition="internal_transfer"),
            ProductFeeLimit(name="monthly_fee", value=500000, unit="VND"),
        ],
        "prerequisites": [
            ProductPrerequisite(document_type="business_registration", required=True),
            ProductPrerequisite(document_type="employee_list", required=True),
            ProductPrerequisite(document_type="authorization_letter", required=True),
        ],
        "eligibility_rules": "Doanh nghiệp từ 10 nhân sự, có tài khoản SHB, đăng ký Dịch vụ Ngân hàng điện tử.",
        "benefits": [
            "Chi lương hàng loạt",
            "Tự động tính thuế TNCN",
            "Báo cáo tùy chỉnh",
            "Miễn phí chuyển tiền lương nội bộ và liên ngân hàng",
        ],
        "use_cases": ["payroll", "salary", "chi_lương", "trả_lương"],
        "source_metadata": {
            "document": "Product_Catalog_v3.pdf",
            "section": "Payroll",
            "effective_date": "2026-01-01",
            "owner": "Product Team",
            "version": "3.0",
            "tier": DataTier.A,
        },
    },
    "PROD-CASH-MGMT": {
        "product_id": "PROD-CASH-MGMT",
        "name": "SHB Cash Management",
        "description": "Quản lý dòng tiền, tài khoản phụ, đối soát tự động real-time.",
        "segment": "corporate",
        "category": "cash_management",
        "fees_limits": [
            ProductFeeLimit(name="account_fee", value=1000000, unit="VND/month"),
            ProductFeeLimit(name="virtual_account_fee", value=50000, unit="VND/account"),
        ],
        "prerequisites": [
            ProductPrerequisite(document_type="financial_statement", required=True),
            ProductPrerequisite(document_type="cash_flow_6m", required=True),
            ProductPrerequisite(document_type="corporate_profile", required=True),
        ],
        "eligibility_rules": "Doanh nghiệp doanh thu từ 50 tỷ VNĐ/năm, dòng tiền phân tán nhiều ngân hàng.",
        "benefits": [
            "Xem dòng tiền real-time",
            "Tài khoản phụ ảo",
            "Đối soát tự động",
        ],
        "use_cases": ["cash_management", "dòng tiền", "tài khoản phụ", "đối soát"],
        "source_metadata": {
            "document": "Product_Catalog_v3.pdf",
            "section": "Cash_Management",
            "effective_date": "2026-01-01",
            "owner": "Product Team",
            "version": "3.0",
            "tier": DataTier.A,
        },
    },
    "PROD-COLLECTION": {
        "product_id": "PROD-COLLECTION",
        "name": "SHB Collection",
        "description": "Dịch vụ thu hộ, chi hộ, Virtual Account, đối soát.",
        "segment": "corporate",
        "category": "collection",
        "fees_limits": [
            ProductFeeLimit(name="collection_fee", value=0.1, unit="%", condition="per_transaction"),
        ],
        "prerequisites": [
            ProductPrerequisite(document_type="collection_agreement", required=True),
            ProductPrerequisite(document_type="partner_list", required=True),
            ProductPrerequisite(document_type="authorization_letter", required=True),
        ],
        "eligibility_rules": "Cần thu/chi định kỳ, số lượng đối tác lớn, dùng Virtual Account.",
        "benefits": [
            "Thu hộ tự động",
            "Virtual Account",
            "Đối soát real-time",
        ],
        "use_cases": ["collection", "thu_hộ", "chi_hộ", "virtual_account", "đối soát"],
        "source_metadata": {
            "document": "Product_Catalog_v3.pdf",
            "section": "Collection",
            "effective_date": "2026-01-01",
            "owner": "Product Team",
            "version": "3.0",
            "tier": DataTier.A,
        },
    },
    "PROD-WORKING-CAPITAL": {
        "product_id": "PROD-WORKING-CAPITAL",
        "name": "SHB Working Capital",
        "description": "Vốn lưu động, thấu chi, hạn mức overdraft.",
        "segment": "corporate",
        "category": "credit",
        "fees_limits": [
            ProductFeeLimit(name="interest_rate", value=8.5, unit="%/year", condition="floating"),
            ProductFeeLimit(name="limit", value=50000000000, unit="VND"),
        ],
        "prerequisites": [
            ProductPrerequisite(document_type="financial_statement_2y", required=True),
            ProductPrerequisite(document_type="cic_report", required=True),
            ProductPrerequisite(document_type="collateral_documents", required=True),
            ProductPrerequisite(document_type="business_plan", required=True),
        ],
        "eligibility_rules": "Doanh nghiệp hoạt động ≥ 2 năm, BCTC kiểm toán, không nợ xấu, có tài sản đảm bảo.",
        "benefits": [
            "Hạn mức linh hoạt",
            "Lãi suất ưu đãi",
            "Giải ngân nhanh",
        ],
        "use_cases": ["working_capital", "vốn_lưu_động", "thấu_chi", "tín_dụng", "cho_vay"],
        "source_metadata": {
            "document": "Product_Catalog_v3.pdf",
            "section": "Working_Capital",
            "effective_date": "2026-01-01",
            "owner": "Product Team",
            "version": "3.0",
            "tier": DataTier.A,
        },
    },
}


def get_entry(product_id: str) -> Mapping[str, Any]:
    """Return a catalog entry or raise ``KeyError`` (fail loud, not silent)."""
    return V3_PRODUCT_CATALOG[product_id]


def fee_value(product_id: str, fee_name: str) -> "tuple[float, str] | None":
    """Exact fee/limit value+unit from catalog — used by NUMERIC_EXACT verify.

    Returns ``None`` when the fee name is unknown so callers fail closed.
    """
    for fee in get_entry(product_id).get("fees_limits", []):
        if fee.name == fee_name:
            return fee.value, fee.unit
    return None


def source_ref(product_id: str) -> Dict[str, str]:
    """Citation anchor (document/section/effective/owner) for a product."""
    meta = get_entry(product_id)["source_metadata"]
    return {
        "source_document_id": meta["document"],
        "source_section": meta["section"],
        "source_version": meta["effective_date"],
        "owner": meta["owner"],
    }