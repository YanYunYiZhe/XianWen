"""核心规则引擎的内部 API。

本模块不是插件 SDK。插件只能提交 StandardEffect 等内容提案；
StateTransition、build_state_transition、apply_state_transition 和
advance_world 仅供核心内部使用。插件隔离由 feat/plugin-contract 完成。
"""

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
from xianwen.core.generation import (
    CharacterDraft,
    ChoiceDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    EffectBound,
    EffectDraft,
    EventDraft,
    LocationDraft,
)
from xianwen.core.models import (
    Choice,
    ChoiceEffect,
    Event,
    LegacyGameState,
    TurnResult,
)
from xianwen.core.narrative import (
    InvalidNarrativeDraftError,
    NarrativeChoice,
    NarrativeDraft,
    RenderedChoice,
    RenderedEvent,
    render_fallback_event,
    validate_narrative_draft,
)
from xianwen.core.player_state import (
    PlayerFlag,
    PlayerState,
    RelationshipValue,
    ReputationValue,
)
from xianwen.core.seed import (
    Condition,
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    StateRequirement,
)
from xianwen.core.seed_turn import (
    InvalidSeedTurnError,
    SeedTurnResult,
    UnsupportedStandardEffectError,
    apply_seed_choice,
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
    # 受控内容生成
    "CharacterDraft",
    "ChoiceDraft",
    "ContentGenerationDraft",
    "ContentGenerationPolicy",
    "EffectBound",
    "EffectDraft",
    "EventDraft",
    "LocationDraft",
    # 种子与叙事契约
    "Condition",
    "InvalidNarrativeDraftError",
    "NarrativeBrief",
    "NarrativeChoice",
    "NarrativeDraft",
    "RenderedChoice",
    "RenderedEvent",
    "SeedChoice",
    "SeedEvent",
    "StateRequirement",
    "render_fallback_event",
    "validate_narrative_draft",
    # 新种子回合
    "InvalidSeedTurnError",
    "SeedTurnResult",
    "UnsupportedStandardEffectError",
    "apply_seed_choice",
    # 世界状态分层与核心内部迁移接口（非插件 API）
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
