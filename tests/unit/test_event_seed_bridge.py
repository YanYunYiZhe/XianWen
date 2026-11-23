"""生成事件到 SeedEvent 的契约桥接测试。"""

from dataclasses import replace

from xianwen.core import (
    CharacterDraft,
    ChoiceDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    EffectBound,
    EffectDraft,
    EventDraft,
    LocationDraft,
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    StateRequirement,
    create_initial_world,
    validate_content_generation,
    validated_event_to_seed_event,
)


def _make_policy() -> ContentGenerationPolicy:
    """构造测试策略。"""
    return ContentGenerationPolicy(
        max_locations_per_turn=1,
        max_characters_per_turn=1,
        max_events_per_turn=1,
        max_options_per_event=3,
        max_effects_per_choice=2,
        allowed_effect_types=("cultivation_delta",),
        effect_bounds=(
            EffectBound(
                effect_type="cultivation_delta",
                min_amount=0,
                max_amount=2,
            ),
        ),
        max_total_effect_per_turn=3,
        forbidden_effect_types=(),
        max_active_foreshadows=2,
        max_model_calls_per_turn=3,
    )


def _make_seed() -> SeedEvent:
    """构造可信来源种子。"""
    return SeedEvent(
        id="base.source_seed",
        category="daily",
        fallback_scene_text="来源种子后备场景。",
        ai_prompt="来源种子 AI 提示。",
        narrative_brief=NarrativeBrief(
            premise="来源种子剧情。",
            tone="平静",
            required_beats=("来源节点",),
            allowed_improvisation=("来源细节",),
            forbidden_content=("不能新增效果",),
        ),
        choices=(
            SeedChoice(
                id="a",
                fallback_label="甲",
                result_hint="甲提示",
                fallback_result_text="甲结果",
            ),
            SeedChoice(
                id="b",
                fallback_label="乙",
                result_hint="乙提示",
                fallback_result_text="乙结果",
            ),
        ),
        worldline_id="base.main",
        stage="opening",
        weight=1,
        location_ids=("base.town",),
        time_slots=("morning",),
        required_state=StateRequirement(min_cultivation=1),
    )


def _make_draft() -> ContentGenerationDraft:
    """构造派生事件草案。"""
    return ContentGenerationDraft(
        derived_from_seed_id="base.source_seed",
        locations=(
            LocationDraft(
                local_id="loc.1",
                name="山祠",
                description="山中小祠。",
                location_type="ruin",
                tags=(),
                connected_to=(),
            ),
        ),
        characters=(
            CharacterDraft(
                local_id="char.1",
                name="守祠人",
                role="神秘老人",
                faction_id=None,
                description="守着小祠。",
                traits=(),
                relationship_hint=None,
            ),
        ),
        events=(
            EventDraft(
                local_id="event.1",
                derived_from_seed_id="base.source_seed",
                title="山祠夜谈",
                scene_text="你在山祠遇见守祠人。",
                location_id="loc.1",
                character_ids=("char.1",),
                choices=(
                    ChoiceDraft(
                        local_id="choice.1",
                        label="交谈",
                        result_text="守祠人告诉你一段旧事。",
                        result_hint="玩家与守祠人交谈。",
                        effects=(
                            EffectDraft(
                                effect_type="cultivation_delta",
                                amount=1,
                            ),
                        ),
                    ),
                    ChoiceDraft(
                        local_id="choice.2",
                        label="离开",
                        result_text="你转身离开。",
                    ),
                ),
            ),
        ),
    )


def _validate():
    snapshot = create_initial_world()
    bundle = validate_content_generation(
        _make_draft(),
        snapshot,
        _make_policy(),
        trusted_seed=_make_seed(),
        generator_version="test.1",
    )
    return bundle


def test_event_inherits_seed_selection_metadata() -> None:
    event = _validate().events[0]

    assert event.category == "daily"
    assert event.worldline_id == "base.main"
    assert event.stage == "opening"
    assert event.weight == 1
    assert event.location_ids == ("base.town",)
    assert event.time_slots == ("morning",)
    assert event.required_state == StateRequirement(min_cultivation=1)
    assert event.fallback_scene_text == "你在山祠遇见守祠人。"
    assert event.ai_prompt == "来源种子 AI 提示。"
    assert event.narrative_brief.premise == "来源种子剧情。"


def test_event_can_override_selection_metadata() -> None:
    draft = replace(
        _make_draft(),
        events=(
            replace(
                _make_draft().events[0],
                category="mystery",
                weight=2,
                location_ids=("loc.1",),
            ),
        ),
    )

    bundle = validate_content_generation(
        draft,
        create_initial_world(),
        _make_policy(),
        trusted_seed=_make_seed(),
        generator_version="test.1",
    )

    assert bundle.events[0].category == "mystery"
    assert bundle.events[0].weight == 2
    assert bundle.events[0].location_ids == ("loc.1",)


def test_bridge_builds_seed_event_with_choices_and_effects() -> None:
    seed = validated_event_to_seed_event(_validate().events[0])

    assert seed.id == "gen.event.1.1"
    assert seed.category == "daily"
    assert seed.worldline_id == "base.main"
    assert seed.weight == 1
    assert seed.fallback_scene_text == "你在山祠遇见守祠人。"
    assert len(seed.choices) == 2
    assert seed.choices[0].id == "gen.event.1.1.choice.choice.1"
    assert seed.choices[0].fallback_label == "交谈"
    assert seed.choices[0].result_hint == "玩家与守祠人交谈。"
    assert seed.choices[0].effects[0].effect_type == "cultivation_delta"


def test_bridge_result_hint_falls_back_to_result_text() -> None:
    seed = validated_event_to_seed_event(_validate().events[0])

    assert seed.choices[1].result_hint == "你转身离开。"
