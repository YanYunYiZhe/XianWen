"""种子事件和固定选项的契约测试。"""

import pytest

from xianwen.core import (
    NarrativeBrief,
    SeedChoice,
    SeedEvent,
    StandardEffect,
)


def _make_choice(choice_id: str = "cultivate") -> SeedChoice:
    """构造一个用于测试的合法固定选项。"""
    return SeedChoice(
        id=choice_id,
        fallback_label="修炼",
        result_hint="你开始运转功法，灵气逐渐汇聚。",
        fallback_result_text="你完成了一次修炼，修为有所增长。",
        effects=(StandardEffect(effect_type="cultivation_delta", amount=1),),
    )


def _make_seed(*choices: SeedChoice) -> SeedEvent:
    """构造一个用于测试的合法种子事件。"""
    return SeedEvent(
        id="base.morning_training",
        category="daily",
        fallback_scene_text="清晨灵气尚可，你准备如何度过今日？",
        ai_prompt="扩写清晨修炼场景，但不能改变选项和效果。",
        narrative_brief=NarrativeBrief(
            premise="玩家在清晨决定如何修行。",
            tone="平静、克制",
            required_beats=("交代清晨环境", "让玩家作出选择"),
            allowed_improvisation=("鸟鸣", "山雾"),
            forbidden_content=("不能新增选项", "不能修改修为效果"),
        ),
        choices=choices,
        weight=1,
    )


def test_seed_event_accepts_two_to_four_choices() -> None:
    seed = _make_seed(_make_choice("cultivate"), _make_choice("rest"))

    assert seed.id == "base.morning_training"
    assert len(seed.choices) == 2


def test_seed_event_rejects_fewer_than_two_choices() -> None:
    with pytest.raises(ValueError, match="2 to 4"):
        _make_seed(_make_choice())


def test_seed_event_rejects_duplicate_choice_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        _make_seed(_make_choice("cultivate"), _make_choice("cultivate"))


def test_seed_event_rejects_negative_weight() -> None:
    with pytest.raises(ValueError, match="weight"):
        SeedEvent(
            id="base.invalid_weight",
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
            choices=(_make_choice("a"), _make_choice("b")),
            weight=-1,
        )


def test_seed_choice_rejects_empty_fallback_text() -> None:
    with pytest.raises(ValueError, match="fallback_result_text"):
        SeedChoice(
            id="empty",
            fallback_label="空结果",
            result_hint="测试",
            fallback_result_text="   ",
        )
