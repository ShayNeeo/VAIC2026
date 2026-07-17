from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EvidenceItem(BaseModel):
    agent: str = Field(..., description="Tên Agent đưa ra kết luận (Product, Legal, Operations)")
    claim: str = Field(..., description="Tuyên bố/kết luận cần xác minh")
    source_doc: str = Field(..., description="Tên tài liệu nguồn (ví dụ: Product_Catalog.pdf)")
    page_or_section: str = Field(..., description="Trang hoặc chương/mục chứa bằng chứng")
    quote: str = Field(..., description="Đoạn văn trích dẫn trực tiếp từ tài liệu")
    is_valid: bool = Field(default=False, description="Trạng thái xác minh của Validator")

class TaskItem(BaseModel):
    task_id: str = Field(..., description="ID của tác vụ (ví dụ: T1, T2)")
    owner: str = Field(..., description="Agent chịu trách nhiệm (Product, Legal, Operations)")
    description: str = Field(..., description="Mô tả công việc cần làm")
    status: str = Field(default="pending", description="Trạng thái tác vụ (pending, in_progress, completed, failed)")
    dependencies: List[str] = Field(default_factory=list, description="Danh sách task_id cần hoàn thành trước")

class SharedCaseState(BaseModel):
    case_id: str = Field(..., description="ID của hồ sơ vụ việc")
    customer_id: str = Field(..., description="ID của khách hàng doanh nghiệp")
    rm_id: str = Field(..., description="ID của RM phụ trách")
    customer_request: Dict[str, Any] = Field(default_factory=dict, description="Nhu cầu thô của khách hàng")
    company_profile: Dict[str, Any] = Field(default_factory=dict, description="Thông tin doanh nghiệp trích xuất được")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách hồ sơ khách hàng đã upload")
    execution_plan: List[TaskItem] = Field(default_factory=list, description="Kế hoạch thực thi do Planner lập")
    
    # Kết quả của từng Agent
    product_result: Dict[str, Any] = Field(default_factory=dict, description="Đề xuất gói sản phẩm từ Product Agent")
    legal_result: Dict[str, Any] = Field(default_factory=dict, description="Kết quả thẩm định từ Legal Agent")
    operations_result: Dict[str, Any] = Field(default_factory=dict, description="Checklist & Nháp email từ Operations Agent")
    
    # Quản lý thông tin thiếu và bằng chứng
    missing_information: List[str] = Field(default_factory=list, description="Các thông tin/tài liệu còn thiếu cần bổ sung")
    evidences: List[EvidenceItem] = Field(default_factory=list, description="Danh sách bằng chứng được xác minh")
    
    # Kiểm soát rủi ro và trạng thái duyệt
    risk_level: str = Field(default="low", description="Mức độ rủi ro (low, medium, high)")
    approval_status: str = Field(default="pending", description="Trạng thái duyệt của RM (pending, approved, rejected)")
    final_status: str = Field(default="new", description="Trạng thái của case (new, in_analysis, pending_information, completed, failed)")
    audit_log: List[Dict[str, Any]] = Field(default_factory=list, description="Nhật ký hành động chi tiết")
    trace_id: str = Field(default="", description="Correlation ID cho toàn bộ workflow")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# DTOs cho API Requests & Responses
class CreateCaseRequest(BaseModel):
    customer_id: str
    rm_id: str
    request_text: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)

class ApproveCaseRequest(BaseModel):
    rm_id: str
    comments: Optional[str] = None

class RejectCaseRequest(BaseModel):
    rm_id: str
    reason: str

class ResumeCaseRequest(BaseModel):
    rm_id: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    company_profile_updates: Dict[str, Any] = Field(default_factory=dict)
