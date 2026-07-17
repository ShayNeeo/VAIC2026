> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 573-696). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 22. Tool Registry
`[PROPOSED DESIGN]`

Các công cụ được khai báo và quản lý tập trung để kiểm soát quyền hạn gọi API:

| Tên Tool | Agent được gọi | Mô tả chức năng | Tham số đầu vào (Schema) | Kết quả đầu ra (Schema) | Trạng thái tích hợp |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `search_product_catalog` | Product Agent | Tìm kiếm sản phẩm tài chính | `{"query": "string"}` | `[{"product_id": "str", "name": "str"}]` | `SYNTHETIC MOCK API` |
| `retrieve_product_policy` | Product Agent | Lấy chính sách sản phẩm chi tiết | `{"product_id": "str"}` | `{"rules": "str", "source": "str"}` | `SYNTHETIC MOCK API` |
| `validate_business_registration` | Legal Agent | Xác thực đăng ký kinh doanh | `{"document_id": "str"}` | `{"status": "str", "tax_code": "str"}` | `SYNTHETIC MOCK API` |
| `check_document_expiry` | Legal Agent | Kiểm tra hạn hiệu lực hồ sơ | `{"expiry_date": "str"}` | `{"is_expired": "bool", "days_left": "int"}` | `SYNTHETIC MOCK API` |
| `check_product_eligibility` | Legal Agent | Kiểm tra điều kiện pháp lý giải pháp | `{"product_id": "str", "profile": "obj"}` | `{"eligible": "bool", "reason": "str"}` | `SYNTHETIC MOCK API` |
| `search_compliance_policy` | Legal Agent | Tra cứu luật & quy chế tuân thủ | `{"query": "string"}` | `{"articles": "arr", "citation": "str"}` | `SYNTHETIC MOCK API` |
| `get_required_documents` | Operations Agent | Lấy danh mục hồ sơ bắt buộc theo SOP | `{"product_ids": "array"}` | `{"required_docs": "array"}` | `SYNTHETIC MOCK API` |
| `create_case` | Operations Agent | Khởi tạo Case trên CRM sau phê duyệt | `{"case_data": "object"}` | `{"crm_case_id": "str", "status": "str"}` | `PRODUCTION API REQUIRED FROM SHB` |
| `create_followup_task` | Operations Agent | Tạo task nghiệp vụ cho RM | `{"task_data": "object"}` | `{"crm_task_id": "str", "status": "str"}` | `PRODUCTION API REQUIRED FROM SHB` |

---

## 23. Shared State
`[PROPOSED DESIGN]`

Shared State là trung tâm lưu trữ thông tin của phiên làm việc đồ thị Multi-Agent. Dưới đây là đặc tả các trường dữ liệu quan trọng:

```json
{
  "case_id": "CORP-2026-001",
  "rm_id": "RM-999",
  "customer_id": "CUST-ABC",
  "customer_request": {
    "text": "Doanh nghiệp muốn mở gói tài khoản chi lương và xin thấu chi vốn lưu động ngắn hạn.",
    "timestamp": "2026-07-17T16:10:00Z"
  },
  "company_profile": {
    "name": "Công ty Cổ phần ABC Việt Nam",
    "tax_code": "0102030405",
    "employees_count": 500,
    "annual_revenue": 120000000000
  },
  "documents": [
    {
      "doc_id": "DOC-001",
      "doc_type": "Giấy chứng nhận ĐKDN",
      "issue_date": "2020-05-12",
      "expiry_date": "none",
      "status": "verified"
    }
  ],
  "execution_plan": [
    {
      "task_id": "T1",
      "owner": "Product Agent",
      "description": "Tư vấn gói giải pháp sản phẩm phù hợp cho Công ty ABC",
      "status": "completed",
      "dependencies": []
    },
    {
      "task_id": "T2",
      "owner": "Legal Agent",
      "description": "Thẩm định tính pháp lý và KYC/UBO của khách hàng",
      "status": "completed",
      "dependencies": []
    }
  ],
  "product_result": {
    "recommended_products": ["PROD-PAYROLL", "PROD-WORKING-CAPITAL"],
    "bundle_name": "Gói thanh toán lương & Tài trợ vốn ngắn hạn",
    "match_score": 0.92
  },
  "legal_result": {
    "eligibility_status": "pending_info",
    "failed_checks": [
      {
        "rule_id": "RULE-UBO",
        "reason": "Thiếu thông tin chủ sở hữu hưởng lợi cuối cùng (UBO)",
        "severity": "blocking"
      }
    ],
    "missing_documents": ["Tờ khai thông tin chủ sở hữu hưởng lợi UBO"]
  },
  "operations_result": {
    "proposed_tasks": [
      {
        "task_description": "Thu thập thông tin UBO từ khách hàng ABC",
        "assigned_team": "RM-999",
        "sla_hours": 24
      }
    ],
    "customer_email_draft": {
      "subject": "[SHB] Yêu cầu bổ sung hồ sơ mở dịch vụ doanh nghiệp - Công ty ABC",
      "body": "Kính gửi Quý khách hàng, Để hoàn tất hồ sơ mở dịch vụ..."
    }
  },
  "missing_information": [
    "Thông tin chủ sở hữu hưởng lợi cuối cùng (UBO)",
    "Báo cáo tài chính năm 2025 (năm gần nhất)"
  ],
  "evidences": [
    {
      "agent": "Product Agent",
      "claim": "Dịch vụ Payroll áp dụng cho doanh nghiệp từ 10 nhân sự trở lên",
      "source_doc": "SHB_Product_Catalog_2026.pdf",
      "page_or_section": "Mục 3.1",
      "quote": "Doanh nghiệp có số lượng nhân sự tối thiểu từ 10 người trở lên.",
      "is_valid": true
    }
  ],
  "risk_level": "medium",
  "approval_status": "pending",
  "final_status": "pending_information",
  "audit_events": [
    {
      "event_id": "EVT-1002",
      "timestamp": "2026-07-17T16:11:15Z",
      "actor": "Legal Agent",
      "action": "check_beneficial_owner",
      "result": "missing_ubo_flagged"
    }
  ]
}
```

---

