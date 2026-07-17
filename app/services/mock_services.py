import logging
from typing import Dict, Any, List, Optional
import uuid

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_services")

# Mock Database của Core Banking / CRM
MOCK_COMPANIES: Dict[str, Dict[str, Any]] = {
    "COMP-ABC": {
        "company_id": "COMP-ABC",
        "name": "Công ty Cổ phần ABC Việt Nam",
        "tax_code": "0102030405",
        "business_type": "Cổ phần",
        "industry": "Sản xuất hàng tiêu dùng",
        "employees_count": 500,
        "annual_revenue": 120000000000,  # 120 tỷ VND
        "cash_flow_status": "Dòng tiền phân tán qua nhiều tài khoản phụ",
        "representatives": [
            {
                "name": "Nguyễn Văn A",
                "role": "Tổng Giám đốc",
                "id_card": "012345678901",
                "authority_limit": 5000000000,  # Hạn mức ủy quyền 5 tỷ
                "is_active": True
            }
        ],
        "ubo_status": "Chưa xác minh đầy đủ",  # Thiếu thông tin UBO
        "financial_reports": {
            "has_recent": False,  # Thiếu báo cáo tài chính năm gần nhất
            "last_year_available": 2024
        }
    },
    "COMP-XYZ": {
        "company_id": "COMP-XYZ",
        "name": "Công ty TNHH XYZ Logistics",
        "tax_code": "0908070605",
        "business_type": "TNHH Hai thành viên trở lên",
        "industry": "Vận tải và Kho bãi",
        "employees_count": 80,
        "annual_revenue": 45000000000,  # 45 tỷ VND
        "cash_flow_status": "Tập trung tại một tài khoản chính",
        "representatives": [
            {
                "name": "Trần Thị B",
                "role": "Giám đốc",
                "id_card": "098765432109",
                "authority_limit": 2000000000,
                "is_active": True
            }
        ],
        "ubo_status": "Đầy đủ",  # Đã có UBO
        "financial_reports": {
            "has_recent": True,
            "last_year_available": 2025
        }
    }
}

class CoreBankingService:
    @staticmethod
    def get_company_profile(company_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[CoreBanking] API Call: Lấy hồ sơ công ty {company_id}")
        return MOCK_COMPANIES.get(company_id)

class CRMService:
    @staticmethod
    def create_case(case_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[CRM] API Call: Tạo case thành công trong hệ thống CRM cho case_id {case_id}")
        return {
            "crm_case_id": f"CRM-CASE-{uuid.uuid4().hex[:6].upper()}",
            "status": "created",
            "case_id": case_id,
            "data": payload
        }

    @staticmethod
    def create_task(case_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[CRM] API Call: Tạo task trong CRM cho case_id {case_id} - Giao cho: {task.get('owner')}")
        return {
            "crm_task_id": f"CRM-TASK-{uuid.uuid4().hex[:6].upper()}",
            "status": "assigned",
            "case_id": case_id,
            "task": task
        }

class EmailService:
    @staticmethod
    def send_draft_email(recipient: str, subject: str, body: str) -> bool:
        logger.info(f"[Email] API Call: Lưu email nháp gửi tới {recipient}")
        logger.info(f"[Email] Tiêu đề: {subject}")
        logger.info(f"[Email] Nội dung nháp:\n{body}\n--------------------")
        return True
