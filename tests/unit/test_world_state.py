"""世界状态分层和版本冲突测试。"""

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from xianwen.core import (
    DynamicWorldState,
    InvalidStateTransitionError,
    StateTransition,
    StateVersionConflictError,
    WorldFlag,
    advance_world,
    apply_state_transition,
    build_state_transition,
    create_initial_world,
)


def test_initial_world_has_core_authority() -> None:
    snapshot = create_initial_world(world_seed=42)

    assert snapshot.core.turn == 1
    assert snapshot.core.year == 1
    assert snapshot.core.world_seed == 42
    assert snapshot.core.state_version == 1


def test_world_snapshot_is_immutable() -> None:
    snapshot = create_initial_world()

    with pytest.raises(FrozenInstanceError):
        snapshot.core.year = 2


def test_dynamic_state_does_not_duplicate_core_fields() -> None:
    dynamic_fields = {item.name for item in fields(DynamicWorldState)}
    core_fields = {
        "turn",
        "year",
        "worldline_id",
        "worldline_stage",
        "state_version",
        "content_version",
    }

    assert dynamic_fields.isdisjoint(core_fields)


def test_advance_world_updates_turn_year_and_version() -> None:
    initial = create_initial_world()
    advanced = advance_world(initial)

    assert advanced.core.turn == 2
    assert advanced.core.year == 2
    assert advanced.core.state_version == 2
    assert initial.core.turn == 1
    assert initial.core.year == 1


def test_dynamic_only_transition_keeps_turn_and_year() -> None:
    initial = create_initial_world()

    new_dynamic = replace(
        initial.dynamic,
        flags=(WorldFlag(key="clue.found"),),
    )
    transition = build_state_transition(
        initial,
        new_dynamic=new_dynamic,
    )
    committed = apply_state_transition(initial, transition)

    assert committed.core.turn == 1
    assert committed.core.year == 1
    assert committed.core.state_version == 2
    assert committed.dynamic.flags == new_dynamic.flags


def test_stale_transition_is_rejected() -> None:
    initial = create_initial_world()
    transition = build_state_transition(initial, advance_time=True)
    current = apply_state_transition(initial, transition)

    with pytest.raises(StateVersionConflictError):
        apply_state_transition(current, transition)


def test_year_cannot_change_independently_of_turn() -> None:
    initial = create_initial_world()
    invalid_core = replace(
        initial.core,
        year=2,
        state_version=2,
    )
    transition = StateTransition(
        expected_version=1,
        new_core=invalid_core,
        new_dynamic=initial.dynamic,
    )

    with pytest.raises(InvalidStateTransitionError):
        apply_state_transition(initial, transition)


def test_worldline_cannot_change_during_normal_transition() -> None:
    initial = create_initial_world()
    invalid_core = replace(
        initial.core,
        worldline_id="base.changed",
        state_version=2,
    )
    transition = StateTransition(
        expected_version=1,
        new_core=invalid_core,
        new_dynamic=initial.dynamic,
    )

    with pytest.raises(InvalidStateTransitionError):
        apply_state_transition(initial, transition)
