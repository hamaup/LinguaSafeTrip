# backend/app/agents/safety_beacon_agent/__init__.py
from .core.main_orchestrator import run_agent_interaction

__all__ = [
    "run_agent_interaction",
]

# Lazy import to avoid circular dependency
def get_proactive_agent():
    from .proactive_suggester import invoke_proactive_agent
    return invoke_proactive_agent