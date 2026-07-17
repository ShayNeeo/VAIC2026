"""Test-session isolation: keep the suite fast, offline and deterministic.

INTENT_USE_LLM=true in .env is a real runtime capability (see app/config.py,
app/intent/extractor.py) that we want enabled for the running server/demo.
Without this override, every test that builds a default IntentExtractor()/
V2WorkflowEngine() would make a live OpenAI call, making the suite slow,
flaky and dependent on network/API-key/cost -- exactly what the deterministic
fallback (app/intent/fallback.py) exists to avoid in tests. python-dotenv
does not clobber an already-set os.environ value, so setting this here before
app.config is ever imported reliably wins over the .env file for the whole
pytest session while leaving the .env file itself unchanged for real runs.
"""

import os

os.environ["INTENT_USE_LLM"] = "false"
