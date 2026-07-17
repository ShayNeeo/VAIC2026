# Kế hoạch Build Song Song — Git Worktree (PLAN, chưa execute)

> Dùng mô hình **German 3-Layer** + `git worktree` cho mỗi Work Package (WP) độc lập.
> Mục tiêu: build MCP workspace toàn bộ mà không conflict, mỗi agent = 1 worktree.

---

## 1. Cấu trúc Worktree

Base branch: `main`. Mỗi WP = 1 worktree + 1 branch `feat/wp<N>-<name>`.

```
../wt-wp1  (feat/wp1-mcp-common)        ← nền tảng chung
../wt-wp2  (feat/wp2-product-agent)     ← BẠN làm (backend đầy đủ)
../wt-wp3  (feat/wp3-legal-stub)        ← stub + contract
../wt-wp4  (feat/wp4-ops-stub)          ← stub + contract
../wt-wp5  (feat/wp5-approval-stub)     ← stub/partial
../wt-wp6  (feat/wp6-orchestrator-mcp)  ← mcp_clients.py hub + fallback
../wt-wp7  (feat/wp7-deploy)            ← systemd + tunnel scripts
```

**Dependency order (build trước → sau):**
```
WP1 (common) ──┬──> WP2 (product, bạn)
                ├──> WP3 (legal stub)
                ├──> WP4 (ops stub)
                └──> WP5 (approval stub)
WP2..WP5 ──────> WP6 (orchestrator hub)
WP1..WP6 ──────> WP7 (deploy)
```

WP1 phải merge/rebase vào main **trước** WP2-5 fork để shared `mcp_common/` có sẵn.
Hoặc: WP2-5 fork từ `wt-wp1` (không từ main) để có `mcp_common` ngay.

## 2. WP Breakdown

| WP | Tên | Owner | Worktree | Deliverable | Depends |
|---|---|---|---|---|---|
| WP1 | mcp-common | bạn | `wt-wp1` | `mcp_common/{schemas,llm_client,config}.py` | — |
| WP2 | product-agent (full) | **bạn** | `wt-wp2` | `servers/product-agent/**` + tests | WP1 |
| WP3 | legal-agent stub | team/you | `wt-wp3` | `servers/legal-agent/server.py` mock | WP1 |
| WP4 | ops-agent stub | team/you | `wt-wp4` | `servers/operations-agent/server.py` mock | WP1 |
| WP5 | approval-agent stub | you/team | `wt-wp5` | `servers/approval-agent/server.py` token issue/verify | WP1 |
| WP6 | orchestrator MCP hub | bạn | `wt-wp6` | `app/services/mcp_clients.py` + fallback | WP2-5 |
| WP7 | deploy | bạn | `wt-wp7` | `deploy/*.sh`, `*.service`, tunnel | WP1-6 |

## 3. Phase Pipeline (theo Company Architect)

```
INTAKE → STRATEGY → DESIGN → BETRIEBSRAT(GATE) → FORK_WRITERS → FORK_WORKERS →
  FIRST-PASS_REVIEW → CONSOLIDATION → QUALITY_AUDIT(parallel) →
  INTEGRATE → RETROSPECTIVE
```

- **Phase BETRIEBSRAT (MANDATORY):** kiểm PII (GOOGLE_API_KEY, VPS pass trong `.env` — đã gitignore), fair scope, co-determination. Veto nếu secret leak.
- **FORK_WRITERS:** mỗi WP = 1 `company-writer` (Abteilungsleiter) fork Workers.
- **Parallel:** WP2-5 chạy song song (độc lập file). WP1 trước tiên.
- **QUALITY_AUDIT:** `company-reviewer` per worktree + `company-auditor` compliance + `company-benchmarker`.

## 4. CI Loop per WP

```
reviewer finds issues → worker fixes → re-validate → PASS → PR → CI green → merge
```
- Mỗi worktree có test riêng. Không merge nếu `pytest` + `pnpm typecheck`(n/a py) fail.
- Lockfile/venv sync trước fork (Python: `requirements.txt` từ `wt-wp1`).

## 5. Worktree commands (execute sau)

```bash
# WP1 base
git worktree add ../wt-wp1 feat/wp1-mcp-common
# fork WP2-5 từ wp1 (có mcp_common sẵn)
git -C ../wt-wp1 worktree add ../wt-wp2 -b feat/wp2-product-agent
git -C ../wt-wp1 worktree add ../wt-wp3 -b feat/wp3-legal-stub
git -C ../wt-wp1 worktree add ../wt-wp4 -b feat/wp4-ops-stub
git -C ../wt-wp1 worktree add ../wt-wp5 -b feat/wp5-approval-stub
# WP6, WP7 từ main sau khi WP1 merge
git worktree add ../wt-wp6 -b feat/wp6-orchestrator-mcp
git worktree add ../wt-wp7 -b feat/wp7-deploy
```

Mỗi worktree chạy:
```bash
cd ../wt-wp<N> && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
pytest -q
```

## 6. Merge order

```
wp1 → main
wp2, wp3, wp4, wp5 → rebase main → PR song song
wp6 → rebase main → PR
wp7 → rebase main → PR
```
Sau mỗi merge: `git worktree remove ../wt-wp<N>` (sạch).

## 7. Rủi ro worktree

- Quên sync `requirements.txt` từ wp1 → import `mcp_common` fail ở WP2-5.
- `.env` không copy vào worktree → test cần key fail. (`.env` chung repo root, worktree share? Không — worktree riêng. Cần symlink `.env` hoặc copy.)
- Conflicting `mcp_common` edit giữa WP → chỉ WP1 sửa,其余 readonly import.
- Long-running VPS deploy test cần SSH tunnel thực tế — làm ở WP7 cuối.

## 8. Next step (chờ bạn bật đèn xanh)

Khi bạn nói "execute", tôi chạy:
1. `git worktree add ../wt-wp1 ...`
2. Tạo `mcp_common/` (WP1) + commit.
3. Fork WP2 (product-agent full) — **bạn làm backend này**.
4. Stub WP3-5.
5. Orchestrator hub WP6.
6. Deploy WP7.
7. Parallel reviewer + audit.
8. Merge tuần tự.
