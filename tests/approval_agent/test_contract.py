"""Contract tests for Approval Agent."""

import pytest
from servers.approval_agent.server import issue_token, verify_token, health_check


class TestApprovalAgentContract:
    @pytest.mark.asyncio
    async def test_app_01_issue_token_returns_hmac_signed(self):
        """APP-01: issue_token returns HMAC-signed token."""
        result = await issue_token({
            "case_id": "CASE-001",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case", "data": {}}
        })
        assert "token" in result
        assert "expires_in" in result
        assert result["expires_in"] == 300

    @pytest.mark.asyncio
    async def test_app_02_verify_token_valid(self):
        """APP-02: verify_token validates correct token."""
        issue = await issue_token({
            "case_id": "CASE-002",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case", "data": {}}
        })
        verify = await verify_token({
            "token": issue["token"],
            "case_id": "CASE-002",
            "rm_id": "RM-001",
            "payload": {"action": "create_case", "data": {}}
        })
        assert verify["valid"] is True
        assert "token_id" in verify

    @pytest.mark.asyncio
    async def test_app_03_verify_wrong_case_rejected(self):
        """APP-03: Wrong case_id rejected."""
        issue = await issue_token({
            "case_id": "CASE-A",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case"}
        })
        verify = await verify_token({
            "token": issue["token"],
            "case_id": "CASE-B",
            "rm_id": "RM-001",
            "payload": {"action": "create_case"}
        })
        assert verify["valid"] is False
        assert verify["reason"] == "CASE_ID_MISMATCH"

    @pytest.mark.asyncio
    async def test_app_04_verify_wrong_rm_rejected(self):
        """APP-04: Wrong RM rejected."""
        issue = await issue_token({
            "case_id": "CASE-003",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case"}
        })
        verify = await verify_token({
            "token": issue["token"],
            "case_id": "CASE-003",
            "rm_id": "RM-002",
            "payload": {"action": "create_case"}
        })
        assert verify["valid"] is False
        assert verify["reason"] == "APPROVER_MISMATCH"

    @pytest.mark.asyncio
    async def test_app_05_verify_tampered_payload_rejected(self):
        """APP-05: Tampered payload rejected."""
        issue = await issue_token({
            "case_id": "CASE-004",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case", "amount": 100}
        })
        verify = await verify_token({
            "token": issue["token"],
            "case_id": "CASE-004",
            "rm_id": "RM-001",
            "payload": {"action": "create_case", "amount": 999999}
        })
        assert verify["valid"] is False
        assert verify["reason"] == "PAYLOAD_MISMATCH"

    @pytest.mark.asyncio
    async def test_app_06_verify_reused_token_rejected(self):
        """APP-06: Reused one-time token rejected."""
        issue = await issue_token({
            "case_id": "CASE-005",
            "rm_id": "RM-001",
            "permissions": ["create_crm_case"],
            "payload": {"action": "create_case"}
        })
        # First use
        await verify_token({
            "token": issue["token"],
            "case_id": "CASE-005",
            "rm_id": "RM-001",
            "payload": {"action": "create_case"}
        })
        # Second use should fail
        verify = await verify_token({
            "token": issue["token"],
            "case_id": "CASE-005",
            "rm_id": "RM-001",
            "payload": {"action": "create_case"}
        })
        assert verify["valid"] is False
        assert verify["reason"] == "TOKEN_ALREADY_USED"

    @pytest.mark.asyncio
    async def test_health_check(self):
        result = await health_check()
        assert result["status"] == "ok"
        assert result["service"] == "approval-agent"