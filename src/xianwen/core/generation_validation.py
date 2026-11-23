"""受控内容生成的确定性校验与正式 ID 分配。

本模块把 AI 提交的不可信 ContentGenerationDraft 转换为可信的
ValidatedGeneratedContent。这里不修改世界状态。
"""

from dataclasses import dataclass

from xianwen.core.generation import (
    CharacterDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    EffectDraft,
    EventDraft,
    LocationDraft,
)
from xianwen.core.seed import (
    Condition,
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    StateRequirement,
)
from xianwen.core.world_state import StandardEffect, WorldSnapshot

# 当前最小实现支持的数值型标准效果。
# 其他效果类型在契约冻结前必须失败关闭，不能假装已经理解。
_SUPPORTED_AMOUNT_EFFECTS = frozenset({"cultivation_delta", "luck_delta"})


class ContentValidationError(ValueError):
    """AI 内容草案未通过确定性校验。"""


@dataclass(frozen=True, slots=True)
class ValidatedLocation:
    """已通过校验并分配正式 ID 的新地点。"""

    id: str  # 核心分配的正式地点 ID
    name: str  # 地点名称
    description: str  # 地点描述
    location_type: str  # 地点类型，例如 sect、ruin、town
    tags: tuple[str, ...]  # 筛选和叙事检索标签
    connected_to: tuple[str, ...]  # 已重写为正式 ID 的连接地点


@dataclass(frozen=True, slots=True)
class ValidatedCharacter:
    """已通过校验并分配正式 ID 的新人物。"""

    id: str  # 核心分配的正式人物 ID
    name: str  # 人物名称
    role: str  # 人物身份或叙事角色
    faction_id: str | None  # 所属势力 ID；无归属时为空
    description: str  # 人物描述
    traits: tuple[str, ...]  # 性格、能力和叙事标签
    relationship_hint: str | None  # 初始关系提示，不携带关系数值


@dataclass(frozen=True, slots=True)
class ValidatedChoice:
    """已通过校验并分配正式选项 ID 的新选项。"""

    choice_id: str  # 核心分配的正式选项 ID
    label: str  # 选项显示文字；转换为 SeedChoice 时作为 fallback_label
    result_text: str  # 选项结果文字；转换为 SeedChoice 时作为 fallback_result_text
    result_hint: str  # 结果扩写提示；转换为 SeedChoice 时保留
    effects: tuple[StandardEffect, ...]  # 已转换并校验的标准效果


@dataclass(frozen=True, slots=True)
class ValidatedEvent:
    """已通过校验并分配正式 ID 的新事件。"""

    event_id: str  # 核心分配的正式事件 ID
    derived_from_seed_id: str  # 派生来源种子 ID
    title: str  # 事件标题
    scene_text: str  # 事件场景文字；同时作为后备场景文字
    location_id: str | None  # 已重写为正式 ID 的发生地点
    character_ids: tuple[str, ...]  # 已重写为正式 ID 的涉及人物
    choices: tuple[ValidatedChoice, ...]  # 已校验选项集合

    category: str  # 事件分类
    worldline_id: str | None  # 所属世界线
    stage: str | None  # 世界线阶段或事件阶段
    conditions: tuple[Condition, ...]  # 触发条件
    weight: int  # 候选权重
    location_ids: tuple[str, ...]  # 允许触发地点
    time_slots: tuple[str, ...]  # 允许触发时间段
    required_state: StateRequirement | None  # 状态门槛
    fallback_scene_text: str  # 无 AI 时使用的场景文字
    ai_prompt: str  # AI 扩写提示
    narrative_brief: NarrativeBrief  # 剧情简报


@dataclass(frozen=True, slots=True)
class ValidatedGeneratedContent:
    """一次完整、已校验、尚未写入世界状态的生成内容。"""

    source_seed_id: str  # 本批内容依据的可信种子 ID
    generator_version: str  # 生成器或提示词版本
    locations: tuple[ValidatedLocation, ...]  # 已校验新地点
    characters: tuple[ValidatedCharacter, ...]  # 已校验新人物
    events: tuple[ValidatedEvent, ...]  # 已校验新事件


