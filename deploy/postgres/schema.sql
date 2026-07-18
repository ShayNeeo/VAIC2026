-- ============================================================================
-- SHB Corporate Expert Workspace — PostgreSQL deployment schema
-- Target: PostgreSQL 17 on VPS (sgp1.w9.nu), port 5432
-- Applied by: tools/seed_postgres_enterprise.py (idempotent)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- GROUP 1: CORPORATE KYC & LEGAL INFORMATION (full KYC source-of-truth)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bank_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    product_type VARCHAR(100) NOT NULL,
    description TEXT,
    target_segment VARCHAR(100),
    key_features VARCHAR(255),
    prerequisites VARCHAR(255),
    supported_currencies VARCHAR(50),
    minimum_revenue_vnd NUMERIC(20, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated'))
);

CREATE TABLE IF NOT EXISTS companies (
    tax_id VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    established_date DATE NOT NULL,
    legal_form VARCHAR(100) NOT NULL CHECK (legal_form IN (
        'Công ty TNHH 1 thành viên',
        'Công ty TNHH 2 thành viên trở lên',
        'Công ty Cổ phần',
        'Doanh nghiệp tư nhân',
        'Công ty Hợp danh',
        'Khác'
    )),
    registered_address TEXT NOT NULL,
    business_address TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Đang hoạt động' CHECK (status IN (
        'Đang hoạt động',
        'Tạm ngừng hoạt động',
        'Đã giải thể',
        'Chờ làm thủ tục phá sản'
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS representatives (
    representative_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    national_id VARCHAR(20) NOT NULL,
    role_type VARCHAR(100) NOT NULL CHECK (role_type IN (
        'Người đại diện pháp luật',
        'Kế toán trưởng',
        'Tổng Giám đốc',
        'Giám đốc',
        'Chủ tịch HĐQT'
    )),
    date_of_birth DATE,
    phone VARCHAR(20),
    email VARCHAR(100),
    verification_status VARCHAR(50) DEFAULT 'Chưa xác minh' CHECK (verification_status IN ('Đã xác minh', 'Chờ bổ sung tài liệu', 'Chưa xác minh')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business_operations (
    operation_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) UNIQUE REFERENCES companies(tax_id) ON DELETE CASCADE,
    vsic_code VARCHAR(10) NOT NULL,
    industry_name VARCHAR(255) NOT NULL,
    core_business_desc TEXT NOT NULL,
    employee_count INT NOT NULL DEFAULT 0,
    branch_count INT DEFAULT 0,
    factory_count INT DEFAULT 0,
    factory_locations TEXT,
    years_in_industry INT DEFAULT 0,
    last_license_change_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_health (
    financial_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    fiscal_year INT NOT NULL,
    is_audited BOOLEAN DEFAULT FALSE,
    total_assets NUMERIC(20, 2) NOT NULL,
    equity NUMERIC(20, 2) NOT NULL,
    inventory NUMERIC(20, 2) NOT NULL DEFAULT 0,
    receivables NUMERIC(20, 2) NOT NULL DEFAULT 0,
    payables NUMERIC(20, 2) NOT NULL DEFAULT 0,
    net_revenue NUMERIC(20, 2) NOT NULL,
    gross_profit NUMERIC(20, 2) NOT NULL,
    net_profit_after_tax NUMERIC(20, 2) NOT NULL,
    ebit NUMERIC(20, 2),
    ebitda NUMERIC(20, 2),
    current_ratio NUMERIC(10, 4),
    quick_ratio NUMERIC(10, 4),
    de_ratio NUMERIC(10, 4),
    net_profit_margin NUMERIC(10, 4),
    roa NUMERIC(10, 4),
    roe NUMERIC(10, 4),
    CONSTRAINT unique_financial_year UNIQUE (tax_id, fiscal_year)
);

CREATE TABLE IF NOT EXISTS cic_risk_profiles (
    risk_profile_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) UNIQUE REFERENCES companies(tax_id) ON DELETE CASCADE,
    cic_score INT CHECK (cic_score BETWEEN 0 AND 1000),
    cic_debt_group INT NOT NULL CHECK (cic_debt_group BETWEEN 1 AND 5),
    outstanding_short_term NUMERIC(20, 2) DEFAULT 0,
    outstanding_medium_term NUMERIC(20, 2) DEFAULT 0,
    outstanding_long_term NUMERIC(20, 2) DEFAULT 0,
    npl_history_12m BOOLEAN DEFAULT FALSE,
    npl_history_3y BOOLEAN DEFAULT FALSE,
    npl_history_5y BOOLEAN DEFAULT FALSE,
    credit_card_limit NUMERIC(20, 2) DEFAULT 0,
    credit_card_outstanding NUMERIC(20, 2) DEFAULT 0,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collaterals (
    collateral_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    asset_name VARCHAR(255) NOT NULL,
    collateral_type VARCHAR(100) NOT NULL CHECK (collateral_type IN (
        'Bất động sản',
        'Máy móc & Thiết bị',
        'Quyền đòi nợ',
        'Phương tiện vận tải',
        'Tiền gửi/Giấy tờ có giá',
        'Khác'
    )),
    valuation_amount NUMERIC(20, 2) NOT NULL,
    valuation_date DATE NOT NULL,
    remarks TEXT
);

CREATE TABLE IF NOT EXISTS ownership_structure (
    ownership_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    shareholder_name VARCHAR(255) NOT NULL,
    national_id_or_tax_id VARCHAR(50),
    ownership_percentage NUMERIC(5, 2) NOT NULL CHECK (ownership_percentage BETWEEN 0 AND 100),
    is_major_shareholder BOOLEAN GENERATED ALWAYS AS (ownership_percentage >= 5.0) STORED
);

CREATE TABLE IF NOT EXISTS corporate_relationships (
    relationship_id SERIAL PRIMARY KEY,
    parent_tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    child_tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL CHECK (relationship_type IN (
        'Công ty mẹ - Công ty con',
        'Công ty liên kết',
        'Cùng nhóm lợi ích'
    )),
    ownership_percentage NUMERIC(5, 2) CHECK (ownership_percentage BETWEEN 0 AND 100),
    CONSTRAINT unique_relationship UNIQUE (parent_tax_id, child_tax_id)
);

CREATE TABLE IF NOT EXISTS supply_chain_partners (
    partner_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    partner_name VARCHAR(255) NOT NULL,
    partner_type VARCHAR(20) NOT NULL CHECK (partner_type IN ('Supplier', 'Buyer')),
    transaction_volume_annual NUMERIC(20, 2),
    revenue_or_cost_share_pct NUMERIC(5, 2) CHECK (revenue_or_cost_share_pct BETWEEN 0 AND 100),
    description TEXT
);

CREATE TABLE IF NOT EXISTS transaction_behavior (
    behavior_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) UNIQUE REFERENCES companies(tax_id) ON DELETE CASCADE,
    casa_avg_balance_3m NUMERIC(20, 2) NOT NULL DEFAULT 0,
    casa_avg_balance_12m NUMERIC(20, 2) NOT NULL DEFAULT 0,
    txn_frequency_in_3m INT DEFAULT 0,
    txn_frequency_out_3m INT DEFAULT 0,
    repayment_history VARCHAR(50) NOT NULL CHECK (repayment_history IN (
        'Hoàn hảo',
        'Trễ hạn nhẹ (1-2 ngày)',
        'Nợ xấu / Quá hạn thường xuyên'
    )),
    last_transaction_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_products (
    subscription_id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    product_id VARCHAR(50) REFERENCES bank_products(product_id) ON DELETE RESTRICT,
    registration_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending', 'terminated')),
    approved_limit NUMERIC(20, 2) DEFAULT 0,
    interest_rate_applied NUMERIC(5, 2),
    CONSTRAINT unique_customer_product UNIQUE (tax_id, product_id)
);

CREATE TABLE IF NOT EXISTS company_transaction_history (
    transaction_id VARCHAR(50) PRIMARY KEY,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    partner_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    debit_amount NUMERIC(20, 2) DEFAULT 0,
    credit_amount NUMERIC(20, 2) DEFAULT 0,
    running_balance NUMERIC(20, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS corporate_credit_requests (
    request_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(20) REFERENCES companies(tax_id) ON DELETE CASCADE,
    requested_amount_vnd NUMERIC(20, 2) NOT NULL,
    collateral_value_billion_vnd NUMERIC(20, 2),
    cic_debt_classification VARCHAR(50),
    debt_to_equity_ratio NUMERIC(10, 4),
    casa_avg_balance_billion_vnd NUMERIC(20, 2),
    requested_term_months INT,
    proposed_interest_rate NUMERIC(5, 2),
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- MIRROR TABLES — keep the legacy SQLite adapter shape so the FastAPI app
-- keeps working unchanged. These expose the pilot demo cast (COMP-MP + the
-- six employee personas) to the PostgreSQL CRM/IAM/SSO adapters.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    profile_version VARCHAR(20) NOT NULL,
    attributes JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    employee_id VARCHAR(50) PRIMARY KEY,
    permissions JSONB NOT NULL,
    access_scope JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    role VARCHAR(100) NOT NULL,
    organization_unit VARCHAR(255) NOT NULL
);
