"""受控内容生成草案和策略结构测试。"""

import pytest

from xianwen.core import (
    CharacterDraft,
    ChoiceDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    EffectBound,
    EffectDraft,
    EventDraft,
    LocationDraft,
)


def _make_policy() -> ContentGenerationPolicy:
    """构造测试用策略，生产默认值尚未冻结。"""
    return ContentGenerationPolicy(
        max_locations_per_turn=1,
        max_characters_per_turn=1,
        max_events_per_turn=1,
        max_options_per_event=3,
        max_effects_per_choice=2,
        allowed_effect_types=("cultivation_delta", "luck_delta"),
        effect_bounds=(
            EffectBound(
                effect_type="cultivation_delta",
                min_amount=0,
                max_amount=2,
            ),
        ),
        max_total_effect_per_turn=3,
        forbidden_effect_types=("grant_invincibility",),
        max_active_foreshadows=2,
        max_model_calls_per_turn=3,
    )


def _make_draft() -> ContentGenerationDraft:
    """构造一次包含地点、人物、事件和选项的合法草案。"""
    return ContentGenerationDraft(
        derived_from_seed_id="base.test_seed",
        locations=(
            LocationDraft(
                local_id="loc.1",
                name="废弃山祠",
                description="山中荒废的小祠。",
                location_type="ruin",
                tags=("ruin", "mystery"),
                connected_to=(),
            ),
        ),
        characters=(
            CharacterDraft(
                local_id="char.1",
                name="守祠人",
                role="神秘老人",
                faction_id=None,
                description="守着一座无人祭拜的山祠。",
                traits=("silent", "knowledgeable"),
                relationship_hint="警惕外来者",
            ),
        ),
        events=(
            EventDraft(
                local_id="event.1",
                derived_from_seed_id="base.test_seed",
                title="山祠夜谈",
                scene_text="你在废弃山祠遇见守祠人。",
                location_id="loc.1",
                character_ids=("char.1",),
                choices=(
                    ChoiceDraft(
                        local_id="choice.1",
                        label="交谈",
                        result_text="守祠人告诉了你一段旧事。",
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
                        result_text="你转身离开山祠。",
                    ),
                ),
            ),
        ),
    )


def test_valid_content_generation_draft_is_created() -> None:
    draft = _make_draft()
    policy = _make_policy()

    assert draft.derived_from_seed_id == "base.test_seed"
    assert len(draft.locations) == 1
    assert len(draft.characters) == 1
    assert len(draft.events) == 1
    assert policy.max_events_per_turn == 1


def test_entity_local_ids_must_be_unique_across_types() -> None:
    with pytest.raises(ValueError, match="local_ids"):
        ContentGenerationDraft(
            derived_from_seed_id="base.test_seed",
            locations=(
                LocationDraft(
                    local_id="same-id",
                    name="地点",
                    description="描述",
                    location_type="ruin",
                    tags=(),
                    connected_to=(),
                ),
            ),
            characters=(
                CharacterDraft(
                    local_id="same-id",
                    name="人物",
                    role="角色",
                    faction_id=None,
                    description="描述",
                    traits=(),
                    relationship_hint=None,
                ),
            ),
        )


def test_event_requires_two_to_four_choices() -> None:
    with pytest.raises(ValueError, match="2 to 4"):
        EventDraft(
            local_id="event.1",
            derived_from_seed_id=None,
            title="测试事件",
            scene_text="测试场景",
            location_id=None,
            character_ids=(),
            choices=(
                ChoiceDraft(
                    local_id="choice.1",
                    label="唯一选项",
                    result_text="结果",
                ),
            ),
        )


def test_policy_rejects_overlapping_effect_types() -> None:
    with pytest.raises(ValueError, match="allowed and forbidden"):
        ContentGenerationPolicy(
            max_locations_per_turn=1,
            max_characters_per_turn=1,
            max_events_per_turn=1,
            max_options_per_event=3,
            max_effects_per_choice=2,
            allowed_effect_types=("cultivation_delta",),
            effect_bounds=(),
            max_total_effect_per_turn=3,
            forbidden_effect_types=("cultivation_delta",),
            max_active_foreshadows=2,
            max_model_calls_per_turn=3,
        )


def test_effect_bound_rejects_reversed_range() -> None:
    with pytest.raises(ValueError, match="min_amount"):
        EffectBound(
            effect_type="cultivation_delta",
            min_amount=5,
            max_amount=1,
        )
