"""Deterministic execution planning and Legal-result re-planning."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.schemas.v2.planning import ExecutionPlan, PlanStep


class PlannerService:
    def plan(self, *, snapshot: Dict[str, Any] | None, user_goal: str) -> ExecutionPlan:
        goals = list((snapshot or {}).get("explicit_needs") or [])
        if not goals:
            goals = [user_goal]
        return ExecutionPlan(
            plan_version=1,
            goals=[str(item) for item in goals],
            steps=self._base_steps(),
            changed_because=None,
            created_at=datetime.now(timezone.utc),
        )

    def replan(
        self,
        previous: Dict[str, Any] | None,
        *,
        eligibility_result: Dict[str, Any],
    ) -> ExecutionPlan:
        current = ExecutionPlan.model_validate(previous) if previous else self.plan(snapshot=None, user_goal="Xử lý nhu cầu")
        outcome = str(eligibility_result.get("overall_status") or "pending_review")
        steps: List[PlanStep] = [item.model_copy(deep=True) for item in current.steps]
        if outcome == "passed":
            for step in steps:
                if step.step_id in {"compliance", "replan"}:
                    step.status = "completed"
                elif step.step_id in {"operations", "approval"}:
                    step.status = "ready"
            reason = "Compliance/Eligibility đã đủ điều kiện; mở bước chuẩn bị và RM approval."
        elif outcome == "pending_information":
            for step in steps:
                if step.step_id == "compliance":
                    step.status = "blocked"
                elif step.step_id == "replan":
                    step.status = "completed"
                elif step.step_id == "operations":
                    step.status = "ready"
                    step.title = "Tạo checklist và discovery task, chưa tạo opportunity-ready payload"
                elif step.step_id == "approval":
                    step.status = "blocked"
            reason = "Compliance/Eligibility thiếu dữ liệu; giữ các nhánh an toàn và chặn phê duyệt."
        else:
            for step in steps:
                if step.step_id == "compliance":
                    step.status = "blocked"
                elif step.step_id == "replan":
                    step.status = "completed"
                elif step.step_id == "operations":
                    step.status = "ready"
                    step.title = "Chuẩn bị phương án thay thế/escalation có evidence"
                elif step.step_id == "approval":
                    step.status = "blocked"
            reason = "Compliance/Eligibility không cho phép tiếp tục tự động; chuyển review/escalation."
        return ExecutionPlan(
            plan_version=current.plan_version + 1,
            goals=current.goals,
            steps=steps,
            changed_because=reason,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _base_steps() -> List[PlanStep]:
        return [
            PlanStep(step_id="product", title="Tìm và xếp hạng bundle sản phẩm", owner="Product", status="ready", reason="Cần giải pháp có trong catalog"),
            PlanStep(step_id="compliance", title="Kiểm tra rule và bằng chứng tuân thủ", owner="Compliance", status="pending", dependencies=["product"], reason="Không giao pass/fail cho LLM", stop_condition="Thiếu dữ liệu hoặc rule blocking"),
            PlanStep(step_id="replan", title="Điều chỉnh kế hoạch theo kết quả Compliance", owner="Planner", status="pending", dependencies=["compliance"], reason="Giữ nhánh an toàn và loại nhánh bị chặn"),
            PlanStep(step_id="operations", title="Chuẩn bị checklist, phản hồi và action draft", owner="Operations", status="pending", dependencies=["replan"], reason="Không tạo side effect thật"),
            PlanStep(step_id="approval", title="RM kiểm tra và phê duyệt payload", owner="RM", status="pending", dependencies=["operations"], reason="Hành động thay đổi hệ thống cần con người duyệt"),
        ]

