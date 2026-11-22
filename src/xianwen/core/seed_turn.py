"""新种子回合的最小原子结算入口。

该模块只接受可信 SeedEvent 和已校验 RenderedEvent。
AI 文本只用于展示，不能决定效果。
"""

from dataclasses import dataclass, replace

from xianwen.core.chronicle import ChronicleEntry
from xianwen.core.game_state import GameState
from xianwen.core.narrative import RenderedChoice, RenderedEvent
from xianwen.core.player_state import PlayerState
from xianwen.core.seed import SeedChoice, SeedEvent
from xianwen.core.world_state import StandardEffect, advance_world


class InvalidSeedTurnError(ValueError):
    """请求的事件、选项或效果不符合可信种子契约。"""


class UnsupportedStandardEffectError(ValueError):
    """当前最小回合尚不支持该 StandardEffect 类型。"""


@dataclass(frozen=True, slots=True)
class SeedTurnResult:
    """新种子回合完成后的完整结果。

    该类型暂时与旧 TurnResult 并存。旧 TurnResult 继续服务
    LegacyGameState；新种子回合使用 GameState。
    """

    state: GameState  # 完成结算后的完整新状态
    event_id: str  # 实际执行的可信种子 ID
    choice_id: str  # 玩家实际选择的固定选项 ID
    result_text: str  # 展示给玩家的已校验结果文字


def apply_seed_choice(
    state: GameState,
    seed: SeedEvent,
    rendered_event: RenderedEvent,
    choice_id: str,
    *,
    expected_version: int,
) -> SeedTurnResult:
    """结算一次新种子回合。

    原子性来自不可变状态：
    - 先校验展示事件和选项；
    - 再从可信 SeedEvent 读取效果；
    - 计算完整的新 PlayerState 和 WorldSnapshot；
    - 只有全部成功后，才组成并返回新 GameState。

    任一校验失败或版本冲突都会抛异常，不会返回半个状态。
    """
    _validate_rendered_event(seed, rendered_event)

    seed_choice = _resolve_seed_choice(seed, choice_id)
    rendered_choice = _resolve_rendered_choice(rendered_event, choice_id)

    new_player = _apply_player_effects(state.player, seed_choice.effects)

    new_world = advance_world(
        state.world,
        expected_version=expected_version,
        applied_effects=seed_choice.effects,
        source="core",
    )

    chronicle_entry = ChronicleEntry(
        id=_chronicle_id(state.world.core.turn, seed.id, seed_choice.id),
        turn=state.world.core.turn,
        year=state.world.core.year,
        event_id=seed.id,
        choice_id=seed_choice.id,
        location_id=new_player.location_id,
        involved_character_ids=(),
        summary=rendered_choice.result_text,
        applied_effects=seed_choice.effects,
        summary_source="fallback",
        tags=(seed.category,),
    )

    new_state = GameState(
        player=new_player,
        world=new_world,
        chronicle=(*state.chronicle, chronicle_entry),
        foreshadows=state.foreshadows,
    )

    return SeedTurnResult(
        state=new_state,
        event_id=seed.id,
        choice_id=seed_choice.id,
        result_text=rendered_choice.result_text,
    )


def _validate_rendered_event(
    seed: SeedEvent,
    rendered_event: RenderedEvent,
) -> None:
    """确认展示事件确实来自指定种子，不能被客户端篡改。

    RenderedEvent 可以来自后备渲染，也可以来自通过校验的 AI 草稿。
    但进入状态结算前必须再次核对 seed_id、选项数量和选项顺序。
    """
    if rendered_event.seed_id != seed.id:
        raise InvalidSeedTurnError(
            f"rendered event seed_id does not match seed: {rendered_event.seed_id!r}"
        )

    if not rendered_event.scene_text.strip():
        raise InvalidSeedTurnError("rendered event scene_text must not be empty")

    if len(rendered_event.choices) != len(seed.choices):
        raise InvalidSeedTurnError(
            "rendered event choice count must match the seed event"
        )

    for expected, actual in zip(seed.choices, rendered_event.choices, strict=True):
        if actual.choice_id != expected.id:
            raise InvalidSeedTurnError(
                "rendered event choice ids must match seed choices in order"
            )
        if not actual.display_text.strip():
            raise InvalidSeedTurnError("rendered choice display_text must not be empty")
        if not actual.result_text.strip():
            raise InvalidSeedTurnError("rendered choice result_text must not be empty")


def _resolve_seed_choice(seed: SeedEvent, choice_id: str) -> SeedChoice:
    """只从可信种子中查找规则选项。"""
    for choice in seed.choices:
        if choice.id == choice_id:
            return choice
    raise InvalidSeedTurnError(f"unknown choice id {choice_id!r} for seed {seed.id!r}")


def _resolve_rendered_choice(
    rendered_event: RenderedEvent,
    choice_id: str,
) -> RenderedChoice:
    """从已校验展示事件中查找对应文字。"""
    for choice in rendered_event.choices:
        if choice.choice_id == choice_id:
            return choice
    raise InvalidSeedTurnError(f"unknown choice id {choice_id!r} for rendered event")


def _apply_player_effects(
    player: PlayerState,
    effects: tuple[StandardEffect, ...],
) -> PlayerState:
    """把当前支持的标准效果应用到玩家状态。

    第一版只支持 cultivation_delta，未知效果必须失败关闭。
    所有效果先计算，再通过 replace 生成一个不可变的新 PlayerState。
    """
    cultivation = player.cultivation

    for effect in effects:
        if effect.effect_type != "cultivation_delta":
            raise UnsupportedStandardEffectError(
                f"unsupported standard effect: {effect.effect_type!r}"
            )

        if effect.target_id not in {None, "player"}:
            raise InvalidSeedTurnError(
                "cultivation_delta target must be player or None"
            )

        if effect.amount is None:
            raise InvalidSeedTurnError("cultivation_delta requires an integer amount")

        cultivation += effect.amount

    if cultivation < 0:
        raise InvalidSeedTurnError("player cultivation cannot be negative")

    return replace(player, cultivation=cultivation)


def _chronicle_id(turn: int, event_id: str, choice_id: str) -> str:
    """生成当前最小实现使用的可追踪事件簿 ID。"""
    return f"chronicle.{turn}.{event_id}.{choice_id}"
