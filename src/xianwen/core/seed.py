"""种子事件及其固定规则选项。

种子事件是规则和剧情骨架。AI 只能扩写展示文本，不能修改这里定义的
选项 ID、标准效果、触发条件或后备文本。
"""

from dataclasses import dataclass

from xianwen.core.world_state import StandardEffect


def _require_text(value: str, field_name: str) -> None:
    """拒绝空白 ID 或文本，避免生成无法追踪的内容。"""
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class Condition:
    """事件触发条件。

    当前阶段只确定数据结构，不执行条件判断，也不限制 kind 的合法取值。
    条件求值器将在候选种子筛选阶段实现。
    """

    kind: str  # 条件类型，例如 flag、relationship、item、year
    target: str  # 条件读取的目标 ID 或状态字段名
    operator: str  # 比较方式，例如 eq、neq、gte、lte、has
    value: str | int | bool  # 与目标值比较时使用的值

    def __post_init__(self) -> None:
        _require_text(self.kind, "condition.kind")
        _require_text(self.target, "condition.target")
        _require_text(self.operator, "condition.operator")


@dataclass(frozen=True, slots=True)
class StateRequirement:
    """种子事件的附加状态门槛。

    所有字段均为可选；当前只校验范围自身是否合法，不读取 GameState。
    """

    min_year: int | None = None  # 允许触发的最小年份；None 表示不限
    max_year: int | None = None  # 允许触发的最大年份；None 表示不限
    min_cultivation: int | None = None  # 允许触发的最低修为；None 表示不限
    max_cultivation: int | None = None  # 允许触发的最高修为；None 表示不限
    required_flags: tuple[str, ...] = ()  # 触发前必须存在的玩家标记
    forbidden_flags: tuple[str, ...] = ()  # 触发前必须不存在的玩家标记

    def __post_init__(self) -> None:
        if self.min_year is not None and self.min_year < 1:
            raise ValueError("state_requirement.min_year must be at least 1")
        if self.max_year is not None and self.max_year < 1:
            raise ValueError("state_requirement.max_year must be at least 1")
        if (
            self.min_year is not None
            and self.max_year is not None
            and self.min_year > self.max_year
        ):
            raise ValueError("state_requirement.min_year cannot exceed max_year")

        if (
            self.min_cultivation is not None
            and self.max_cultivation is not None
            and self.min_cultivation > self.max_cultivation
        ):
            raise ValueError(
                "state_requirement.min_cultivation cannot exceed max_cultivation"
            )

        for flag in (*self.required_flags, *self.forbidden_flags):
            _require_text(flag, "state_requirement.flag")

        overlap = set(self.required_flags) & set(self.forbidden_flags)
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ValueError(
                "state_requirement flags cannot be both required and "
                f"forbidden: {names}"
            )


@dataclass(frozen=True, slots=True)
class NarrativeBrief:
    """提供给 AI 的结构化剧情简报。

    required_beats 是必须保留的剧情节点；allowed_improvisation 是允许 AI
    自由增加的临时细节；forbidden_content 是不可越过的规则边界。
    """

    premise: str  # 本事件的核心情境和戏剧问题
    tone: str  # AI 扩写时应保持的叙事基调
    required_beats: tuple[str, ...]  # 扩写必须保留的剧情节点
    allowed_improvisation: tuple[str, ...]  # 允许 AI 自由创造的临时细节
    forbidden_content: tuple[str, ...]  # 禁止 AI 引入的设定或规则变化

    def __post_init__(self) -> None:
        _require_text(self.premise, "narrative_brief.premise")
        _require_text(self.tone, "narrative_brief.tone")

        for beat in self.required_beats:
            _require_text(beat, "narrative_brief.required_beats")
        for item in self.allowed_improvisation:
            _require_text(item, "narrative_brief.allowed_improvisation")
        for item in self.forbidden_content:
            _require_text(item, "narrative_brief.forbidden_content")


@dataclass(frozen=True, slots=True)
class SeedChoice:
    """种子事件中的固定规则选项。

    AI 不能修改 id、effects 或后备文本。玩家选择后，effects 由核心解析，
    不能从 AI 返回的叙事文本中推导。
    """

    id: str  # 事件内唯一的选项 ID；AI 不得修改
    fallback_label: str  # 无 AI 时显示的选项文字
    result_hint: str  # 供 AI 扩写结果文本的剧情提示
    fallback_result_text: str  # 无 AI 时展示的结果文字
    effects: tuple[StandardEffect, ...] = ()  # 核心校验并应用的标准效果

    def __post_init__(self) -> None:
        _require_text(self.id, "seed_choice.id")
        _require_text(self.fallback_label, "seed_choice.fallback_label")
        _require_text(self.result_hint, "seed_choice.result_hint")
        _require_text(self.fallback_result_text, "seed_choice.fallback_result_text")


@dataclass(frozen=True, slots=True)
class SeedEvent:
    """稳定的规则与剧情骨架。

    事件本身不可变。AI 只能围绕该结构生成 NarrativeDraft，不能修改选项、
    效果、触发条件或后备文本。
    """

    id: str  # 全局唯一事件 ID；基础内容使用 base. 命名空间
    category: str  # 事件分类，例如 daily、combat、mystery
    fallback_scene_text: str  # 无 AI 或 AI 失败时使用的完整场景文字
    ai_prompt: str  # 针对本事件的叙事扩写提示
    narrative_brief: NarrativeBrief  # 约束 AI 扩写范围的结构化简报
    choices: tuple[SeedChoice, ...]  # 2-4 个固定规则选项

    worldline_id: str | None = None  # 所属世界线 ID；普通支线为空
    stage: str | None = None  # 世界线阶段或事件阶段；无阶段约束时为空
    conditions: tuple[Condition, ...] = ()  # 事件被选中前必须满足的条件
    weight: int = 1  # 合格候选中的抽取权重；必须为非负整数
    location_ids: tuple[str, ...] = ()  # 允许触发该事件的地点 ID 集合
    time_slots: tuple[str, ...] = ()  # 允许触发该事件的时间段集合
    required_state: StateRequirement | None = None  # 额外状态门槛；None 表示无
    source_plugin_id: str | None = None  # 来源插件 ID；基础或 AI 内容可为空

    def __post_init__(self) -> None:
        _require_text(self.id, "seed_event.id")
        _require_text(self.category, "seed_event.category")
        _require_text(
            self.fallback_scene_text,
            "seed_event.fallback_scene_text",
        )
        _require_text(self.ai_prompt, "seed_event.ai_prompt")

        if self.worldline_id is not None:
            _require_text(self.worldline_id, "seed_event.worldline_id")
        if self.stage is not None:
            _require_text(self.stage, "seed_event.stage")
        if self.source_plugin_id is not None:
            _require_text(self.source_plugin_id, "seed_event.source_plugin_id")

        if self.weight < 0:
            raise ValueError("seed_event.weight must not be negative")

        if not 2 <= len(self.choices) <= 4:
            raise ValueError("seed_event must contain 2 to 4 choices")

        choice_ids = [choice.id for choice in self.choices]
        if len(set(choice_ids)) != len(choice_ids):
            raise ValueError("seed_event choice ids must be unique")

        for location_id in self.location_ids:
            _require_text(location_id, "seed_event.location_ids")
        for time_slot in self.time_slots:
            _require_text(time_slot, "seed_event.time_slots")
