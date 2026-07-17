"""V3 Product Catalog - Tier A internal authoritative data (§9.2)."""

from typing import Any, Dict, List, Mapping

from mcp_common.schemas import DataTier, ProductFeeLimit, ProductPrerequisite


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