"""Test-session isolation: keep the suite fast, offline and deterministic.

INTENT_USE_LLM=true and AGENTIC_LLM_ENABLED=true in .env are real runtime
capabilities (see app/config.py, app/intent/extractor.py,
app/agents/base.py) that we want enabled for the running server/demo.
Without this override, every test that builds a default IntentExtractor()/
V2WorkflowEngine()/*ExpertAgent() would make a live OpenAI call, making the
suite slow, flaky, billed and dependent on network/API-key/cost -- exactly
what the deterministic fallback (app/intent/fallback.py, and each expert's
domain service) exists to avoid in tests. python-dotenv does not clobber an
already-set os.environ value, so setting these here before app.config is
ever imported reliably wins over the .env file for the whole pytest session
while leaving the .env file itself unchanged for real runs.
"""

import os

os.environ["INTENT_USE_LLM"] = "false"
os.environ["AGENTIC_LLM_ENABLED"] = "false"
