"""受控内容生成草案与策略结构。

本模块只定义 AI 可以提交的未校验结构和核心允许的数量边界。
这里创建的对象不能直接写入 GameState，必须经过后续确定性校验、
正式 ID 分配和 GeneratedContentStore 登记。
"""

from dataclasses import dataclass


def _require_text(value: str, field_name: str) -> None:
    """拒绝空白 ID 和文本，避免生成无法追踪的内容。"""
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class EffectDraft:
    """AI 提出的未校验标准效果草案。

    校验通过后才会转换为可信 StandardEffect。
    """

    effect_type: str  # 效果类型，例如 cultivation_delta、luck_delta
    target_id: str | None = None  # 目标实体或字段 ID；无目标效果可为空
    amount: int | None = None  # 数值变化量；非数值效果可为空
    value: bool | None = None  # 布尔标记效果的目标值；非标记效果可为空

    def __post_init__(self) -> None:
        _require_text(self.effect_type, "effect_draft.effect_type")
        if self.target_id is not None:
            _require_text(self.target_id, "effect_draft.target_id")


@dataclass(frozen=True, slots=True)
class ChoiceDraft:
    """AI 提出的新选项草案。

    选项效果必须由核心校验，AI 不能自行决定最终生效数值。
    """

    local_id: str  # 本次 AI 响应内的临时选项 ID
    label: str  # 选项显示文字
    result_text: str  # 选项结果文字
    effects: tuple[EffectDraft, ...] = ()  # 选项携带的未校验效果提案

    def __post_init__(self) -> None:
        _require_text(self.local_id, "choice_draft.local_id")
        _require_text(self.label, "choice_draft.label")
        _require_text(self.result_text, "choice_draft.result_text")


@dataclass(frozen=True, slots=True)
class EventDraft:
    """AI 提出的新事件草案。

    事件可以使用本轮响应内的临时地点、人物和选项 ID。
    正式 ID 和引用关系只能由核心分配。
    """

    local_id: str  # 本次 AI 响应内的临时事件 ID
    derived_from_seed_id: str | None  # 派生来源种子 ID；无来源时可为空
    title: str  # 事件标题
    scene_text: str  # 事件场景文字
    location_id: str | None  # 发生地点；可使用临时或已有地点 ID
    character_ids: tuple[str, ...]  # 涉及人物；可使用临时或已有人物 ID
    choices: tuple[ChoiceDraft, ...]  # 新事件包含的选项提案

    def __post_init__(self) -> None:
        _require_text(self.local_id, "event_draft.local_id")
        _require_text(self.title, "event_draft.title")
        _require_text(self.scene_text, "event_draft.scene_text")

        if self.derived_from_seed_id is not None:
            _require_text(
                self.derived_from_seed_id,
                "event_draft.derived_from_seed_id",
            )
        if self.location_id is not None:
            _require_text(self.location_id, "event_draft.location_id")

        for character_id in self.character_ids:
            _require_text(character_id, "event_draft.character_ids")

        if len(set(self.character_ids)) != len(self.character_ids):
            raise ValueError("event_draft character_ids must be unique")

        if not 2 <= len(self.choices) <= 4:
            raise ValueError("event_draft must contain 2 to 4 choices")

        choice_ids = [choice.local_id for choice in self.choices]
        if len(set(choice_ids)) != len(choice_ids):
            raise ValueError("event_draft choice local_ids must be unique")


@dataclass(frozen=True, slots=True)
class CharacterDraft:
    """AI 提出的新人物草案。"""

    local_id: str  # 本次 AI 响应内的临时人物 ID
    name: str  # 人物名称
    role: str  # 人物身份或叙事角色
    faction_id: str | None  # 所属势力 ID；无归属时可为空
    description: str  # 人物描述
    traits: tuple[str, ...]  # 性格、能力和叙事标签
    relationship_hint: str | None  # 初始关系提示，不能直接改关系数值

    def __post_init__(self) -> None:
        _require_text(self.local_id, "character_draft.local_id")
        _require_text(self.name, "character_draft.name")
        _require_text(self.role, "character_draft.role")
        _require_text(self.description, "character_draft.description")

        if self.faction_id is not None:
            _require_text(self.faction_id, "character_draft.faction_id")
        if self.relationship_hint is not None:
            _require_text(
                self.relationship_hint,
                "character_draft.relationship_hint",
            )

        for trait in self.traits:
            _require_text(trait, "character_draft.traits")


