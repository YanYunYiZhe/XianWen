"""AI 叙事草稿校验与无 AI 后备渲染测试。"""

from dataclasses import fields

import pytest

from xianwen.core import (
    InvalidNarrativeDraftError,
    NarrativeBrief,
    NarrativeChoice,
    NarrativeDraft,
    SeedChoice,
    SeedEvent,
    StandardEffect,
    render_fallback_event,
    validate_narrative_draft,
)


def _make_seed() -> SeedEvent:
    """构造一个带完整后备文本的测试种子。"""
    return SeedEvent(
        id="base.test_event",
        category="daily",
        fallback_scene_text="你站在山门前。",
        ai_prompt="扩写山门场景。",
        narrative_brief=NarrativeBrief(
            premise="玩家需要决定是否进入山门。",
            tone="平静",
            required_beats=("描写山门", "让玩家选择"),
            allowed_improvisation=("松风",),
            forbidden_content=("不能增加新选项",),
        ),
        choices=(
            SeedChoice(
                id="enter",
                fallback_label="进入山门",
                result_hint="你走进山门。",
                fallback_result_text="你踏入了山门。",
                effects=(StandardEffect(effect_type="cultivation_delta", amount=1),),
            ),
            SeedChoice(
                id="leave",
                fallback_label="离开山门",
                result_hint="你转身离开。",
                fallback_result_text="你没有进入山门。",
            ),
        ),
    )


def _make_draft() -> NarrativeDraft:
    """构造一个与测试种子完全匹配的 AI 叙事草稿。"""
    return NarrativeDraft(
        seed_id="base.test_event",
        scene_text="松风拂过山门，你停在石阶前。",
        choices=(
            NarrativeChoice(
                choice_id="enter",
                display_text="踏上石阶",
                result_text="你走入山门，灵气扑面而来。",
            ),
            NarrativeChoice(
                choice_id="leave",
                display_text="转身离去",
                result_text="你沿山路离开，没有回头。",
            ),
        ),
    )


def test_fallback_rendering_uses_seed_texts() -> None:
    rendered = render_fallback_event(_make_seed())

    assert rendered.seed_id == "base.test_event"
    assert rendered.scene_text == "你站在山门前。"
    assert rendered.choices[0].display_text == "进入山门"
    assert rendered.choices[0].result_text == "你踏入了山门。"


def test_valid_narrative_draft_renders_successfully() -> None:
    rendered = validate_narrative_draft(_make_draft(), (_make_seed(),))

    assert rendered.scene_text == "松风拂过山门，你停在石阶前。"
    assert rendered.choices[0].choice_id == "enter"
    assert rendered.choices[1].choice_id == "leave"


def test_unknown_seed_id_is_rejected() -> None:
    draft = NarrativeDraft(
        seed_id="base.unknown",
        scene_text="测试场景",
        choices=_make_draft().choices,
    )

    with pytest.raises(InvalidNarrativeDraftError, match="seed_id"):
        validate_narrative_draft(draft, (_make_seed(),))


def test_choice_order_must_match_seed() -> None:
    draft = _make_draft()
    reversed_draft = NarrativeDraft(
        seed_id=draft.seed_id,
        scene_text=draft.scene_text,
        choices=tuple(reversed(draft.choices)),
    )

    with pytest.raises(InvalidNarrativeDraftError, match="in order"):
        validate_narrative_draft(reversed_draft, (_make_seed(),))


def test_empty_scene_text_is_rejected() -> None:
    draft = NarrativeDraft(
        seed_id="base.test_event",
        scene_text="   ",
        choices=_make_draft().choices,
    )

    with pytest.raises(InvalidNarrativeDraftError, match="scene_text"):
        validate_narrative_draft(draft, (_make_seed(),))


def test_narrative_choice_has_no_effect_field() -> None:
    field_names = {item.name for item in fields(NarrativeChoice)}

    assert field_names == {"choice_id", "display_text", "result_text"}
