"""In-memory Legal Knowledge Base — fallback khi d:\\data\\legal\\ không có.

Cấu trúc dữ liệu mirrors shb_kyc_aml_policy_2026.json và shb_credit_policy_manual.json
nhưng ở dạng Python dict để có thể dùng offline không cần file hệ thống.

NOTE: Dữ liệu này là SYNTHETIC DEMO. Không phải chính sách thật của SHB.
"""

from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# In-memory policy chunks — mỗi chunk là một điều/khoản
# Cấu trúc: document_id, article_id, title, text, rule_refs, effective_from
# ---------------------------------------------------------------------------

LEGAL_KNOWLEDGE_CHUNKS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # SHB_KYC_AML_Demo_Policy_2026
    # -------------------------------------------------------------------------
    {
        "chunk_id": "KYC-DIEU-3",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương II — Định danh và Xác minh Doanh nghiệp",
        "article": "Điều 3 — Định danh doanh nghiệp",
        "article_id": "DIEU-3",
        "text": (
            "Mã số thuế trên giấy chứng nhận đăng ký doanh nghiệp phải khớp với hồ sơ khách hàng. "
            "Trường hợp không khớp, hồ sơ bị từ chối cho đến khi có xác nhận. "
            "Giấy đăng ký doanh nghiệp hết hạn hoặc bị thu hồi dẫn đến trạng thái từ chối toàn bộ dịch vụ."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-BUSINESS-REG-001"],
        "keywords": ["đăng ký", "dkkd", "mã số thuế", "định danh doanh nghiệp", "giấy chứng nhận"],
    },
    {
        "chunk_id": "KYC-DIEU-4",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương II — Định danh và Xác minh Doanh nghiệp",
        "article": "Điều 4 — Hồ sơ đăng ký bắt buộc",
        "article_id": "DIEU-4",
        "text": (
            "Bộ hồ sơ đăng ký tối thiểu cho khách hàng doanh nghiệp bao gồm Giấy chứng nhận đăng ký doanh nghiệp, "
            "CCCD/Hộ chiếu còn hiệu lực của người đại diện pháp luật và hợp đồng dịch vụ. "
            "CCCD/Hộ chiếu của người đại diện pháp luật phải còn hiệu lực và không bị hết hạn quá 6 tháng tính từ ngày nộp hồ sơ."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-BUSINESS-REG-001", "RULE-LEGAL-REP-001", "RULE-DOC-EXPIRY-001"],
        "keywords": ["hồ sơ", "cccd", "hộ chiếu", "người đại diện", "đăng ký bắt buộc"],
    },
    {
        "chunk_id": "KYC-DIEU-5",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương III — Người đại diện pháp luật và Ủy quyền",
        "article": "Điều 5 — Người đại diện pháp luật",
        "article_id": "DIEU-5",
        "text": (
            "Người đại diện pháp luật phải được xác minh danh tính theo quy định KYC cá nhân. "
            "Thông tin người đại diện pháp luật trên hồ sơ KYC phải khớp với thông tin đăng ký tại cơ quan nhà nước. "
            "Nếu có thay đổi người đại diện pháp luật, doanh nghiệp phải thông báo trong vòng 30 ngày."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-LEGAL-REP-001"],
        "keywords": ["người đại diện", "pháp luật", "đại diện pháp luật", "kyc", "xác minh"],
    },
    {
        "chunk_id": "KYC-DIEU-6",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương III — Người đại diện pháp luật và Ủy quyền",
        "article": "Điều 6 — Ủy quyền",
        "article_id": "DIEU-6",
        "text": (
            "Giấy ủy quyền phải nêu rõ phạm vi ủy quyền, thời hạn và được công chứng hoặc xác nhận bởi cơ quan có thẩm quyền. "
            "Số CCCD/Hộ chiếu của người được ủy quyền phải khớp với giấy ủy quyền và hồ sơ định danh gốc. "
            "Giấy ủy quyền phải được công chứng và còn trong thời hạn hiệu lực."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-AUTH-POWER-001"],
        "keywords": ["ủy quyền", "giấy ủy quyền", "công chứng", "phạm vi ủy quyền"],
    },
    {
        "chunk_id": "KYC-DIEU-8",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương IV — Chủ sở hữu hưởng lợi (UBO) và KYC nâng cao",
        "article": "Điều 8 — Chủ sở hữu hưởng lợi (UBO)",
        "article_id": "DIEU-8",
        "text": (
            "Hồ sơ khách hàng doanh nghiệp phải có thông tin chủ sở hữu hưởng lợi cuối cùng (UBO). "
            "UBO là cá nhân sở hữu trực tiếp hoặc gián tiếp từ 25% trở lên vốn điều lệ, "
            "hoặc có quyền kiểm soát thực tế đối với doanh nghiệp. "
            "Thiếu thông tin UBO sẽ chặn tất cả các sản phẩm tín dụng và các sản phẩm có rủi ro cao. "
            "Đối với sản phẩm vốn lưu động, thấu chi và tín dụng ngắn hạn, thông tin UBO là điều kiện bắt buộc blocking. "
            "Doanh nghiệp phải khai báo đầy đủ danh sách UBO bao gồm họ tên, ngày sinh, quốc tịch, tỷ lệ sở hữu và số giấy tờ định danh."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-UBO-001"],
        "keywords": ["ubo", "chủ sở hữu hưởng lợi", "sở hữu thực", "kiểm soát thực tế", "25%", "vốn điều lệ"],
    },
    {
        "chunk_id": "KYC-DIEU-9",
        "document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "document_title": "Chính sách KYC/AML Demo 2026",
        "chapter": "Chương IV — Chủ sở hữu hưởng lợi (UBO) và KYC nâng cao",
        "article": "Điều 9 — Danh sách cấm vận và PEP",
        "article_id": "DIEU-9",
        "text": (
            "Trước khi cung cấp bất kỳ dịch vụ nào, SHB phải thực hiện sàng lọc doanh nghiệp và các UBO "
            "theo danh sách cấm vận quốc tế (UN, OFAC) và danh sách người chính trị có ảnh hưởng (PEP). "
            "Kết quả khớp danh sách cấm vận là hard block — không được cung cấp bất kỳ dịch vụ nào và phải báo cáo ngay cho Compliance. "
            "Kết quả khớp PEP phải chuyển pending_review và yêu cầu phê duyệt từ Giám đốc Chi nhánh."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-WATCHLIST-001"],
        "keywords": ["cấm vận", "pep", "watchlist", "sanction", "sàng lọc", "un", "ofac", "danh sách đen"],
    },
    # -------------------------------------------------------------------------
    # SHB_Credit_Policy_Manual
    # -------------------------------------------------------------------------
    {
        "chunk_id": "CREDIT-DIEU-15",
        "document_id": "SHB_Credit_Policy_Manual",
        "document_title": "Sổ tay Chính sách Tín dụng Doanh nghiệp Demo 2026",
        "chapter": "Chương III — Điều kiện cấp tín dụng",
        "article": "Điều 15 — Điều kiện chung",
        "article_id": "DIEU-15",
        "text": (
            "Doanh nghiệp xin cấp tín dụng phải đáp ứng đồng thời các điều kiện: "
            "có giấy chứng nhận đăng ký doanh nghiệp còn hiệu lực, "
            "có thông tin UBO đầy đủ, "
            "không có kết quả khớp danh sách cấm vận và "
            "có báo cáo tài chính năm gần nhất được kiểm toán. "
            "Tất cả điều kiện phải được thỏa mãn đồng thời. Không có điều kiện nào có thể bị bỏ qua."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-UBO-001", "RULE-CREDIT-FS-001", "RULE-BUSINESS-REG-001"],
        "keywords": ["tín dụng", "điều kiện cấp", "tín dụng ngắn hạn", "working capital", "vốn lưu động"],
    },
    {
        "chunk_id": "CREDIT-DIEU-25",
        "document_id": "SHB_Credit_Policy_Manual",
        "document_title": "Sổ tay Chính sách Tín dụng Doanh nghiệp Demo 2026",
        "chapter": "Chương V — Hồ sơ tín dụng",
        "article": "Điều 25 — Báo cáo tài chính",
        "article_id": "DIEU-25",
        "text": (
            "Hồ sơ cấp tín dụng vốn lưu động phải có báo cáo tài chính năm gần nhất được kiểm toán bởi công ty kiểm toán độc lập. "
            "Báo cáo tài chính không được lập quá 18 tháng tính đến ngày nộp hồ sơ. "
            "Đối với sản phẩm thấu chi tài khoản và vốn lưu động, báo cáo tài chính năm gần nhất là bắt buộc ở mức độ blocking. "
            "Không có ngoại lệ. "
            "Thiếu báo cáo tài chính hoặc báo cáo quá hạn dẫn đến trạng thái pending_information. "
            "Báo cáo tài chính phải được kiểm toán độc lập; báo cáo nội bộ không được chấp nhận thay thế."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": ["RULE-CREDIT-FS-001"],
        "keywords": [
            "báo cáo tài chính", "bctc", "kiểm toán", "tín dụng vốn lưu động",
            "thấu chi", "hồ sơ tín dụng", "tài chính năm gần nhất"
        ],
    },
    {
        "chunk_id": "CREDIT-DIEU-35",
        "document_id": "SHB_Credit_Policy_Manual",
        "document_title": "Sổ tay Chính sách Tín dụng Doanh nghiệp Demo 2026",
        "chapter": "Chương VII — Thẩm quyền phê duyệt",
        "article": "Điều 35 — Phân cấp thẩm quyền",
        "article_id": "DIEU-35",
        "text": (
            "Thẩm quyền phê duyệt tín dụng: dưới 5 tỷ VND do Giám đốc Chi nhánh phê duyệt, "
            "từ 5-50 tỷ do Hội đồng Tín dụng Chi nhánh, trên 50 tỷ do Hội sở. "
            "Mọi kết quả thẩm định Legal phải được đính kèm trước khi trình phê duyệt."
        ),
        "effective_from": "2026-01-01",
        "rule_refs": [],
        "keywords": ["thẩm quyền", "phê duyệt", "hạn mức", "hội đồng tín dụng", "giám đốc chi nhánh"],
    },
]


# ---------------------------------------------------------------------------
# In-memory rules fallback (mirrors data\legal\rules\compliance_rules.json)
# ---------------------------------------------------------------------------

BUILTIN_COMPLIANCE_RULES: list[dict] = [
    {
        "rule_id": "RULE-WATCHLIST-001",
        "version": "2026.1",
        "name": "Sàng lọc Danh sách cấm vận và PEP",
        "scope": [],  # all products
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "hard_block",
        "priority": 1,
        "condition_type": "deterministic",
        "condition_description": "Doanh nghiệp hoặc UBO không trong danh sách cấm vận/PEP",
        "required_inputs": ["company_profile.company_name", "company_profile.tax_code"],
        "failure_code": "WATCHLIST_MATCH",
        "failure_message": "Doanh nghiệp hoặc đại diện khớp danh sách cấm vận/PEP — hard block",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 9 - Danh sách cấm vận và PEP",
        "escalation_owner": "Legal/Compliance",
        "action_on_failure": "hard_block_all_services",
    },
    {
        "rule_id": "RULE-BUSINESS-REG-001",
        "version": "2026.1",
        "name": "Giấy chứng nhận đăng ký doanh nghiệp",
        "scope": [],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "blocking",
        "priority": 2,
        "condition_type": "deterministic",
        "condition_description": "ĐKKD phải tồn tại, còn hiệu lực và MST khớp",
        "required_inputs": ["documents", "company_profile.tax_code"],
        "failure_code": "BUSINESS_REG_INVALID",
        "failure_message": "Thiếu hoặc không hợp lệ Giấy chứng nhận đăng ký doanh nghiệp",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 3 - Định danh doanh nghiệp",
        "escalation_owner": None,
        "action_on_failure": "block_all_services",
    },
    {
        "rule_id": "RULE-LEGAL-REP-001",
        "version": "2026.1",
        "name": "Người đại diện pháp luật",
        "scope": [],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "blocking",
        "priority": 2,
        "condition_type": "deterministic",
        "condition_description": "Thông tin người đại diện pháp luật phải có và CCCD còn hiệu lực",
        "required_inputs": ["company_profile.representative", "documents"],
        "failure_code": "LEGAL_REP_MISSING",
        "failure_message": "Thiếu thông tin người đại diện pháp luật hoặc CCCD/hộ chiếu hết hạn",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 5 - Người đại diện pháp luật",
        "escalation_owner": None,
        "action_on_failure": "block_all_services",
    },
    {
        "rule_id": "RULE-UBO-001",
        "version": "2026.1",
        "name": "Chủ sở hữu hưởng lợi (UBO)",
        "scope": ["PROD-WORKING-CAPITAL"],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "blocking",
        "priority": 2,
        "condition_type": "deterministic",
        "condition_description": "Hồ sơ phải có thông tin UBO cho sản phẩm tín dụng",
        "required_inputs": ["company_profile.ubo_status", "documents"],
        "failure_code": "UBO_MISSING",
        "failure_message": "Thiếu thông tin chủ sở hữu hưởng lợi cuối cùng (UBO)",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 8 - Chủ sở hữu hưởng lợi",
        "escalation_owner": None,
        "action_on_failure": "block_credit_products",
    },
    {
        "rule_id": "RULE-CREDIT-FS-001",
        "version": "2026.1",
        "name": "Báo cáo tài chính cho tín dụng",
        "scope": ["PROD-WORKING-CAPITAL"],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "blocking",
        "priority": 3,
        "condition_type": "deterministic",
        "condition_description": "Hồ sơ tín dụng vốn lưu động phải có BCTC năm gần nhất",
        "required_inputs": ["documents", "company_profile.financial_reports"],
        "failure_code": "FINANCIAL_STATEMENT_MISSING",
        "failure_message": "Thiếu báo cáo tài chính năm gần nhất cho thẩm định tín dụng",
        "source_document_id": "SHB_Credit_Policy_Manual",
        "source_location": "Chương V - Hồ sơ tín dụng",
        "escalation_owner": None,
        "action_on_failure": "block_credit_products",
    },
    {
        "rule_id": "RULE-AUTH-POWER-001",
        "version": "2026.1",
        "name": "Giấy ủy quyền",
        "scope": [],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "warning",
        "priority": 5,
        "condition_type": "deterministic",
        "condition_description": "Nếu có người được ủy quyền, giấy ủy quyền phải hợp lệ",
        "required_inputs": ["documents"],
        "failure_code": "AUTH_POWER_INVALID",
        "failure_message": "Giấy ủy quyền không hợp lệ hoặc hết hạn",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 6 - Ủy quyền",
        "escalation_owner": None,
        "action_on_failure": "warning_only",
    },
    {
        "rule_id": "RULE-DOC-EXPIRY-001",
        "version": "2026.1",
        "name": "Hiệu lực tài liệu chung",
        "scope": [],
        "effective_from": "2026-01-01",
        "effective_to": None,
        "severity": "blocking",
        "priority": 4,
        "condition_type": "deterministic",
        "condition_description": "Tài liệu có ngày hết hạn phải còn trong thời hạn hiệu lực",
        "required_inputs": ["documents"],
        "failure_code": "DOCUMENT_EXPIRED",
        "failure_message": "Một hoặc nhiều tài liệu quan trọng đã hết hạn",
        "source_document_id": "SHB_KYC_AML_Demo_Policy_2026",
        "source_location": "Điều 4 - Hồ sơ đăng ký bắt buộc",
        "escalation_owner": None,
        "action_on_failure": "block_affected_services",
    },
]
