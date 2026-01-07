"""
Registration module for NeMo Agent Toolkit custom functions.
This file ensures custom functions are registered when the package is imported.
"""

# Import all registered functions to ensure they're registered at runtime
from .event_planning_nemo import (
    generate_event_themes,
    refine_event_plan,
    fetch_moderators,
    fetch_participants,
    ask_user,
)

__all__ = [
    "generate_event_themes",
    "refine_event_plan",
    "fetch_moderators",
    "fetch_participants",
    "ask_user",
]