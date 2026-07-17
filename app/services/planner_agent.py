"""Deterministic Planner Agent for the SHB corporate expert workspace.

The planner only creates and updates graph state. It does not call business
tools or make product/legal decisions. A model can be added later behind the
same contracts, but DAG validation and safety transitions remain deterministic.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional
import unicodedata

from app.schemas.state import SharedCaseState, TaskItem


MAX_REPLANNING_LOOPS = 3


@dataclass(frozen=True)
class AgentCapability:
    owner: str
    capabilities: tuple[str, ...]


DEFAULT_CAPABILITY_REGISTRY: tuple[AgentCapability, ...] = (
    AgentCapability("Product", ("product_matching", "product_policy")),
    AgentCapability("Legal", ("kyc_ubo", "eligibility", "compliance")),
    AgentCapability("Operations", ("missing_information", "crm_draft")),
    AgentCapability("Validator", ("evidence_validation", "plan_validation")),
)


@dataclass
class PlannerMetrics:
    plans_created: int = 0
    valid_plans: int = 0
    replanning_steps: int = 0

    @property
    def plan_validity_rate(self) -> float:
        return self.valid_plans / self.plans_created if self.plans_created else 0.0

    @property
    def average_replanning_steps(self) -> float:
        return self.replanning_steps / self.plans_created if self.plans_created else 0.0


@dataclass
class PlannerResult:
    execution_plan: List[TaskItem]
    status: str
    reason: str = ""
    adjacency_list: Dict[str, List[str]] = field(default_factory=dict)


class PlannerAgent:
    """Build and adapt an execution DAG for a corporate case."""

    def __init__(
        self,
        capability_registry: Iterable[AgentCapability] = DEFAULT_CAPABILITY_REGISTRY,
        max_loops: int = MAX_REPLANNING_LOOPS,
    ) -> None:
        self.capability_registry = {item.owner: item for item in capability_registry}
        self.max_loops = max_loops
        self.metrics = PlannerMetrics()

    def create_plan(self, state: SharedCaseState) -> PlannerResult:
        """Create a valid plan from case context without exposing private reasoning."""
        self.metrics.plans_created += 1
        request = self._request_text(state.customer_request)
        wants_payroll = self._contains_any(request, "payroll", "chi lương", "trả lương")
        wants_credit = self._contains_any(
            request, "thấu chi", "vốn lưu động", "tín dụng", "cho vay", "credit"
        )

        tasks: List[TaskItem] = []
        if wants_payroll or not wants_credit:
            tasks.append(
                TaskItem(
                    task_id="T1",
                    owner="Product",
                    description="Tìm và đối chiếu giải pháp thanh toán/chi lương phù hợp.",
                )
            )
        if wants_credit:
            dependencies = ["T1"] if wants_payroll else []
            tasks.append(
                TaskItem(
                    task_id=f"T{len(tasks) + 1}",
                    owner="Legal",
                    description="Thẩm định KYC/UBO và điều kiện pháp lý cho nhu cầu tín dụng.",
                    dependencies=dependencies,
                )
            )

        validator_dependencies = [task.task_id for task in tasks]
        tasks.append(
            TaskItem(
                task_id=f"T{len(tasks) + 1}",
                owner="Validator",
                description="Kiểm tra bằng chứng, tính đầy đủ và tính hợp lệ của kết quả.",
                dependencies=validator_dependencies,
            )
        )
        tasks.append(
            TaskItem(
                task_id=f"T{len(tasks) + 1}",
                owner="Operations",
                description="Tổng hợp checklist, brief và bản nháp tác vụ/email theo kết quả xác minh.",
                dependencies=[tasks[-1].task_id],
            )
        )

        validation = self.validate_dag(tasks)
        if not validation[0]:
            tasks = self._sequential_fallback(tasks)
            reason = "Phát hiện chu kỳ phụ thuộc; đã chuyển sang kế hoạch tuần tự mặc định."
        else:
            reason = "Kế hoạch DAG hợp lệ được tạo từ yêu cầu và capability registry."
        self.metrics.valid_plans += 1
        state.execution_plan = tasks
        state.final_status = "in_analysis"
        self._audit(state, "planner.create_plan", reason, tasks)
        return PlannerResult(tasks, "planned", reason, self.adjacency_list(tasks))

    def adapt_plan(
        self,
        state: SharedCaseState,
        *,
        legal_severity: Optional[str] = None,
        policy_conflict: bool = False,
        missing_information: Optional[Iterable[str]] = None,
    ) -> PlannerResult:
        """Apply deterministic safety transitions after specialist feedback."""
        self.metrics.replanning_steps += 1
        if self.metrics.replanning_steps > self.max_loops:
            state.final_status = "failed"
            reason = f"Đã vượt giới hạn {self.max_loops} vòng điều chỉnh kế hoạch."
            self._audit(state, "planner.stop", reason)
            return PlannerResult(state.execution_plan, "failed", reason, self.adjacency_list(state.execution_plan))

        if policy_conflict:
            state.final_status = "pending_review"
            state.approval_status = "pending"
            reason = "Xung đột chính sách Product/Legal; chuyển RM review."
            self._audit(state, "planner.escalate", reason)
            return PlannerResult(state.execution_plan, "pending_review", reason, self.adjacency_list(state.execution_plan))

        if (legal_severity or "").lower() == "blocking":
            items = [item for item in (missing_information or []) if item]
            state.missing_information = list(dict.fromkeys([*state.missing_information, *items]))
            for task in state.execution_plan:
                if task.owner == "Legal" and task.status == "pending":
                    task.status = "failed"
            existing = {task.task_id for task in state.execution_plan}
            if "T-OPS-MISSING" not in existing:
                state.execution_plan.append(
                    TaskItem(
                        task_id="T-OPS-MISSING",
                        owner="Operations",
                        description="Soạn checklist thông tin thiếu và email nháp cho RM duyệt.",
                        dependencies=["T1"] if "T1" in existing else [],
                    )
                )
            state.final_status = "pending_information"
            reason = "Legal báo Blocking; tạm dừng luồng rủi ro và chuyển Operations lập checklist thiếu."
            self._audit(state, "planner.pause_blocking", reason)
            return PlannerResult(state.execution_plan, "pending_information", reason, self.adjacency_list(state.execution_plan))

        reason = "Không có tín hiệu cần điều chỉnh; giữ nguyên kế hoạch."
        self._audit(state, "planner.noop", reason)
        return PlannerResult(state.execution_plan, "planned", reason, self.adjacency_list(state.execution_plan))

    @staticmethod
    def validate_dag(tasks: Iterable[TaskItem]) -> tuple[bool, str]:
        task_list = list(tasks)
        ids = {task.task_id for task in task_list}
        if len(ids) != len(task_list):
            return False, "duplicate_task_id"
        graph = {task.task_id: list(task.dependencies) for task in task_list}
        if any(dep not in ids for deps in graph.values() for dep in deps):
            return False, "unknown_dependency"
        indegree = {task_id: 0 for task_id in ids}
        children: Dict[str, List[str]] = defaultdict(list)
        for task_id, deps in graph.items():
            indegree[task_id] = len(deps)
            for dep in deps:
                children[dep].append(task_id)
        queue = deque(task_id for task_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        return visited == len(ids), "ok" if visited == len(ids) else "cycle"

    @staticmethod
    def adjacency_list(tasks: Iterable[TaskItem]) -> Dict[str, List[str]]:
        return {task.task_id: list(task.dependencies) for task in tasks}

    @staticmethod
    def _sequential_fallback(tasks: List[TaskItem]) -> List[TaskItem]:
        previous: Optional[str] = None
        result: List[TaskItem] = []
        for task in tasks:
            task.dependencies = [previous] if previous else []
            result.append(task)
            previous = task.task_id
        return result

    @staticmethod
    def _request_text(request: Any) -> str:
        if isinstance(request, Mapping):
            return " ".join(str(value) for value in request.values()).lower()
        return str(request or "").lower()

    @staticmethod
    def _contains_any(text: str, *terms: str) -> bool:
        def fold(value: str) -> str:
            decomposed = unicodedata.normalize("NFD", value.lower())
            return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("đ", "d")

        folded_text = fold(text)
        return any(fold(term) in folded_text for term in terms)

    @staticmethod
    def _audit(state: SharedCaseState, action: str, reason: str, tasks: Optional[List[TaskItem]] = None) -> None:
        event: Dict[str, Any] = {"action": action, "reason": reason}
        if tasks is not None:
            event["adjacency_list"] = PlannerAgent.adjacency_list(tasks)
        state.audit_log.append(event)