def validate_content_generation(
    draft: ContentGenerationDraft,
    snapshot: WorldSnapshot,
    policy: ContentGenerationPolicy,
    *,
    trusted_seed: SeedEvent,
    generator_version: str,
) -> ValidatedGeneratedContent:
    """校验 AI 内容草案并分配正式 ID。

    校验顺序：
    1. 来源种子必须匹配。
    2. 数量不得超过策略。
    3. 临时 ID 不与已有 ID 冲突。
    4. 引用和效果合法。
    5. 分配正式 ID 并重写引用。
    """
    if not generator_version.strip():
        raise ContentValidationError("generator_version must not be empty")

    if draft.derived_from_seed_id != trusted_seed.id:
        raise ContentValidationError(
            f"draft seed {draft.derived_from_seed_id!r} "
            f"does not match trusted seed {trusted_seed.id!r}"
        )

    _validate_counts(draft, policy)

    existing_location_ids = {item.id for item in snapshot.dynamic.locations}
    existing_character_ids = {item.id for item in snapshot.dynamic.characters}
    existing_faction_ids = {item.id for item in snapshot.dynamic.factions}
    existing_item_ids = {item.id for item in snapshot.dynamic.items}
    existing_generated_ids = {
        item.id
        for item in (
            *snapshot.dynamic.generated_content.locations,
            *snapshot.dynamic.generated_content.characters,
            *snapshot.dynamic.generated_content.events,
        )
    }

    reserved_ids = (
        existing_location_ids
        | existing_character_ids
        | existing_faction_ids
        | existing_item_ids
        | existing_generated_ids
    )
    _reject_local_id_collisions(draft, reserved_ids)

    location_map, character_map, event_map = _allocate_formal_ids(
        draft,
        snapshot.core.turn,
        existing_generated_ids,
    )

    locations = _validate_locations(
        draft.locations,
        existing_location_ids,
        location_map,
    )
    characters = _validate_characters(
        draft.characters, existing_faction_ids, character_map
    )
    events = _validate_events(
        draft.events,
        policy,
        existing_location_ids,
        existing_character_ids,
        location_map,
        character_map,
        event_map,
        trusted_seed,
    )

    _validate_total_effect_budget(events, policy)

    return ValidatedGeneratedContent(
        source_seed_id=trusted_seed.id,
        generator_version=generator_version,
        locations=locations,
        characters=characters,
        events=events,
    )


def _validate_counts(
    draft: ContentGenerationDraft,
    policy: ContentGenerationPolicy,
) -> None:
    """检查每回合新增内容数量不超过策略上限。"""
    if len(draft.locations) > policy.max_locations_per_turn:
        raise ContentValidationError("too many locations in content generation draft")
    if len(draft.characters) > policy.max_characters_per_turn:
        raise ContentValidationError("too many characters in content generation draft")
    if len(draft.events) > policy.max_events_per_turn:
        raise ContentValidationError("too many events in content generation draft")

    for event in draft.events:
        if len(event.choices) > policy.max_options_per_event:
            raise ContentValidationError("too many choices in generated event")


def _reject_local_id_collisions(
    draft: ContentGenerationDraft,
    reserved_ids: set[str],
) -> None:
    """临时 ID 不能冒充已有实体或正式内容 ID。"""
    local_ids = [
        *(item.local_id for item in draft.locations),
        *(item.local_id for item in draft.characters),
        *(item.local_id for item in draft.events),
    ]
    for local_id in local_ids:
        if local_id in reserved_ids:
            raise ContentValidationError(
                f"local id {local_id!r} collides with an existing id"
            )


