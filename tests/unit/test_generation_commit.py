"""生成内容原子登记测试。"""

import json

import pytest

from xianwen.core import (
    CharacterDraft,
    ChoiceDraft,
    ContentGenerationDraft,
    ContentGenerationPolicy,
    EffectBound,
    EffectDraft,
    EventDraft,
    GeneratedContentConflictError,
    LocationDraft,
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    StateVersionConflictError,
    commit_generated_content,
    create_initial_world,
    validate_content_generation,
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


def _validated():
    snapshot = create_initial_world()
    bundle = validate_content_generation(
        _make_draft(),
        snapshot,
        _make_policy(),
        trusted_seed=_make_seed(),
        generator_version="test.1",
    )
    return snapshot, bundle


def test_commit_writes_locations_characters_events_and_metadata() -> None:
    snapshot, bundle = _validated()

    committed = commit_generated_content(
        snapshot,
        bundle,
        expected_version=1,
    )

    assert committed.core.state_version == 2
    assert committed.core.turn == 1
    assert committed.core.year == 1

    assert committed.dynamic.locations[0].id == "gen.location.1.1"
    assert committed.dynamic.characters[0].id == "gen.character.1.1"
    assert committed.dynamic.generated_content.locations[0].kind == "location"
    assert committed.dynamic.generated_content.characters[0].kind == "character"
    assert committed.dynamic.generated_content.events[0].kind == "event"

    definition = committed.dynamic.generated_content.events[0].definition
    assert "gen.event.1.1" in json.loads(definition)["event_id"]


def test_commit_does_not_modify_original_snapshot() -> None:
    snapshot, bundle = _validated()

    commit_generated_content(snapshot, bundle, expected_version=1)

    assert snapshot.core.state_version == 1
    assert snapshot.dynamic.locations == ()
    assert snapshot.dynamic.generated_content.locations == ()


def test_stale_version_is_rejected() -> None:
    snapshot, bundle = _validated()
    committed = commit_generated_content(
        snapshot,
        bundle,
        expected_version=1,
    )

    with pytest.raises(StateVersionConflictError):
        commit_generated_content(
            committed,
            bundle,
            expected_version=1,
        )


def test_reused_bundle_conflicts_with_existing_ids() -> None:
    snapshot, bundle = _validated()
    committed = commit_generated_content(
        snapshot,
        bundle,
        expected_version=1,
    )

    with pytest.raises(GeneratedContentConflictError):
        commit_generated_content(
            committed,
            bundle,
            expected_version=2,
        )
