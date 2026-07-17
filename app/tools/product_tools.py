from typing import List, Dict, Any, Optional

# Cơ sở dữ liệu mẫu về danh mục sản phẩm của SHB hỗ trợ doanh nghiệp
SHB_PRODUCT_CATALOG: Dict[str, Dict[str, Any]] = {
    "PROD-PAYROLL": {
        "product_id": "PROD-PAYROLL",
        "name": "Dịch vụ chi trả lương doanh nghiệp (Corporate Payroll)",
        "description": "Hỗ trợ doanh nghiệp tự động chi trả lương cho nhân viên qua tài khoản SHB với mức phí ưu đãi 0đ, thời gian xử lý tức thì.",
        "benefits": ["Miễn phí chuyển tiền lương nội bộ và liên ngân hàng", "Hỗ trợ RM thiết lập file tự động", "Nhân viên nhận lương được mở thẻ ATM miễn phí"],
        "eligibility_rules": "Doanh nghiệp có số lượng nhân sự tối thiểu từ 10 người trở lên. Có đăng ký kinh doanh hợp pháp.",
        "required_documents": ["Hợp đồng dịch vụ chi lương", "Danh sách nhân viên nhận lương (mẫu SHB)", "Đăng ký kinh doanh"],
        "source_metadata": {
            "document": "SHB_Product_Catalog_2026.pdf",
            "section": "Chương III: Dịch vụ thanh toán nội địa - Mục 3.1",
            "effective_date": "2026-01-01"
        }
    },
    "PROD-CASH-MGMT": {
        "product_id": "PROD-CASH-MGMT",
        "name": "Giải pháp Quản lý dòng tiền thông minh (Cash Management)",
        "description": "Giải pháp quản lý và tối ưu hóa số dư trên nhiều tài khoản phụ của doanh nghiệp, tự động điều vốn (Cash Sweeping) về tài khoản mẹ cuối ngày.",
        "benefits": ["Tối ưu lãi suất số dư", "Tự động hóa luồng tiền thu chi hộ giữa tổng công ty và đại lý", "Báo cáo dòng tiền thời gian thực"],
        "eligibility_rules": "Doanh nghiệp có từ 3 tài khoản phụ hoặc chi nhánh/đại lý trở lên. Doanh thu năm tối thiểu từ 50 tỷ VND.",
        "required_documents": ["Thỏa thuận quản lý dòng tiền", "Đăng ký kinh doanh", "Biên bản họp Hội đồng quản trị/Hội đồng thành viên chấp thuận dịch vụ"],
        "source_metadata": {
            "document": "SHB_Cash_Management_Policy.pdf",
            "section": "Điều 12: Điều kiện áp dụng Cash Sweeping",
            "effective_date": "2025-10-15"
        }
    },
    "PROD-COLLECTION": {
        "product_id": "PROD-COLLECTION",
        "name": "Dịch vụ Thu hộ/Chi hộ doanh nghiệp (Cash Collection & Disbursal)",
        "description": "Tích hợp kênh thu hộ qua tài khoản định danh (Virtual Account) tại hệ thống quầy SHB hoặc các kênh số, giúp doanh nghiệp tự động gạch nợ hóa đơn khách hàng.",
        "benefits": ["Quản lý công nợ chính xác 100%", "Tích hợp API kết nối trực tiếp với ERP của doanh nghiệp", "Đối soát tự động hàng ngày"],
        "eligibility_rules": "Doanh nghiệp có nhu cầu thu chi khối lượng giao dịch lớn. Có hệ thống quản lý công nợ hoặc ERP kết nối.",
        "required_documents": ["Hợp đồng dịch vụ thu chi hộ", "Hồ sơ kỹ thuật kết nối API (nếu có)", "Đăng ký kinh doanh"],
        "source_metadata": {
            "document": "SHB_Transactional_Banking_Handbook.pdf",
            "section": "Phần IV: Dịch vụ thu hộ qua Virtual Account",
            "effective_date": "2026-02-01"
        }
    },
    "PROD-WORKING-CAPITAL": {
        "product_id": "PROD-WORKING-CAPITAL",
        "name": "Tài trợ Vốn lưu động Doanh nghiệp (Working Capital Financing)",
        "description": "Cấp hạn mức thấu chi hoặc cho vay ngắn hạn bổ sung vốn lưu động phục vụ sản xuất kinh doanh, thời hạn vay tối đa 12 tháng.",
        "benefits": ["Lãi suất ưu đãi cạnh tranh", "Thủ tục giải ngân nhanh trong 24 giờ sau khi phê duyệt hạn mức", "Tài sản bảo đảm linh hoạt"],
        "eligibility_rules": "Doanh nghiệp hoạt động liên tục tối thiểu 2 năm. Có báo cáo tài chính được kiểm toán hoặc báo cáo thuế năm gần nhất có lãi. Không có nợ xấu tại các tổ chức tín dụng trong 12 tháng gần nhất.",
        "required_documents": ["Báo cáo tài chính năm gần nhất", "Phương án sử dụng vốn vay", "Hồ sơ tài sản bảo đảm", "Tờ khai thuế VAT 4 quý gần nhất"],
        "source_metadata": {
            "document": "SHB_Credit_Policy_Manual.pdf",
            "section": "Chương V: Quy định cấp tín dụng ngắn hạn bổ sung vốn lưu động",
            "effective_date": "2025-12-01"
        }
    }
}

def search_product_catalog(query: str) -> List[Dict[str, Any]]:
    """
    Giả lập tìm kiếm ngữ nghĩa trong cơ sở tri thức sản phẩm của SHB.
    """
    query_lower = query.lower()
    results = []
    for prod_id, prod_info in SHB_PRODUCT_CATALOG.items():
        # Kiểm tra xem từ khóa truy vấn có khớp với mô tả hoặc tên sản phẩm không
        if (query_lower in prod_info["name"].lower() or 
            query_lower in prod_info["description"].lower() or
            any(query_lower in benefit.lower() for benefit in prod_info["benefits"])):
            results.append(prod_info)
    return results

def retrieve_product_policy(product_id: str, query: str) -> Optional[Dict[str, Any]]:
    """
    Truy xuất chính sách chi tiết và điều kiện của một sản phẩm cụ thể.
    """
    return SHB_PRODUCT_CATALOG.get(product_id)