@dataclass(frozen=True, slots=True)
class LocationDraft:
    """AI 提出的新地点草案。"""

    local_id: str  # 本次 AI 响应内的临时地点 ID
    name: str  # 地点名称
    description: str  # 地点描述
    location_type: str  # 地点类型，例如 sect、ruin、town
    tags: tuple[str, ...]  # 用于筛选和叙事检索的标签
    connected_to: tuple[str, ...]  # 连接地点；可使用临时或已有地点 ID

    def __post_init__(self) -> None:
        _require_text(self.local_id, "location_draft.local_id")
        _require_text(self.name, "location_draft.name")
        _require_text(self.description, "location_draft.description")
        _require_text(self.location_type, "location_draft.location_type")

        for tag in self.tags:
            _require_text(tag, "location_draft.tags")
        for location_id in self.connected_to:
            _require_text(location_id, "location_draft.connected_to")

        if len(set(self.connected_to)) != len(self.connected_to):
            raise ValueError("location_draft connected_to must be unique")


@dataclass(frozen=True, slots=True)
class ContentGenerationDraft:
    """AI 返回的一次完整内容生成提案。

    该对象仍不可信，不能直接进入 DynamicWorldState 或 GeneratedContentStore。
    """

    derived_from_seed_id: str  # 本次生成依据的可信种子 ID
    locations: tuple[LocationDraft, ...] = ()  # 新地点提案集合
    characters: tuple[CharacterDraft, ...] = ()  # 新人物提案集合
    events: tuple[EventDraft, ...] = ()  # 新事件提案集合

    def __post_init__(self) -> None:
        _require_text(
            self.derived_from_seed_id,
            "content_generation_draft.derived_from_seed_id",
        )

        # 地点、人物、事件共享同一个响应内命名空间，临时 ID 不允许重复。
        local_ids = [
            *(location.local_id for location in self.locations),
            *(character.local_id for character in self.characters),
            *(event.local_id for event in self.events),
        ]
        if len(set(local_ids)) != len(local_ids):
            raise ValueError(
                "content_generation_draft local_ids must be unique across entities"
            )


@dataclass(frozen=True, slots=True)
class EffectBound:
    """某一种标准效果允许的数值上下限。"""

    effect_type: str  # 需要限制的标准效果类型
    min_amount: int  # 允许的最小数值变化
    max_amount: int  # 允许的最大数值变化

    def __post_init__(self) -> None:
        _require_text(self.effect_type, "effect_bound.effect_type")
        if self.min_amount > self.max_amount:
            raise ValueError("effect_bound min_amount cannot exceed max_amount")


@dataclass(frozen=True, slots=True)
class ContentGenerationPolicy:
    """AI 内容生成和效果提交的数量、类型与数值边界。

    生产默认值尚未冻结，因此该类不提供隐含默认值，必须由调用方显式传入。
    """

    max_locations_per_turn: int  # 每回合最多新增地点数
    max_characters_per_turn: int  # 每回合最多新增人物数
    max_events_per_turn: int  # 每回合最多新增事件数
    max_options_per_event: int  # 单个事件最多选项数
    max_effects_per_choice: int  # 单个选项最多效果数
    allowed_effect_types: tuple[str, ...]  # 允许的标准效果类型
    effect_bounds: tuple[EffectBound, ...]  # 每种效果的数值上下限
    max_total_effect_per_turn: int  # 单回合总效果预算
    forbidden_effect_types: tuple[str, ...]  # 明确禁止的效果类型
    max_active_foreshadows: int  # 同时存在的认证伏笔上限
    max_model_calls_per_turn: int  # 单回合模型调用上限

    def __post_init__(self) -> None:
        counts = (
            self.max_locations_per_turn,
            self.max_characters_per_turn,
            self.max_events_per_turn,
            self.max_options_per_event,
            self.max_effects_per_choice,
            self.max_total_effect_per_turn,
            self.max_active_foreshadows,
            self.max_model_calls_per_turn,
        )
        if any(value < 0 for value in counts):
            raise ValueError("content_generation_policy counts cannot be negative")

        for effect_type in self.allowed_effect_types:
            _require_text(
                effect_type,
                "content_generation_policy.allowed_effect_types",
            )
        for effect_type in self.forbidden_effect_types:
            _require_text(
                effect_type,
                "content_generation_policy.forbidden_effect_types",
            )

        overlap = set(self.allowed_effect_types) & set(self.forbidden_effect_types)
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ValueError(
                f"effect types cannot be both allowed and forbidden: {names}"
            )

        bound_types = [bound.effect_type for bound in self.effect_bounds]
        if len(set(bound_types)) != len(bound_types):
            raise ValueError("content_generation_policy effect_bounds must be unique")
