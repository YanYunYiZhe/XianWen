"""受控内容生成确定性校验测试。"""

from dataclasses import replace

import pytest

from xianwen.core import (
    CharacterDraft,
    ChoiceDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    ContentValidationError,
    EffectBound,
    EffectDraft,
    EventDraft,
    LocationDraft,
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    create_initial_world,
    validate_content_generation,
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
            EffectBound(
                effect_type="luck_delta",
                min_amount=-1,
                max_amount=1,
            ),
        ),
        max_total_effect_per_turn=3,
        forbidden_effect_types=("grant_invincibility",),
        max_active_foreshadows=2,
        max_model_calls_per_turn=3,
    )


def _make_seed() -> SeedEvent:
    """构造可信种子。"""
    return SeedEvent(
        id="base.test_seed",
        category="daily",
        fallback_scene_text="测试场景",
        ai_prompt="测试提示",
        narrative_brief=NarrativeBrief(
            premise="测试",
            tone="平静",
            required_beats=(),
            allowed_improvisation=(),
            forbidden_content=(),
        ),
        choices=(
            SeedChoice(
                id="a", fallback_label="甲", result_hint="甲", fallback_result_text="甲"
            ),
            SeedChoice(
                id="b", fallback_label="乙", result_hint="乙", fallback_result_text="乙"
            ),
        ),
    )


def _make_draft() -> ContentGenerationDraft:
    """构造合法草案。"""
    return ContentGenerationDraft(
        derived_from_seed_id="base.test_seed",
        locations=(
            LocationDraft(
                local_id="loc.1",
                name="废弃山祠",
                description="山中荒废的小祠。",
                location_type="ruin",
                tags=("ruin",),
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
                traits=("silent",),
                relationship_hint=None,
            ),
        ),
        events=(
            EventDraft(
                local_id="event.1",
                derived_from_seed_id="base.test_seed",
                title="山祠夜谈",
                scene_text="你在山祠遇见守祠人。",
                location_id="loc.1",
                character_ids=("char.1",),
                choices=(
                    ChoiceDraft(
                        local_id="choice.1",
                        label="交谈",
                        result_text="守祠人告诉你一段旧事。",
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


def test_valid_draft_gets_formal_ids_and_rewritten_references() -> None:
    bundle = validate_content_generation(
        _make_draft(),
        create_initial_world(),
        _make_policy(),
        trusted_seed=_make_seed(),
        generator_version="test.1",
    )

    assert bundle.source_seed_id == "base.test_seed"
    assert bundle.locations[0].id == "gen.location.1.1"
    assert bundle.characters[0].id == "gen.character.1.1"
    assert bundle.events[0].event_id == "gen.event.1.1"
    assert bundle.events[0].location_id == "gen.location.1.1"
    assert bundle.events[0].character_ids == ("gen.character.1.1",)
    assert bundle.events[0].choices[0].choice_id == ("gen.event.1.1.choice.choice.1")
    assert bundle.events[0].choices[0].effects[0].effect_type == ("cultivation_delta")


def test_location_reference_is_rewritten() -> None:
    draft = replace(
        _make_draft(),
        locations=(
            LocationDraft(
                local_id="loc.1",
                name="山祠",
                description="山中小祠。",
                location_type="ruin",
                tags=(),
                connected_to=("loc.2",),
            ),
            LocationDraft(
                local_id="loc.2",
                name="山道",
                description="通往山祠的小路。",
                location_type="path",
                tags=(),
                connected_to=(),
            ),
        ),
    )
    policy = replace(_make_policy(), max_locations_per_turn=2)

    bundle = validate_content_generation(
        draft,
        create_initial_world(),
        policy,
        trusted_seed=_make_seed(),
        generator_version="test.1",
    )

    assert bundle.locations[0].connected_to == ("gen.location.1.2",)


def test_unknown_location_reference_is_rejected() -> None:
    draft = replace(
        _make_draft(),
        locations=(
            LocationDraft(
                local_id="loc.1",
                name="山祠",
                description="山中小祠。",
                location_type="ruin",
                tags=(),
                connected_to=("loc.missing",),
            ),
        ),
    )

    with pytest.raises(ContentValidationError, match="unknown"):
        validate_content_generation(
            draft,
            create_initial_world(),
            _make_policy(),
            trusted_seed=_make_seed(),
            generator_version="test.1",
        )


def test_source_seed_mismatch_is_rejected() -> None:
    draft = replace(_make_draft(), derived_from_seed_id="base.other_seed")

    with pytest.raises(ContentValidationError, match="does not match"):
        validate_content_generation(
            draft,
            create_initial_world(),
            _make_policy(),
            trusted_seed=_make_seed(),
            generator_version="test.1",
        )


def test_forbidden_effect_is_rejected() -> None:
    draft = replace(
        _make_draft(),
        events=(
            replace(
                _make_draft().events[0],
                choices=(
                    replace(
                        _make_draft().events[0].choices[0],
                        effects=(
                            EffectDraft(
                                effect_type="grant_invincibility",
                                amount=1,
                            ),
                        ),
                    ),
                    _make_draft().events[0].choices[1],
                ),
            ),
        ),
    )

    with pytest.raises(ContentValidationError, match="forbidden"):
        validate_content_generation(
            draft,
            create_initial_world(),
            _make_policy(),
            trusted_seed=_make_seed(),
            generator_version="test.1",
        )


def test_effect_out_of_bounds_is_rejected() -> None:
    draft = replace(
        _make_draft(),
        events=(
            replace(
                _make_draft().events[0],
                choices=(
                    replace(
                        _make_draft().events[0].choices[0],
                        effects=(
                            EffectDraft(
                                effect_type="cultivation_delta",
                                amount=99,
                            ),
                        ),
                    ),
                    _make_draft().events[0].choices[1],
                ),
            ),
        ),
    )

    with pytest.raises(ContentValidationError, match="out of bounds"):
        validate_content_generation(
            draft,
            create_initial_world(),
            _make_policy(),
            trusted_seed=_make_seed(),
            generator_version="test.1",
        )


def test_total_effect_budget_is_rejected() -> None:
    policy = replace(_make_policy(), max_total_effect_per_turn=0)
    draft = _make_draft()

    with pytest.raises(ContentValidationError, match="budget"):
        validate_content_generation(
            draft,
            create_initial_world(),
            policy,
            trusted_seed=_make_seed(),
            generator_version="test.1",
        )
