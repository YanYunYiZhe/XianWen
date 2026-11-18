"""Unit tests for the first-phase core turn flow."""

import pytest

from xianwen.core import (
    InvalidChoiceError,
    InvalidEventError,
    apply_choice,
    get_current_event,
    new_game,
)


def test_new_game_has_expected_initial_state() -> None:
    state = new_game()

    assert state.year == 1
    assert state.cultivation == 0
    assert state.ended is False


def test_current_event_is_the_fixed_morning_training() -> None:
    event = get_current_event(new_game())

    assert event.id == "base.morning_training"
    assert event.scene_text
    assert {choice.id for choice in event.choices} == {"cultivate", "rest"}


def test_cultivate_advances_year_and_adds_one_cultivation() -> None:
    result = apply_choice(new_game(), "base.morning_training", "cultivate")

    assert result.state.year == 2
    assert result.state.cultivation == 1
    assert result.choice_id == "cultivate"
    assert result.result_text


def test_rest_advances_year_and_keeps_cultivation() -> None:
    result = apply_choice(new_game(), "base.morning_training", "rest")

    assert result.state.year == 2
    assert result.state.cultivation == 0
    assert result.choice_id == "rest"
    assert result.result_text


def test_unknown_event_raises_invalid_event_error() -> None:
    with pytest.raises(InvalidEventError):
        apply_choice(new_game(), "base.unknown_event", "cultivate")


def test_unknown_choice_raises_and_leaves_original_state_unchanged() -> None:
    state = new_game()

    with pytest.raises(InvalidChoiceError):
        apply_choice(state, "base.morning_training", "unknown_choice")

    assert state == new_game()
