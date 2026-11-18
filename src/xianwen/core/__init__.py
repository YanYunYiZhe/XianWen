"""给核心规则引擎的公共 API。"""

from xianwen.core.chronicle import ChronicleEntry
from xianwen.core.engine import (
    InvalidChoiceError,
    InvalidEventError,
    apply_choice,
    get_current_event,
    new_game,
)
from xianwen.core.foreshadow import (
    ForeshadowAssessment,
    ForeshadowBook,
    ForeshadowRecord,
)
from xianwen.core.game_state import GameState
from xianwen.core.models import (
    Choice,
    ChoiceEffect,
    Event,
    LegacyGameState,
    TurnResult,
)
from xianwen.core.player_state import (
    PlayerFlag,
    PlayerState,
    RelationshipValue,
    ReputationValue,
)
from xianwen.core.world_state import (
    CharacterRecord,
    CoreWorldState,
    DynamicWorldState,
    FactionRecord,
    GeneratedContentRecord,
    GeneratedContentStore,
    InvalidStateTransitionError,
    ItemRecord,
    LocationRecord,
    PluginStateRecord,
    RelationshipRecord,
    StandardEffect,
    StateTransition,
    StateVersionConflictError,
    WorldFlag,
    WorldSnapshot,
    advance_world,
    apply_state_transition,
    build_state_transition,
    create_initial_world,
)

__all__ = [
    # 第一阶段兼容接口
    "Choice",
    "ChoiceEffect",
    "Event",
    "InvalidChoiceError",
    "InvalidEventError",
    "LegacyGameState",
    "TurnResult",
    "apply_choice",
    "get_current_event",
    "new_game",
    # 玩家与局状态
    "ChronicleEntry",
    "ForeshadowAssessment",
    "ForeshadowBook",
    "ForeshadowRecord",
    "GameState",
    "PlayerFlag",
    "PlayerState",
    "RelationshipValue",
    "ReputationValue",
    # 世界状态分层接口
    "CharacterRecord",
    "CoreWorldState",
    "DynamicWorldState",
    "FactionRecord",
    "GeneratedContentRecord",
    "GeneratedContentStore",
    "InvalidStateTransitionError",
    "ItemRecord",
    "LocationRecord",
    "PluginStateRecord",
    "RelationshipRecord",
    "StandardEffect",
    "StateTransition",
    "StateVersionConflictError",
    "WorldFlag",
    "WorldSnapshot",
    "advance_world",
    "apply_state_transition",
    "build_state_transition",
    "create_initial_world",
]
