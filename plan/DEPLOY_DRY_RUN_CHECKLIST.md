# Pre-Deployment Checklist & Dry-Run Analysis — Product Agent MCP

> **Goal:** Simulate what happens on VPS `root@sgp1.w9.nu:2204` before running deploy script.
> **Constraint:** Keep remote clean — no failed deploys, no orphan processes, no port conflicts.

---

## 1. Port Conflict Analysis

| Port | Usage | Risk |
|------|-------|------|
| **2204** | SSH (VPS_SSH_PORT) **AND** PRODUCT_AGENT_PORT | **CRITICAL CONFLICT** — SSH and MCP server cannot both bind 2204 |
| 2205 | Legal Agent | OK |
| 2206 | Operations Agent | OK |
| 2207 | Approval Agent | OK |

**Fix required:** Change `PRODUCT_AGENT_PORT` to something else (e.g., 8004) in `.env` and config.

---

## 2. IPv6 Binding

- VPS is IPv6-only (IPv4 via NAT SSH)
- Current `server.py`: `uvicorn.run(..., host="0.0.0.0", port=settings.PRODUCT_AGENT_PORT)`
- **Problem:** `0.0.0.0` binds IPv4 only. Need `host="::"` for IPv6.
- **Fix:** Detect IPv6 and bind `::` (dual-stack: `host="::"` works for both IPv6 + IPv4 mapped).

---

## 3. System Dependencies (VPS)

`underthesea` (Vietnamese tokenizer) requires:
```bash
apt-get install -y python3-dev build-essential
pip install underthesea  # may need rust/cargo for some deps
```

`sentence-transformers` (phase 2) pulls PyTorch — **heavy** (~2GB). VPS likely limited RAM/disk.
- Current config: `USE_REAL_EMBEDDING=false` → uses hash fallback (good).
- Keep it false for MVP deploy.

---

## 4. Environment File on VPS

Deploy script uses `EnvironmentFile=-/opt/shb-workspace/.env` but **doesn't sync `.env`**.
- Need to rsync `.env` (with GOOGLE_API_KEY) to VPS.
- Or: create `.env` on VPS manually before first deploy.

---

## 5. Python Path / Import Issues

Server code imports:
```python
from mcp_common.config import settings
from servers.product_agent.rag.retriever import ProductRetriever
```

Deploy structure on VPS:
```
/opt/shb-workspace/
├── mcp_common/          (synced)
├── product-agent/       (synced as product-agent/)
│   └── server.py
```

But `servers.product_agent` expects:
```
/opt/shb-workspace/servers/product-agent/
```

**Mismatch!** Rsync target is `/opt/shb-workspace/product-agent/` not `/opt/shb-workspace/servers/product-agent/`.

Fix: either
- Rsync to `/opt/shb-workspace/servers/product-agent/`, or
- Change imports to `from product_agent.rag.retriever import ...`

---

## 6. Systemd Service Issues

Current service file:
```ini
ExecStart=/opt/shb-workspace/product-agent/.venv/bin/python -m servers.product_agent.server
WorkingDirectory=/opt/shb-workspace/product-agent
```

But module path `servers.product_agent.server` requires `WorkingDirectory=/opt/shb-workspace` with `servers/` package.

---

## 7. SSH Authentication

User gave password `Thanh1010` but deploy script uses key-based SSH (`ssh -p $VPS_PORT`).
- Need to either:
  - Copy SSH key to VPS first: `ssh-copy-id -p 2204 root@sgp1.w9.nu`
  - Or modify script to use `sshpass` (not recommended)
  - Or manual first deploy, then key for subsequent

---

## 8. FastMCP + Uvicorn Version Compatibility

`fastmcp>=0.1.0` + `uvicorn>=0.30` — check if `mcp.http_app()` returns ASGI app compatible with uvicorn directly.
- May need `uvicorn.run(mcp.http_app(), ...)` or `uvicorn.run("servers.product_agent.server:mcp.http_app", ...)`

---

## 9. Health Check Before Deploy

Local smoke test (run in worktree before rsync):
```bash
cd ../wt-wp1
python -m venv .venv && source .venv/bin/activate
pip install -r mcp_common/requirements.txt
pip install -e mcp_common
pip install -r servers/product-agent/requirements.txt
# Set env
export GOOGLE_API_KEY=...  # from .env
export USE_REAL_EMBEDDING=false
# Run server in background
python -m servers.product_agent.server &
sleep 3
curl http://localhost:8004/health  # or MCP endpoint
curl -X POST http://localhost:8004/mcp -d '{"method":"tools/call","params":{"name":"health_check"}}'
```

---

## 10. Corrected Deploy Plan

### Step 1: Fix `.env` locally
```bash
# Change PRODUCT_AGENT_PORT=8004 (not 2204)
# Add BIND_HOST=:: for IPv6
```

### Step 2: Fix imports in server.py
```python
# Option A: Rsync to /opt/shb-workspace/servers/product-agent/
# Option B: Change imports
from product_agent.rag.retriever import ProductRetriever  # if workdir=/opt/shb-workspace/product-agent
```

### Step 3: Fix systemd service
```ini
WorkingDirectory=/opt/shb-workspace
ExecStart=/opt/shb-workspace/.venv/bin/python -m servers.product_agent.server
```

### Step 4: Pre-sync `.env` to VPS manually once
```bash
scp -P 2204 .env root@sgp1.w9.nu:/opt/shb-workspace/.env
```

### Step 5: Local smoke test → then deploy

---

## 11. Rollback Plan (if deploy fails)

```bash
ssh -p 2204 root@sgp1.w9.nu "systemctl stop shb-product-agent; systemctl disable shb-product-agent"
# No orphan processes, port freed
```

---

## 12. Updated Files Needed

| File | Change |
|------|--------|
| `.env` | `PRODUCT_AGENT_PORT=8004`, `BIND_HOST=::` |
| `mcp_common/config.py` | Read `BIND_HOST` default `::` |
| `servers/product-agent/server.py` | Use `settings.BIND_HOST` |
| `deploy/deploy_product_agent.sh` | Rsync to `/opt/shb-workspace/servers/product-agent/`, sync `.env` |
| `deploy/shb-product-agent.service` | `WorkingDirectory=/opt/shb-workspace`, correct ExecStart |

---

## 13. Go/No-Go Decision

**Ready to deploy when:**
- [ ] Port conflict resolved (8004 not 2204)
- [ ] IPv6 bind verified locally (`host="::"`)
- [ ] Local smoke test passes (health_check + product_analyze tool call)
- [ ] SSH key copied to VPS
- [ ] `.env` manually placed on VPS
- [ ] Systemd service file corrected

**Do NOT run deploy script until above checked.**