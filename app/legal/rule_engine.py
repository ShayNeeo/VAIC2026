"""Rule Engine (L5 + L6).

Đánh giá các điều kiện deterministic dựa trên LegalProfile và State.
Sở hữu kết quả passed/failed/pending_information/pending_review.
"""

from typing import Any, Dict, List

from app.schemas.state import SharedCaseState
from .models import (
    ComplianceRule, 
    LegalProfile, 
    ProductEligibilityResult, 
    RuleEvaluationResult
)
from .rule_registry import RuleRegistry


class RuleEngine:
    """Deterministic Rule Engine."""

    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def evaluate_all_products(self, state: SharedCaseState, profile: LegalProfile) -> List[ProductEligibilityResult]:
        """Đánh giá eligibility cho tất cả sản phẩm đang được propose (L6)."""
        results = []
        
        # Nếu chưa có product nào được propose, ta thử evaluate toàn bộ hoặc chỉ 1 product mặc định.
        # thường Product Agent sẽ điền vào state.product_result["recommended_products"]
        products_to_check = []
        if state.product_result and "recommended_products" in state.product_result:
            for p in state.product_result["recommended_products"]:
                if isinstance(p, dict) and p.get("product_id"):
                    products_to_check.append(p.get("product_id"))
                elif isinstance(p, str):
                    products_to_check.append(p)
        
        # Nếu vẫn không có, ta test 1 số sản phẩm demo
        if not products_to_check:
            products_to_check = ["PROD-WORKING-CAPITAL", "PROD-PAYROLL"]
            
        for product_id in set(products_to_check):
            results.append(self.evaluate_product(product_id, profile))
            
        return results

    def evaluate_product(self, product_id: str, profile: LegalProfile) -> ProductEligibilityResult:
        """Đánh giá các rules cho một sản phẩm cụ thể (L5)."""
        # 1. Lấy danh sách rules áp dụng cho product này
        rules = self.registry.get_rules_for_product(product_id)
        
        result = ProductEligibilityResult(
            product_id=product_id,
            product_name=product_id,  # có thể enrich tên nếu cần
            status="passed" # Default status, will be updated later
        )
        
        # 2. Evaluate từng rule
        for rule in rules:
            eval_res = self._evaluate_single_rule(rule, profile)
            
            if eval_res.status == "failed":
                result.blocking_rules.append(eval_res)
            elif eval_res.status == "pending_information" or eval_res.status == "pending_review":
                # Các trạng thái này cũng block quá trình
                result.blocking_rules.append(eval_res)
            elif eval_res.status == "passed" and rule.severity == "warning":
                # Nếu rule warning mà có vấn đề nhẹ thì status có thể vẫn pass nhưng đưa vào warning
                # Ở đây đơn giản: passed -> passed_rules
                pass
                
            if eval_res.status == "passed":
                result.passed_rules.append(eval_res)
            elif rule.severity == "warning" and eval_res.status != "passed":
                result.warning_rules.append(eval_res)
                # Warning không đưa vào blocking_rules nếu không muốn block, 
                # nhưng ở trên ta đang coi mọi fail là block trừ khi nó warning.
                # Logic chuẩn:
                if eval_res in result.blocking_rules:
                    result.blocking_rules.remove(eval_res)

        # 3. Tính toán overall status
        if any(r.status == "failed" for r in result.blocking_rules):
            result.status = "failed"
        elif any(r.status == "pending_review" for r in result.blocking_rules):
            result.status = "pending_review"
        elif any(r.status == "pending_information" for r in result.blocking_rules):
            result.status = "pending_information"
        else:
            result.status = "passed"
            
        return result

    def _evaluate_single_rule(self, rule: ComplianceRule, profile: LegalProfile) -> RuleEvaluationResult:
        """Thực thi logic deterministic cho từng loại rule."""
        
        res = RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            rule_version=rule.version,
            severity=rule.severity,
            priority=rule.priority,
            source_document_id=rule.source_document_id,
            source_location=rule.source_location,
            status="passed"
        )
        
        if rule.rule_id == "RULE-WATCHLIST-001":
            if profile.watchlist_result and profile.watchlist_result.get("match_found"):
                res.status = "failed"
                res.reason = profile.watchlist_result.get("reason", rule.failure_message)
                res.failure_code = rule.failure_code
                
        elif rule.rule_id == "RULE-BUSINESS-REG-001":
            if not profile.has_business_reg:
                res.status = "pending_information"
                res.reason = "Thiếu Giấy chứng nhận đăng ký doanh nghiệp"
                res.failure_code = rule.failure_code
            elif profile.business_reg_expired:
                res.status = "failed"
                res.reason = "Giấy chứng nhận đăng ký doanh nghiệp đã hết hạn"
                res.failure_code = rule.failure_code
            elif profile.business_reg_tax_mismatch:
                res.status = "pending_review"
                res.reason = "Mã số thuế trên ĐKKD không khớp với hồ sơ"
                res.failure_code = rule.failure_code

        elif rule.rule_id == "RULE-LEGAL-REP-001":
            rep = profile.representative
            if not rep or not rep.name or not rep.id_number:
                res.status = "pending_information"
                res.reason = "Thiếu thông tin người đại diện pháp luật"
                res.failure_code = rule.failure_code
            # Ta cũng có thể check expiry của CCCD nếu có metadata

        elif rule.rule_id == "RULE-UBO-001":
            if profile.ubo.status == "missing" and not profile.ubo.doc_present:
                res.status = "pending_information"
                res.reason = "Thiếu thông tin UBO"
                res.failure_code = rule.failure_code
            elif profile.ubo.status == "partial" and not profile.ubo.doc_present:
                res.status = "pending_information"
                res.reason = "Thông tin UBO chưa đầy đủ"
                res.failure_code = rule.failure_code

        elif rule.rule_id == "RULE-CREDIT-FS-001":
            if not profile.has_financial_reports:
                res.status = "pending_information"
                res.reason = "Thiếu báo cáo tài chính cho đánh giá tín dụng"
                res.failure_code = rule.failure_code

        elif rule.rule_id == "RULE-DOC-EXPIRY-001":
            expired_docs = [d.get("document_type_id", "Unknown") for d in profile.classified_documents if d.get("is_expired")]
            if expired_docs:
                res.status = "failed"
                res.reason = f"Tài liệu đã hết hạn: {', '.join(expired_docs)}"
                res.failure_code = rule.failure_code

        elif rule.rule_id == "RULE-AUTH-POWER-001":
            if profile.representative.is_authorized and not profile.representative.authorization_doc_present:
                res.status = "pending_information"
                res.reason = "Thiếu giấy ủy quyền hợp lệ"
                res.failure_code = rule.failure_code
                
        return res
