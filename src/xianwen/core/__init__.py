"""给核心规则引擎的公共API"""

from xianwen.core.engine import (
    InvalidChoiceError,
    InvalidEventError,
    apply_choice,
    get_current_event,
    new_game,
)
from xianwen.core.models import Choice, ChoiceEffect, Event, GameState, TurnResult

__all__ = [
    "Choice",
    "ChoiceEffect",
    "Event",
    "GameState",
    "InvalidChoiceError",
    "InvalidEventError",
    "TurnResult",
    "apply_choice",
    "get_current_event",
    "new_game",
]