def _allocate_formal_ids(
    draft: ContentGenerationDraft,
    turn: int,
    existing_generated_ids: set[str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """为地点、人物和事件分配本回合唯一的正式 ID。"""
    location_map = _allocate_sequence(
        "location",
        len(draft.locations),
        turn,
        existing_generated_ids,
    )
    character_map = _allocate_sequence(
        "character",
        len(draft.characters),
        turn,
        existing_generated_ids,
    )
    event_map = _allocate_sequence(
        "event",
        len(draft.events),
        turn,
        existing_generated_ids,
    )
    return (
        dict(
            zip((item.local_id for item in draft.locations), location_map, strict=True)
        ),
        dict(
            zip(
                (item.local_id for item in draft.characters), character_map, strict=True
            )
        ),
        dict(zip((item.local_id for item in draft.events), event_map, strict=True)),
    )


def _allocate_sequence(
    kind: str,
    count: int,
    turn: int,
    existing_ids: set[str],
) -> list[str]:
    """生成 count 个不与已有 ID 冲突的正式 ID。"""
    ids: list[str] = []
    ordinal = 1
    while len(ids) < count:
        candidate = f"gen.{kind}.{turn}.{ordinal}"
        if candidate not in existing_ids and candidate not in ids:
            ids.append(candidate)
        ordinal += 1
    return ids


def _validate_locations(
    locations: tuple[LocationDraft, ...],
    existing_location_ids: set[str],
    location_map: dict[str, str],
) -> tuple[ValidatedLocation, ...]:
    """校验地点引用并生成正式地点。"""
    validated: list[ValidatedLocation] = []
    for location in locations:
        connected_to: list[str] = []
        for target in location.connected_to:
            if target == location.local_id:
                raise ContentValidationError("location cannot connect to itself")
            if target in location_map:
                connected_to.append(location_map[target])
            elif target in existing_location_ids:
                connected_to.append(target)
            else:
                raise ContentValidationError(
                    f"location {location.local_id!r} references unknown {target!r}"
                )
        validated.append(
            ValidatedLocation(
                id=location_map[location.local_id],
                name=location.name,
                description=location.description,
                location_type=location.location_type,
                tags=location.tags,
                connected_to=tuple(connected_to),
            )
        )
    return tuple(validated)


def _validate_characters(
    characters: tuple[CharacterDraft, ...],
    existing_faction_ids: set[str],
    character_map: dict[str, str],
) -> tuple[ValidatedCharacter, ...]:
    """校验人物所属势力并生成正式人物。"""
    validated: list[ValidatedCharacter] = []
    for character in characters:
        if (
            character.faction_id is not None
            and character.faction_id not in existing_faction_ids
        ):
            raise ContentValidationError(
                f"character {character.local_id!r} "
                f"references unknown faction {character.faction_id!r}"
            )
        validated.append(
            ValidatedCharacter(
                id=character_map[character.local_id],
                name=character.name,
                role=character.role,
                faction_id=character.faction_id,
                description=character.description,
                traits=character.traits,
                relationship_hint=character.relationship_hint,
            )
        )
    return tuple(validated)


def _validate_events(
    events: tuple[EventDraft, ...],
    policy: ContentGenerationPolicy,
    existing_location_ids: set[str],
    existing_character_ids: set[str],
    location_map: dict[str, str],
    character_map: dict[str, str],
    event_map: dict[str, str],
    trusted_seed: SeedEvent,
) -> tuple[ValidatedEvent, ...]:
    """校验事件引用、选项和效果。"""
    validated: list[ValidatedEvent] = []
    for event in events:
        if event.location_id is None:
            location_id = None
        elif event.location_id in location_map:
            location_id = location_map[event.location_id]
        elif event.location_id in existing_location_ids:
            location_id = event.location_id
        else:
            raise ContentValidationError(
                f"event {event.local_id!r} "
                f"references unknown location {event.location_id!r}"
            )

        character_ids = _rewrite_character_ids(
            event,
            existing_character_ids,
            character_map,
        )
        choices = _validate_choices(event, policy, event_map[event.local_id])
        validated.append(
            ValidatedEvent(
                event_id=event_map[event.local_id],
                derived_from_seed_id=_require_derived_seed(event, trusted_seed.id),
                title=event.title,
                scene_text=event.scene_text,
                location_id=location_id,
                character_ids=character_ids,
                choices=choices,
                category=event.category or trusted_seed.category,
                worldline_id=(
                    event.worldline_id
                    if event.worldline_id is not None
                    else trusted_seed.worldline_id
                ),
                stage=(event.stage if event.stage is not None else trusted_seed.stage),
                conditions=event.conditions or trusted_seed.conditions,
                weight=(
                    event.weight if event.weight is not None else trusted_seed.weight
                ),
                location_ids=event.location_ids or trusted_seed.location_ids,
                time_slots=event.time_slots or trusted_seed.time_slots,
                required_state=(
                    event.required_state
                    if event.required_state is not None
                    else trusted_seed.required_state
                ),
                fallback_scene_text=event.scene_text,
                ai_prompt=event.ai_prompt or trusted_seed.ai_prompt,
                narrative_brief=event.narrative_brief or trusted_seed.narrative_brief,
            )
        )
    return tuple(validated)


def _require_derived_seed(event: EventDraft, seed_id: str) -> str:
    """事件必须从当前可信种子派生。"""
    if event.derived_from_seed_id != seed_id:
        raise ContentValidationError(
            f"generated event seed {event.derived_from_seed_id!r} "
            f"does not match trusted seed {seed_id!r}"
        )
    return seed_id


def _rewrite_character_ids(
    event: EventDraft,
    existing_character_ids: set[str],
    character_map: dict[str, str],
) -> tuple[str, ...]:
    """把事件中的人物临时 ID 重写为正式 ID。"""
    rewritten: list[str] = []
    for character_id in event.character_ids:
        if character_id in character_map:
            rewritten.append(character_map[character_id])
        elif character_id in existing_character_ids:
            rewritten.append(character_id)
        else:
            raise ContentValidationError(
                f"event {event.local_id!r} "
                f"references unknown character {character_id!r}"
            )
    return tuple(rewritten)


def _validate_choices(
    event: EventDraft,
    policy: ContentGenerationPolicy,
    event_id: str,
) -> tuple[ValidatedChoice, ...]:
    """校验事件选项并转换效果。"""
    validated: list[ValidatedChoice] = []
    for choice in event.choices:
        if len(choice.effects) > policy.max_effects_per_choice:
            raise ContentValidationError("too many effects in generated choice")

        effects = tuple(_validate_effect(effect, policy) for effect in choice.effects)
        validated.append(
            ValidatedChoice(
                choice_id=f"{event_id}.choice.{choice.local_id}",
                label=choice.label,
                result_text=choice.result_text,
                result_hint=choice.result_hint or choice.result_text,
                effects=effects,
            )
        )
    return tuple(validated)


def _validate_effect(
    effect: EffectDraft,
    policy: ContentGenerationPolicy,
) -> StandardEffect:
    """把 EffectDraft 校验并转换为 StandardEffect。"""
    if effect.effect_type in policy.forbidden_effect_types:
        raise ContentValidationError(f"forbidden effect type: {effect.effect_type!r}")
    if effect.effect_type not in policy.allowed_effect_types:
        raise ContentValidationError(f"effect type not allowed: {effect.effect_type!r}")
    if effect.effect_type not in _SUPPORTED_AMOUNT_EFFECTS:
        raise ContentValidationError(
            f"effect type not supported yet: {effect.effect_type!r}"
        )

    bound = next(
        (
            item
            for item in policy.effect_bounds
            if item.effect_type == effect.effect_type
        ),
        None,
    )
    if bound is None:
        raise ContentValidationError(f"missing effect bound for {effect.effect_type!r}")

    if effect.amount is None:
        raise ContentValidationError(f"{effect.effect_type} requires an integer amount")
    if effect.value is not None:
        raise ContentValidationError(
            f"{effect.effect_type} does not support a boolean value"
        )
    if effect.target_id not in {None, "player"}:
        raise ContentValidationError(
            f"{effect.effect_type} target must be player or None"
        )

    if not bound.min_amount <= effect.amount <= bound.max_amount:
        raise ContentValidationError(
            f"{effect.effect_type} amount {effect.amount} is out of bounds"
        )

    return StandardEffect(
        effect_type=effect.effect_type,
        target_id=effect.target_id,
        amount=effect.amount,
        value=None,
    )


def _validate_total_effect_budget(
    events: tuple[ValidatedEvent, ...],
    policy: ContentGenerationPolicy,
) -> None:
    """检查单回合效果总预算。"""
    total = 0
    for event in events:
        for choice in event.choices:
            for effect in choice.effects:
                total += abs(effect.amount or 0)

    if total > policy.max_total_effect_per_turn:
        raise ContentValidationError("total effect budget exceeded")


def validated_event_to_seed_event(event: ValidatedEvent) -> SeedEvent:
    """把已验证生成事件转换为统一 SeedEvent。

    这是基础内容、插件内容和 AI 生成内容共用同一候选池契约的关键入口。
    """
    return SeedEvent(
        id=event.event_id,
        category=event.category,
        worldline_id=event.worldline_id,
        stage=event.stage,
        conditions=event.conditions,
        weight=event.weight,
        location_ids=event.location_ids,
        time_slots=event.time_slots,
        required_state=event.required_state,
        fallback_scene_text=event.fallback_scene_text,
        ai_prompt=event.ai_prompt,
        narrative_brief=event.narrative_brief,
        choices=tuple(
            SeedChoice(
                id=choice.choice_id,
                fallback_label=choice.label,
                result_hint=choice.result_hint,
                fallback_result_text=choice.result_text,
                effects=choice.effects,
            )
            for choice in event.choices
        ),
        source_plugin_id=None,
    )
