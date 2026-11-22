"""AI 叙事草稿、后备渲染和确定性校验。

该模块只处理展示文本，不应用效果，也不修改 GameState。
"""

from dataclasses import dataclass

from xianwen.core.seed import SeedEvent


class InvalidNarrativeDraftError(ValueError):
    """AI 叙事草稿与候选种子不一致。"""


def _require_text(value: str, field_name: str) -> None:
    """拒绝空文本，避免把空白内容展示给玩家。"""
    if not value.strip():
        raise InvalidNarrativeDraftError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class NarrativeChoice:
    """AI 草稿中的一个选项展示文本。

    该结构刻意不包含 effects 字段，防止 AI 通过叙事输出提交规则效果。
    """

    choice_id: str  # 必须与种子中的 SeedChoice.id 完全一致
    display_text: str  # AI 扩写后的选项显示文字
    result_text: str  # AI 扩写后的选择结果文字


@dataclass(frozen=True, slots=True)
class NarrativeDraft:
    """AI 返回的未校验叙事草稿。"""

    seed_id: str  # AI 从候选集中选择的 SeedEvent.id
    scene_text: str  # AI 扩写后的场景文字
    choices: tuple[NarrativeChoice, ...]  # 与种子选项一一对应的展示文本


@dataclass(frozen=True, slots=True)
class RenderedChoice:
    """通过校验、可以展示给玩家的选项。"""

    choice_id: str  # 对应可信种子中的选项 ID
    display_text: str  # 最终展示给玩家的选项文字
    result_text: str  # 选择后展示给玩家的结果文字


@dataclass(frozen=True, slots=True)
class RenderedEvent:
    """通过校验、可以展示给玩家的回合事件。

    规则效果仍保存在来源 SeedEvent 中，不进入 RenderedEvent。
    """

    seed_id: str  # 本事件使用的可信种子 ID
    scene_text: str  # 最终展示给玩家的场景文字
    choices: tuple[RenderedChoice, ...]  # 已校验的展示选项


def render_fallback_event(seed: SeedEvent) -> RenderedEvent:
    """使用种子的后备文本生成可展示事件。

    该函数不依赖 AI 或网络，是无 Key 模式下必须始终可用的路径。
    """
    return RenderedEvent(
        seed_id=seed.id,
        scene_text=seed.fallback_scene_text,
        choices=tuple(
            RenderedChoice(
                choice_id=choice.id,
                display_text=choice.fallback_label,
                result_text=choice.fallback_result_text,
            )
            for choice in seed.choices
        ),
    )


def validate_narrative_draft(
    draft: NarrativeDraft,
    candidates: tuple[SeedEvent, ...],
) -> RenderedEvent:
    """校验 AI 草稿，并转换为可展示事件。

    规则：
    - seed_id 必须唯一匹配一个候选种子。
    - 选项数量和顺序必须与种子完全一致。
    - choice_id 必须与种子完全一致。
    - 场景、显示文字和结果文字不能为空。
    - 草稿没有 effects 字段，无法提交规则效果。
    """
    matches = [candidate for candidate in candidates if candidate.id == draft.seed_id]
    if len(matches) != 1:
        raise InvalidNarrativeDraftError(
            f"seed_id must identify exactly one candidate: {draft.seed_id!r}"
        )

    seed = matches[0]
    _require_text(draft.scene_text, "narrative.scene_text")

    if len(draft.choices) != len(seed.choices):
        raise InvalidNarrativeDraftError(
            "narrative choice count must match the seed event"
        )

    rendered_choices: list[RenderedChoice] = []
    for expected, actual in zip(seed.choices, draft.choices, strict=True):
        if actual.choice_id != expected.id:
            raise InvalidNarrativeDraftError(
                "narrative choice ids must match seed choices in order"
            )

        _require_text(actual.display_text, "narrative.choice.display_text")
        _require_text(actual.result_text, "narrative.choice.result_text")
        rendered_choices.append(
            RenderedChoice(
                choice_id=expected.id,
                display_text=actual.display_text,
                result_text=actual.result_text,
            )
        )

    return RenderedEvent(
        seed_id=seed.id,
        scene_text=draft.scene_text,
        choices=tuple(rendered_choices),
    )
