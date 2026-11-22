"""新种子回合原子结算测试。"""

from dataclasses import replace

import pytest

from xianwen.core import (
    GameState,
    InvalidSeedTurnError,
    NarrativeBrief,
    RenderedEvent,
    SeedChoice,
    SeedEvent,
    StandardEffect,
    StateVersionConflictError,
    UnsupportedStandardEffectError,
    apply_seed_choice,
    render_fallback_event,
)


def _make_seed(
    effects: tuple[StandardEffect, ...] = (
        StandardEffect(effect_type="cultivation_delta", amount=1),
    ),
) -> SeedEvent:
    """构造一个带有效效果和无效果选项的测试种子。"""
    return SeedEvent(
        id="base.test_turn",
        category="daily",
        fallback_scene_text="清晨，你准备开始今日修行。",
        ai_prompt="扩写清晨修行场景。",
        narrative_brief=NarrativeBrief(
            premise="玩家决定是否修炼。",
            tone="平静",
            required_beats=("描写清晨", "让玩家选择"),
            allowed_improvisation=("鸟鸣",),
            forbidden_content=("不能修改效果",),
        ),
        choices=(
            SeedChoice(
                id="cultivate",
                fallback_label="修炼",
                result_hint="你开始运转功法。",
                fallback_result_text="你完成了一次修炼。",
                effects=effects,
            ),
            SeedChoice(
                id="rest",
                fallback_label="休息",
                result_hint="你决定休息。",
                fallback_result_text="你休息了一段时间。",
            ),
        ),
    )


def test_seed_choice_updates_player_world_and_chronicle() -> None:
    state = GameState()
    seed = _make_seed()
    rendered = render_fallback_event(seed)

    result = apply_seed_choice(
        state,
        seed,
        rendered,
        "cultivate",
        expected_version=1,
    )

    assert result.state.player.cultivation == 1
    assert result.state.world.core.turn == 2
    assert result.state.world.core.year == 2
    assert result.state.world.core.state_version == 2
    assert len(result.state.chronicle) == 1
    assert result.state.chronicle[0].event_id == "base.test_turn"
    assert result.state.chronicle[0].choice_id == "cultivate"
    assert result.state.chronicle[0].summary_source == "fallback"

    # 原状态必须保持不变，证明结算采用不可变快照。
    assert state.player.cultivation == 0
    assert state.world.core.turn == 1
    assert state.chronicle == ()


def test_stale_version_is_rejected() -> None:
    state = GameState()
    seed = _make_seed()
    rendered = render_fallback_event(seed)

    first = apply_seed_choice(
        state,
        seed,
        rendered,
        "cultivate",
        expected_version=1,
    )

    with pytest.raises(StateVersionConflictError):
        apply_seed_choice(
            first.state,
            seed,
            rendered,
            "cultivate",
            expected_version=1,
        )


def test_rendered_text_cannot_change_effect() -> None:
    state = GameState()
    seed = _make_seed()
    rendered = render_fallback_event(seed)
    tampered_choices = tuple(
        replace(choice, result_text="你的修为增加了 999 点。")
        for choice in rendered.choices
    )
    tampered = RenderedEvent(
        seed_id=rendered.seed_id,
        scene_text=rendered.scene_text,
        choices=tampered_choices,
    )

    result = apply_seed_choice(
        state,
        seed,
        tampered,
        "cultivate",
        expected_version=1,
    )

    # 效果只能来自 SeedChoice.effects。
    assert result.state.player.cultivation == 1


def test_tampered_seed_id_is_rejected() -> None:
    state = GameState()
    seed = _make_seed()
    rendered = render_fallback_event(seed)
    tampered = replace(rendered, seed_id="base.other_seed")

    with pytest.raises(InvalidSeedTurnError, match="seed_id"):
        apply_seed_choice(
            state,
            seed,
            tampered,
            "cultivate",
            expected_version=1,
        )


def test_unknown_choice_is_rejected() -> None:
    state = GameState()
    seed = _make_seed()
    rendered = render_fallback_event(seed)

    with pytest.raises(InvalidSeedTurnError, match="unknown choice"):
        apply_seed_choice(
            state,
            seed,
            rendered,
            "missing",
            expected_version=1,
        )


def test_unsupported_effect_is_rejected() -> None:
    state = GameState()
    seed = _make_seed(
        effects=(
            StandardEffect(
                effect_type="grant_invincibility",
                target_id="player",
                amount=1,
            ),
        )
    )
    rendered = render_fallback_event(seed)

    with pytest.raises(UnsupportedStandardEffectError):
        apply_seed_choice(
            state,
            seed,
            rendered,
            "cultivate",
            expected_version=1,
        )


def test_effect_without_amount_is_rejected() -> None:
    state = GameState()
    seed = _make_seed(
        effects=(StandardEffect(effect_type="cultivation_delta"),),
    )
    rendered = render_fallback_event(seed)

    with pytest.raises(InvalidSeedTurnError, match="amount"):
        apply_seed_choice(
            state,
            seed,
            rendered,
            "cultivate",
            expected_version=1,
        )
