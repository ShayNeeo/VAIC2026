"""Document Classifier (L1).

Nhận diện loại hồ sơ, trích xuất trường và ngày hiệu lực bằng phương pháp
deterministic (keyword matching) thay vì dùng LLM trực tiếp, nhằm tối ưu tốc độ
và đảm bảo tính nhất quán (Plan v3 Section 5 & 11).
"""

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional


class DocumentClassifier:
    """Deterministic document classifier and metadata extractor."""

    # Map các loại tài liệu phổ biến và keyword nhận diện
    DOC_TYPES = {
        "BUSINESS_REGISTRATION": ["đăng ký kinh doanh", "đăng ký doanh nghiệp", "giấy phép kinh doanh", "đkkd"],
        "IDENTITY_DOCUMENT": ["cccd", "căn cước công dân", "cmnd", "chứng minh nhân dân", "hộ chiếu", "passport"],
        "AUTHORIZATION_LETTER": ["ủy quyền", "giấy ủy quyền", "thư ủy quyền", "authorization"],
        "FINANCIAL_STATEMENT": ["báo cáo tài chính", "bctc", "cân đối kế toán", "kết quả kinh doanh", "lưu chuyển tiền tệ"],
        "UBO_DECLARATION": ["ubo", "chủ sở hữu hưởng lợi", "hưởng lợi cuối cùng"],
    }

    def classify_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phân loại và bổ sung metadata cho danh sách tài liệu."""
        classified_docs = []
        for doc in documents:
            classified_doc = dict(doc)  # copy
            
            # 1. Xác định document_type_id
            if "document_type_id" not in classified_doc or not classified_doc["document_type_id"]:
                title_or_type = doc.get("title", doc.get("doc_type", ""))
                classified_doc["document_type_id"] = self._detect_doc_type(
                    title_or_type, doc.get("content", "")
                )
            
            # 2. Chuẩn hóa ngày tháng (issue_date, expiry_date)
            for date_field in ["issue_date", "expiry_date"]:
                if date_field in classified_doc and isinstance(classified_doc[date_field], str):
                    parsed_date = self._parse_date(classified_doc[date_field])
                    if parsed_date:
                        classified_doc[date_field] = parsed_date.isoformat()
            
            # 3. Tính toán trạng thái hiệu lực (nếu có expiry_date)
            self._evaluate_expiry(classified_doc)
            
            classified_docs.append(classified_doc)
            
        return classified_docs

    def _detect_doc_type(self, title: str, content: str) -> str:
        """Dùng keyword matching để tìm loại tài liệu."""
        text = f"{title} {content}".lower()
        
        # Thử tìm theo từ khóa
        for doc_type, keywords in self.DOC_TYPES.items():
            for kw in keywords:
                if kw in text:
                    return doc_type
                    
        return "UNKNOWN"

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Chuẩn hóa chuỗi ngày tháng."""
        if not date_str:
            return None
            
        # Thử một số format phổ biến
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ"]
        
        for fmt in formats:
            try:
                # Nếu là timestamp iso có timezone thì cắt phần timezone đi để parse cho dễ với strptime cơ bản
                if "T" in date_str and (date_str.endswith("Z") or "+" in date_str or "-" in date_str[11:]):
                    clean_str = date_str.split("+")[0]
                    if clean_str.endswith("Z"):
                        clean_str = clean_str[:-1]
                    # Nếu có microsecond
                    if "." in clean_str:
                        return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S.%f").date()
                    return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S").date()
                    
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        return None
        
    def _evaluate_expiry(self, doc: Dict[str, Any]) -> None:
        """Kiểm tra tài liệu đã hết hạn chưa."""
        if "expiry_date" in doc and doc["expiry_date"]:
            try:
                expiry = date.fromisoformat(doc["expiry_date"])
                is_expired = expiry < date.today()
                doc["is_expired"] = is_expired
                doc["status"] = "expired" if is_expired else "active"
            except ValueError:
                doc["is_expired"] = False
                doc["status"] = "active"
        else:
            doc["is_expired"] = False
            doc["status"] = "active"
