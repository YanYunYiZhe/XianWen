"""新 GameState 结构测试。"""

from dataclasses import FrozenInstanceError

import pytest

from xianwen.core import (
    ChronicleEntry,
    ForeshadowBook,
    GameState,
    PlayerState,
    ReputationValue,
    StandardEffect,
    WorldSnapshot,
)


def test_default_game_state_has_new_prd_fields() -> None:
    state = GameState()

    assert isinstance(state.player, PlayerState)
    assert isinstance(state.world, WorldSnapshot)
    assert state.chronicle == ()
    assert isinstance(state.foreshadows, ForeshadowBook)


def test_game_state_is_immutable() -> None:
    state = GameState()

    with pytest.raises(FrozenInstanceError):
        state.world = WorldSnapshot()


def test_player_state_can_hold_reputation() -> None:
    player = PlayerState(
        reputation=(ReputationValue(faction_id="base.sect", value=10),),
    )

    assert player.reputation[0].faction_id == "base.sect"
    assert player.reputation[0].value == 10


def test_chronicle_holds_applied_effects() -> None:
    entry = ChronicleEntry(
        id="chr.1",
        turn=1,
        year=1,
        event_id="base.morning_training",
        choice_id="cultivate",
        location_id=None,
        involved_character_ids=(),
        summary="你完成了一次修炼。",
        applied_effects=(StandardEffect(effect_type="cultivation_delta", amount=1),),
        summary_source="fallback",
    )

    state = GameState(chronicle=(entry,))

    assert state.chronicle[0].applied_effects[0].amount == 1
