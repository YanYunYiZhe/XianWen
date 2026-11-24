"""不可变世界状态、状态版本和核心迁移入口。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# 插件状态和生成内容元数据允许使用的 JSON 标量。
JsonScalar = str | int | bool | None

DEFAULT_WORLDLINE_ID = "base.main"
DEFAULT_WORLDLINE_STAGE = "opening"
DEFAULT_CONTENT_VERSION = "1.0"

_TRANSITION_SOURCES = frozenset({"core", "plugin", "ai"})
_GENERATED_CONTENT_KINDS = frozenset({"location", "character", "event"})


def _require_text(value: str, field_name: str) -> None:
    """核心字段不允许空字符串，避免无法追踪的世界线或版本。"""
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


# ---------------------------------------------------------------------------
# 动态世界记录
#
# 当前只实现最小字段，后续内容生成阶段再扩展。
# 所有记录均不可变，只通过 replace() 生成新记录。
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LocationRecord:
    """已发现或已生成的地点。"""

    id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        _require_text(self.id, "location.id")
        _require_text(self.name, "location.name")


@dataclass(frozen=True, slots=True)
class CharacterRecord:
    """已出现或已生成的永久人物。"""

    id: str
    name: str
    role: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        _require_text(self.id, "character.id")
        _require_text(self.name, "character.name")


@dataclass(frozen=True, slots=True)
class RelationshipRecord:
    """人物、势力或玩家之间的关系数值。"""

    source_id: str
    target_id: str
    value: int = 0
    kind: str = "relationship"

    def __post_init__(self) -> None:
        _require_text(self.source_id, "relationship.source_id")
        _require_text(self.target_id, "relationship.target_id")
        _require_text(self.kind, "relationship.kind")


@dataclass(frozen=True, slots=True)
class FactionRecord:
    """已出现的势力。"""

    id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        _require_text(self.id, "faction.id")
        _require_text(self.name, "faction.name")


@dataclass(frozen=True, slots=True)
class WorldFlag:
    """世界层面的布尔标记。"""

    key: str
    value: bool = True

    def __post_init__(self) -> None:
        _require_text(self.key, "flag.key")


@dataclass(frozen=True, slots=True)
class ItemRecord:
    """物品快照。

    玩家持有物位于 PlayerState.items；世界关键物品、公共物品和
    掉落物位于 DynamicWorldState.items。同一物品同一时刻只能有一个
    权威归属。
    """

    id: str
    name: str
    quantity: int = 1

    def __post_init__(self) -> None:
        _require_text(self.id, "item.id")
        _require_text(self.name, "item.name")
        if self.quantity < 1:
            raise ValueError("item.quantity must be at least 1")


@dataclass(frozen=True, slots=True)
class PluginStateRecord:
    """插件命名空间下的私有可序列化状态。"""

    plugin_id: str
    key: str
    value: JsonScalar = None

    def __post_init__(self) -> None:
        _require_text(self.plugin_id, "plugin_state.plugin_id")
        _require_text(self.key, "plugin_state.key")


@dataclass(frozen=True, slots=True)
class GeneratedContentRecord:
    """AI 生成内容的正式 ID、来源和版本元数据。"""

    id: str
    kind: str
    source_seed_id: str | None
    created_turn: int
    generator_version: str
    definition: str

    def __post_init__(self) -> None:
        _require_text(self.id, "generated_content.id")
        if self.kind not in _GENERATED_CONTENT_KINDS:
            raise ValueError(f"Unsupported generated content kind: {self.kind!r}")
        if self.source_seed_id is not None:
            _require_text(self.source_seed_id, "generated_content.source_seed_id")
        if self.created_turn < 1:
            raise ValueError("generated_content.created_turn must be at least 1")
        _require_text(self.generator_version, "generated_content.generator_version")
        _require_text(self.definition, "generated_content.definition")


@dataclass(frozen=True, slots=True)
class GeneratedContentStore:
    """当前局已登记并随存档保存的 AI 生成内容。"""

    locations: tuple[GeneratedContentRecord, ...] = ()
    characters: tuple[GeneratedContentRecord, ...] = ()
    events: tuple[GeneratedContentRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class DynamicWorldState:
    """可演化、但不可原地修改的动态世界状态。"""

    locations: tuple[LocationRecord, ...] = ()
    characters: tuple[CharacterRecord, ...] = ()
    relationships: tuple[RelationshipRecord, ...] = ()
    factions: tuple[FactionRecord, ...] = ()
    flags: tuple[WorldFlag, ...] = ()
    # 世界中的关键、公共或掉落物品，不包含玩家背包中的持有物
    items: tuple[ItemRecord, ...] = ()
    plugin_states: tuple[PluginStateRecord, ...] = ()
    generated_content: GeneratedContentStore = field(
        default_factory=GeneratedContentStore
    )


# ---------------------------------------------------------------------------
# 核心权威状态
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CoreWorldState:
    """
    年份、回合、世界线阶段和状态版本的唯一权威来源。

    AI、插件和 Web 都不能直接修改这个对象。
    每次合法提交都必须生成一个新的 CoreWorldState。
    """

    turn: int = 1
    year: int = 1
    world_seed: int = 0
    worldline_id: str = DEFAULT_WORLDLINE_ID
    worldline_stage: str = DEFAULT_WORLDLINE_STAGE
    state_version: int = 1
    content_version: str = DEFAULT_CONTENT_VERSION

    def __post_init__(self) -> None:
        """在创建核心快照时立即校验基本不变量。"""
        if self.turn < 1:
            raise ValueError("turn must be at least 1")
        if self.year < 1:
            raise ValueError("year must be at least 1")
        if self.state_version < 1:
            raise ValueError("state_version must be at least 1")

        _require_text(self.worldline_id, "worldline_id")
        _require_text(self.worldline_stage, "worldline_stage")
        _require_text(self.content_version, "content_version")


@dataclass(frozen=True, slots=True)
class WorldSnapshot:
    """某一回合的完整世界不可变快照。"""

    core: CoreWorldState = field(default_factory=CoreWorldState)
    dynamic: DynamicWorldState = field(default_factory=DynamicWorldState)


# ---------------------------------------------------------------------------
# 状态提交
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StandardEffect:
    """
    状态迁移中记录的标准效果提案。

    当前只记录效果数据，白名单和数值范围校验在内容生成阶段实现。
    插件只能提交 StandardEffect，不能提交 PlayerState、WorldSnapshot
    或 StateTransition。AddItem/RemoveItem 类效果必须声明物品归属。
    """

    effect_type: str
    target_id: str | None = None
    amount: int | None = None
    value: JsonScalar = None

    def __post_init__(self) -> None:
        _require_text(self.effect_type, "effect_type")
        if self.target_id is not None:
            _require_text(self.target_id, "target_id")


@dataclass(frozen=True, slots=True)
class StateTransition:
    """
    核心构造的一次状态变化原子请求，不是插件 API。

    expected_version 必须等于提交方看到的状态版本。
    new_core 和 new_dynamic 只能由核心构造；插件、AI 和 Web
    只能提交 StandardEffect 提案，不能直接提交本对象。
    source 仅记录提案来源，不代表外部模块有权提交状态。
    """

    expected_version: int
    new_core: CoreWorldState
    new_dynamic: DynamicWorldState
    applied_effects: tuple[StandardEffect, ...] = ()
    source: str = "core"

    def __post_init__(self) -> None:
        """拒绝明显非法的提交来源。"""
        if self.expected_version < 1:
            raise ValueError("expected_version must be at least 1")
        if self.source not in _TRANSITION_SOURCES:
            raise ValueError(f"Unsupported transition source: {self.source!r}")


class StateVersionConflictError(ValueError):
    """提交方使用了过期状态版本。"""


class InvalidStateTransitionError(ValueError):
    """迁移试图绕过核心状态不变量。"""


def create_initial_world(
    *,
    world_seed: int = 0,
    worldline_id: str = DEFAULT_WORLDLINE_ID,
    worldline_stage: str = DEFAULT_WORLDLINE_STAGE,
    content_version: str = DEFAULT_CONTENT_VERSION,
) -> WorldSnapshot:
    """创建第一回合的初始世界快照。"""
    return WorldSnapshot(
        core=CoreWorldState(
            world_seed=world_seed,
            worldline_id=worldline_id,
            worldline_stage=worldline_stage,
            content_version=content_version,
        )
    )


def build_state_transition(
    snapshot: WorldSnapshot,
    *,
    expected_version: int | None = None,
    new_dynamic: DynamicWorldState | None = None,
    advance_time: bool = False,
    applied_effects: tuple[StandardEffect, ...] = (),
    source: str = "core",
) -> StateTransition:
    """
    由核心构造下一版状态请求。

    - 不修改传入快照。
    - advance_time=False 时只更新动态内容和状态版本。
    - advance_time=True 时同时推进一个回合和一年。
    """
    next_version = snapshot.core.state_version + 1

    if advance_time:
        new_core = replace(
            snapshot.core,
            turn=snapshot.core.turn + 1,
            year=snapshot.core.year + 1,
            state_version=next_version,
        )
    else:
        new_core = replace(snapshot.core, state_version=next_version)

    return StateTransition(
        expected_version=(
            snapshot.core.state_version
            if expected_version is None
            else expected_version
        ),
        new_core=new_core,
        new_dynamic=(snapshot.dynamic if new_dynamic is None else new_dynamic),
        applied_effects=applied_effects,
        source=source,
    )


def apply_state_transition(
    snapshot: WorldSnapshot,
    transition: StateTransition,
) -> WorldSnapshot:
    """
    校验版本和核心字段后，返回新的不可变世界快照。

    这一步是核心唯一的普通状态提交入口。
    """
    current_version = snapshot.core.state_version

    if transition.expected_version != current_version:
        raise StateVersionConflictError(
            f"Expected version {transition.expected_version}, "
            f"current version is {current_version}"
        )

    _validate_core_transition(snapshot.core, transition.new_core)

    return WorldSnapshot(
        core=transition.new_core,
        dynamic=transition.new_dynamic,
    )


def advance_world(
    snapshot: WorldSnapshot,
    *,
    expected_version: int | None = None,
    new_dynamic: DynamicWorldState | None = None,
    applied_effects: tuple[StandardEffect, ...] = (),
    source: str = "core",
) -> WorldSnapshot:
    """由核心推进一个回合和一年，并生成新版本快照。"""
    transition = build_state_transition(
        snapshot,
        expected_version=expected_version,
        new_dynamic=new_dynamic,
        advance_time=True,
        applied_effects=applied_effects,
        source=source,
    )
    return apply_state_transition(snapshot, transition)


def _validate_core_transition(
    current_core: CoreWorldState,
    new_core: CoreWorldState,
) -> None:
    """
    检查普通状态迁移是否试图修改核心权威字段。

    世界线切换未来需要单独的世界线迁移函数，不能走普通提交。
    """
    if new_core.state_version != current_core.state_version + 1:
        raise InvalidStateTransitionError("state_version must increase by exactly one")

    if new_core.world_seed != current_core.world_seed:
        raise InvalidStateTransitionError(
            "world_seed cannot change during a transition"
        )

    if new_core.content_version != current_core.content_version:
        raise InvalidStateTransitionError(
            "content_version cannot change during a transition"
        )

    if new_core.worldline_id != current_core.worldline_id:
        raise InvalidStateTransitionError(
            "worldline switches require a dedicated transition"
        )

    turn_delta = new_core.turn - current_core.turn
    if turn_delta not in {0, 1}:
        raise InvalidStateTransitionError(
            "turn may only stay unchanged or advance by one"
        )

    if new_core.year - current_core.year != turn_delta:
        raise InvalidStateTransitionError("year must advance in lockstep with turn")
