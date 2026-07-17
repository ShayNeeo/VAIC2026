"""Legal Agent V2 Package.

This package contains the new extension for the Legal Agent, built according
to plan_v3 (V2 Proposal). It does not modify existing orchestrator code and
provides a `LegalAgentV2` class as a drop-in replacement.
"""

# We export LegalAgentV2 here
from .adapter import LegalAgentV2

__all__ = ["LegalAgentV2"]
