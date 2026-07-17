"""Test fixtures for Product Agent tests."""
import pytest
import pytest_asyncio
from mcp_common.schemas import SharedCaseState, EvidenceItem


@pytest.fixture
def mock_company_profile():
    return {
        "customer_id": "COMP-ABC",
        "employees_count": 500,
        "annual_revenue": 100_000_000_000,
        "cash_flow_status": "phân tán",
        "industry": "manufacturing",
    }


@pytest.fixture
def mock_documents():
    return [
        {"type": "business_registration", "text": "Giấy đăng ký kinh doanh COMP-ABC"},
        {"type": "financial_statement", "text": "BCTC 2 năm gần nhất"},
    ]


@pytest.fixture
def sample_evidence():
    return [
        EvidenceItem(
            claim_id="EVID-001",
            agent="Product",
            claim="SHB Payroll có điều kiện: Doanh nghiệp từ 10 nhân sự",
            source_document_id="Product_Catalog.pdf",
            source_version="2025-01-01",
            section_or_page="Payroll",
            quote="Doanh nghiệp từ 10 nhân sự, có tài khoản SHB",
            validation_method="exact_match",
            is_valid=True,
        ),
        EvidenceItem(
            claim_id="EVID-002",
            agent="Product",
            claim="SHB Cash Management cho doanh nghiệp doanh thu từ 50 tỷ",
            source_document_id="Product_Catalog.pdf",
            source_version="2025-01-01",
            section_or_page="Cash_Management",
            quote="Doanh nghiệp doanh thu từ 50 tỷ VNĐ/năm",
            validation_method="exact_match",
            is_valid=True,
        ),
    ]


@pytest.fixture
def mock_case_state(mock_company_profile, mock_documents):
    return SharedCaseState(
        case_id="CORP-TEST001",
        customer_id="COMP-ABC",
        rm_id="RM-001",
        customer_request={"text": "chi lương 500 nhân viên, dòng tiền phân tán"},
        company_profile=mock_company_profile,
        documents=mock_documents,
    )


@pytest_asyncio.fixture
async def async_client():
    """Async client fixture for MCP tool calls."""
    pass