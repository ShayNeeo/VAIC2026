"""V2 Audit Logger for SHB Corporate Sales Copilot.

Implements Phase 10 of the End-to-End Workflow.
Captures structured logs for human-in-the-loop interventions,
system decisions, and policy overrides to support feedback loops.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict


class V2EventLogger:
    def __init__(self, log_path: str = "data/audit.log"):
        self.log_path = log_path
        self.logger = logging.getLogger("V2Audit")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_path)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def log_decision(
        self,
        case_id: str,
        actor_id: str,
        decision_type: str,
        context: Dict[str, Any],
        outcome: str
    ) -> None:
        """Log an automated or human decision."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "decision",
            "case_id": case_id,
            "actor_id": actor_id,
            "decision_type": decision_type,
            "context": context,
            "outcome": outcome,
        }
        self.logger.info(json.dumps(event))

    def log_override(
        self,
        case_id: str,
        specialist_id: str,
        rule_id: str,
        reason: str
    ) -> None:
        """Log a specialist overriding a system risk/policy block."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "override",
            "case_id": case_id,
            "actor_id": specialist_id,
            "rule_id": rule_id,
            "reason": reason,
        }
        self.logger.info(json.dumps(event))
