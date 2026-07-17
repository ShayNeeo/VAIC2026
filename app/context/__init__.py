"""V2-002: employee/workspace/customer/conversation context services.

Each service returns exactly one piece of app.schemas.v2.context_snapshot
(Employee, Workspace, Customer, Conversation) with correct provenance,
freshness and RBAC handling. Merging these into one ContextSnapshot with
precedence rules, conflict detection and minimization is V2-003 (Context
Assembler) -- deliberately not implemented here, see
plan_v2/14_BUILD_ORDER.md V2-002 vs V2-003.
"""
