"""
Agent-related schema definitions.
Consolidates all agent state, suggestions, and response schemas.
"""

# Import from unified agent_state location
from ..agent_state import AgentState, AgentStateModel
from .suggestions import SuggestionItem, SuggestionCard, SuggestionCardActionButton, ProactiveSuggestion
from .responses import AgentResponse, ErrorResponse
from .routing import RoutingDecision, DisasterIntentSchema

__all__ = [
    # Agent state
    "AgentState",
    "AgentStateModel",
    
    # Suggestions
    "SuggestionItem",
    "SuggestionCard",
    "SuggestionCardActionButton",
    "ProactiveSuggestion",
    
    # Responses
    "AgentResponse",
    "ErrorResponse",
    
    # Routing
    "RoutingDecision",
    "DisasterIntentSchema"
]