"""核心规则引擎，完整的回合流程

    年份推进由核心统一做（year + 1），插件以后不能自己改年份。
    非法事件 → InvalidEventError；非法选项 → InvalidChoiceError。
    不读取、不修改任何全局可变状态。
"""

from xianwen.core.base_content import MORNING_TRAINING
from xianwen.core.models import Choice, Event, GameState, TurnResult


class InvalidEventError(ValueError):
    """当请求的事件 ID 不可用时抛出"""


class InvalidChoiceError(ValueError):
    """当请求的选项 ID 不属于该事件时抛出"""


def new_game() -> GameState:
    """创建一个全新的游戏状态，用于第一回合"""
    return GameState()


def get_current_event(state: GameState) -> Event:
    """根据给定的游戏状态，返回当前可用的事件

    第一阶段的事件选择故意做得很简单：只有一个固定事件
    `state` 参数是公共契约的一部分，将来会用于真正的事件选择逻辑
    """
    return MORNING_TRAINING


def apply_choice(state: GameState, event_id: str, choice_id: str) -> TurnResult:
    """
    校验选择，并返回应用选择后的新状态与结果文字

    该函数是纯函数：它从不修改传入的 state，也不读取进程级的可变全局数据
    """
    event = _resolve_event(event_id)
    choice = _resolve_choice(event, choice_id)

    # new 一个GameState
    new_state = GameState(
        year=state.year + 1,
        cultivation=state.cultivation + choice.effect.cultivation_delta,
        ended=state.ended,
    )

    return TurnResult(
        state=new_state,
        event_id=event.id,
        choice_id=choice.id,
        result_text=choice.result_text,
    )


def _resolve_event(event_id: str) -> Event:
    """根据事件 ID 找到事件；找不到抛 InvalidEventError"""
    if event_id != MORNING_TRAINING.id:
        raise InvalidEventError(f"Unknown event id: {event_id!r}")
    return MORNING_TRAINING


def _resolve_choice(event: Event, choice_id: str) -> Choice:
    """在事件里找选项；找不到抛 InvalidChoiceError"""
    for choice in event.choices:
        if choice.id == choice_id:
            return choice
    raise InvalidChoiceError(
        f"Unknown choice id {choice_id!r} for event {event.id!r}"
    )