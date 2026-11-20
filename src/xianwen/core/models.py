"""核心数据模型"""

from dataclasses import dataclass


# 游戏状态
@dataclass(frozen=True, slots=True)
class LegacyGameState:
    year: int = 1
    cultivation: int = 0  # 修为值
    ended: bool = False  # 是否结束


# 选择效果（给插件平台看的‘标准效果展示’）
@dataclass(frozen=True, slots=True)
class ChoiceEffect:
    """
    表示玩家做出某个选择后，对游戏状态产生的影响。

    这是一种插件安全机制。外部插件不能直接修改冻结的 LegacyGameState，
    只能提交 ChoiceEffect，由核心引擎统一处理状态变更。
    """

    cultivation_delta: int = 0


# 选项
@dataclass(frozen=True, slots=True)
class Choice:
    """事件中的一个选项（按钮）"""

    id: str
    label: str  # 显示给玩家的文字
    result_text: str  # 选项结果的文字
    effect: ChoiceEffect  # 选项效果


# 事件
@dataclass(frozen=True, slots=True)
class Event:
    """一个完整的回合事件"""

    id: str
    scene_text: str  # 场景描述文字
    choices: tuple[
        Choice, ...
    ]  # 一个元组，包含所有选项（元组是不可变的，一个事件定义好后，只能包含固定的选项）


# 回合结果
@dataclass(frozen=True, slots=True)
class TurnResult:
    """记录一次有效选择执行后的结果快照"""

    state: LegacyGameState  # 第一阶段兼容游戏状态
    event_id: str  # 事件ID
    choice_id: str  # 选项ID
    result_text: str  # 需要展示给玩家的结果文字
