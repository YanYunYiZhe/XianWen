"""核心数据模型"""

from dataclasses import dataclass


# 游戏状态
@dataclass(frozen=True, slots=True)
class LegacyGameState:
    year: int = 1
    cultivation: int = 0  # 修为值
    ended: bool = False  # 是否结束


# 第一阶段兼容效果，仅用于 LegacyGameState 固定回合
@dataclass(frozen=True, slots=True)
class ChoiceEffect:
    """
    旧 LegacyGameState 回合使用的简化效果。

    该类型只服务第一阶段兼容接口，不是新架构的标准效果契约。
    新插件、新种子事件和新回合必须使用 StandardEffect，
    由核心校验、应用并记录到状态迁移中。
    """

    cultivation_delta: int = 0


# 选项
@dataclass(frozen=True, slots=True)
class Choice:
    """事件中的一个选项（按钮）"""

    id: str
    label: str  # 显示给玩家的文字
    result_text: str  # 选项结果的文字
    effect: ChoiceEffect  # 第一阶段兼容效果；新架构使用 StandardEffect


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
