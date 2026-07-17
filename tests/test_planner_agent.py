from app.schemas.state import SharedCaseState, TaskItem
from app.services.planner_agent import PlannerAgent


def make_abc_state() -> SharedCaseState:
    return SharedCaseState(
        case_id="CASE-ABC",
        customer_id="COMP-ABC",
        rm_id="RM-001",
        customer_request={"text": "Mở dịch vụ Payroll và tín dụng thấu chi"},
    )


def test_abc_payroll_precedes_overdraft_legal_review():
    state = make_abc_state()
    result = PlannerAgent().create_plan(state)

    assert result.status == "planned"
    assert PlannerAgent.validate_dag(state.execution_plan) == (True, "ok")
    legal_task = next(task for task in state.execution_plan if task.owner == "Legal")
    assert legal_task.dependencies == ["T1"]
    assert result.adjacency_list[legal_task.task_id] == ["T1"]


def test_blocking_legal_feedback_pauses_and_creates_operations_checklist():
    state = make_abc_state()
    planner = PlannerAgent()
    planner.create_plan(state)

    result = planner.adapt_plan(
        state,
        legal_severity="blocking",
        missing_information=["Thông tin UBO", "Báo cáo tài chính năm gần nhất"],
    )

    assert result.status == "pending_information"
    assert state.final_status == "pending_information"
    assert "Thông tin UBO" in state.missing_information
    ops_task = next(task for task in state.execution_plan if task.task_id == "T-OPS-MISSING")
    assert ops_task.owner == "Operations"


def test_policy_conflict_escalates_to_rm_review():
    state = make_abc_state()
    planner = PlannerAgent()
    planner.create_plan(state)

    result = planner.adapt_plan(state, policy_conflict=True)

    assert result.status == "pending_review"
    assert state.final_status == "pending_review"


def test_cycle_is_detected_and_sequential_fallback_is_valid():
    tasks = [
        TaskItem(task_id="A", owner="Product", description="a", dependencies=["B"]),
        TaskItem(task_id="B", owner="Legal", description="b", dependencies=["A"]),
    ]
    assert PlannerAgent.validate_dag(tasks) == (False, "cycle")
    fallback = PlannerAgent._sequential_fallback(tasks)
    assert PlannerAgent.validate_dag(fallback) == (True, "ok")


def test_replanning_has_a_hard_limit():
    state = make_abc_state()
    planner = PlannerAgent(max_loops=1)
    planner.create_plan(state)
    planner.adapt_plan(state, policy_conflict=True)
    result = planner.adapt_plan(state, policy_conflict=True)

    assert result.status == "failed"
    assert state.final_status == "failed"

