import sqlite3
import json
import os
from pathlib import Path

# Đảm bảo thư mục tồn tại
DB_PATH = Path("data/mock_database/enterprise_core.sqlite3")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Lấy dữ liệu mặc định từ các module cũ trước khi chúng bị xóa
try:
    from app.integrations.crm import _DEFAULT_DIRECTORY as CRM_DATA
except ImportError:
    CRM_DATA = {}

try:
    from app.integrations.iam import _DEFAULT_DIRECTORY as IAM_DATA
except ImportError:
    IAM_DATA = {}

try:
    from app.integrations.sso import _DEFAULT_DIRECTORY as SSO_DATA
except ImportError:
    SSO_DATA = {}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Bảng CRM Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            profile_version TEXT,
            attributes JSON
        )
    """)
    
    # Bảng SSO Employees
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            role TEXT,
            organization_unit TEXT
        )
    """)
    
    # Bảng IAM Permissions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            employee_id TEXT PRIMARY KEY,
            permissions JSON,
            access_scope JSON
        )
    """)
    
    # Clear old data
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM employees")
    cursor.execute("DELETE FROM permissions")
    
    # Insert CRM
    for cid, record in CRM_DATA.items():
        cursor.execute("INSERT INTO customers (customer_id, profile_version, attributes) VALUES (?, ?, ?)",
                       (cid, record["profile_version"], json.dumps(record["attributes"], ensure_ascii=False)))
                       
    # Insert SSO
    for eid, record in SSO_DATA.items():
        cursor.execute("INSERT INTO employees (employee_id, role, organization_unit) VALUES (?, ?, ?)",
                       (eid, record["role"], record["organization_unit"]))
                       
    # Insert IAM
    for eid, record in IAM_DATA.items():
        cursor.execute("INSERT INTO permissions (employee_id, permissions, access_scope) VALUES (?, ?, ?)",
                       (eid, json.dumps(record["permissions"], ensure_ascii=False), json.dumps(record["access_scope"], ensure_ascii=False)))
                       
    conn.commit()
    conn.close()
    print(f"Initialized Enterprise Core Database at {DB_PATH}")

if __name__ == "__main__":
    init_db()
