"""Seed the VPS PostgreSQL instance for the SHB Corporate Expert Workspace.

Idempotent: applies deploy/postgres/schema.sql, then upserts the pilot demo
cast (COMP-MP customer + the six employee personas) into the mirror tables
the FastAPI PostgreSQL adapters read, plus a sample KYC `companies` row so the
richer schema is populated and exercised.

Usage:
    DATABASE_URL=postgresql://postgres:...@127.0.0.1:5432/vaic \\
        python tools/seed_postgres_enterprise.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.integrations.pg import EMPLOYEE_COPILOT_DEMO_PERSONAS  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "deploy" / "postgres" / "schema.sql"


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fall back to the VPS-local Postgres defaults.
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:Thanh1010.@127.0.0.1:5432/vaic",
        )

    import psycopg2

    conn = psycopg2.connect(database_url, connect_timeout=10)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

            # --- Mirror: employees + permissions (the six personas) ---
            for employee_id, role, org_unit, permissions, access_scope in EMPLOYEE_COPILOT_DEMO_PERSONAS:
                cur.execute(
                    """
                    INSERT INTO employees (employee_id, role, organization_unit)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id) DO UPDATE SET
                        role = excluded.role,
                        organization_unit = excluded.organization_unit
                    """,
                    (employee_id, role, org_unit),
                )
                cur.execute(
                    """
                    INSERT INTO permissions (employee_id, permissions, access_scope)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id) DO UPDATE SET
                        permissions = excluded.permissions,
                        access_scope = excluded.access_scope
                    """,
                    (employee_id, json.dumps(permissions), json.dumps(access_scope)),
                )

            # RM-999 already exists in the SQLite seed; mirror it here too so
            # SSO/IAM resolve consistently in Postgres-only deployments.
            cur.execute(
                """
                INSERT INTO employees (employee_id, role, organization_unit)
                VALUES ('RM-999', 'RM', 'Corporate Banking HN')
                ON CONFLICT (employee_id) DO UPDATE SET
                    role = excluded.role,
                    organization_unit = excluded.organization_unit
                """
            )
            cur.execute(
                """
                INSERT INTO permissions (employee_id, permissions, access_scope)
                VALUES ('RM-999', %s, %s)
                ON CONFLICT (employee_id) DO UPDATE SET
                    permissions = excluded.permissions,
                    access_scope = excluded.access_scope
                """,
                (
                    json.dumps(["case:read", "case:write", "approval:request"]),
                    json.dumps({"managed_customer_ids": ["COMP-ABC", "COMP-MP", "COMP-XYZ"], "branch": "HN01"}),
                ),
            )

            # --- Mirror: COMP-MP customer profile ---
            comp_mp = {
                "company_name": "Công ty TNHH Minh Phát",
                "tax_id": "COMP-MP",
                "legal_form": "Công ty TNHH 2 thành viên trở lên",
                "industry": "Sản xuất & Thương mại",
                "segment": "SME Corporate",
                "status": "Đang hoạt động",
            }
            cur.execute(
                """
                INSERT INTO customers (customer_id, profile_version, attributes)
                VALUES ('COMP-MP', 'v1', %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    profile_version = excluded.profile_version,
                    attributes = excluded.attributes
                """,
                (json.dumps(comp_mp),),
            )

            # --- KYC sample row so the rich schema is populated ---
            cur.execute(
                """
                INSERT INTO companies (
                    tax_id, company_name, established_date, legal_form,
                    registered_address, business_address, status
                ) VALUES ('COMP-MP', 'Công ty TNHH Minh Phát', '2015-03-12',
                    'Công ty TNHH 2 thành viên trở lên',
                    'Số 1, Nguyễn Chí Thanh, Hà Nội', 'Số 1, Nguyễn Chí Thanh, Hà Nội',
                    'Đang hoạt động')
                ON CONFLICT (tax_id) DO NOTHING
                """
            )

        conn.commit()
        print("OK: schema applied + pilot demo cast seeded into PostgreSQL.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
