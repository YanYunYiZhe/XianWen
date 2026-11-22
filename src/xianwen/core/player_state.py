"""玩家自身状态与相关值记录。"""

from dataclasses import dataclass

from xianwen.core.world_state import ItemRecord


@dataclass(frozen=True, slots=True)
class ReputationValue:
    """玩家对某个势力的声望。"""

    faction_id: str  # 目标势力 ID，例如 base.sect
    value: int = 0  # 声望值，可正可负


@dataclass(frozen=True, slots=True)
class RelationshipValue:
    """玩家与某个关键人物的好感。"""

    character_id: str  # 目标人物 ID
    value: int = 0  # 好感值，可正可负


@dataclass(frozen=True, slots=True)
class PlayerFlag:
    """玩家层面的布尔标记，用于后续条件判断。"""

    key: str  # 标记键，例如 enlightened
    value: bool = True  # 标记值


@dataclass(frozen=True, slots=True)
class PlayerState:
    """玩家直接拥有的数值、关系、物品和叙事标签。

    PlayerState 只能由核心高层回合结算函数与世界快照一起原子更新。
    插件、AI 和 Web 不得单独构造并替换该对象。
    """

    identity: str = "云州散修"  # 出身与身份
    realm: str = "练气一层"  # 当前境界
    cultivation: int = 0  # 当前修为
    lifespan: int = 100  # 当前寿元
    injuries: int = 0  # 当前伤势
    mood: int = 50  # 当前心境
    luck: int = 0  # 气运值

    # 各势力声望；同一势力只允许一条记录
    reputation: tuple[ReputationValue, ...] = ()

    # 与关键人物的好感；同一人物只允许一条记录
    relationships: tuple[RelationshipValue, ...] = ()

    # 玩家持有物；同一物品不得同时在 DynamicWorldState.items 中重复归属
    items: tuple[ItemRecord, ...] = ()

    # 当前地点 ID；新游戏可为空，表示尚未进入具体地点
    location_id: str | None = None

    # 玩家标签和布尔标记
    flags: tuple[PlayerFlag, ...] = ()
