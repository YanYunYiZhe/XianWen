"""当前局完整不可变快照。"""

from dataclasses import dataclass, field

from xianwen.core.chronicle import ChronicleEntry
from xianwen.core.foreshadow import ForeshadowBook
from xianwen.core.player_state import PlayerState
from xianwen.core.world_state import WorldSnapshot


@dataclass(frozen=True, slots=True)
class GameState:
    """新 PRD 定义的完整局状态。"""

    player: PlayerState = field(default_factory=PlayerState)
    world: WorldSnapshot = field(default_factory=WorldSnapshot)

    # 已发生事件的结构化历史
    chronicle: tuple[ChronicleEntry, ...] = ()

    # 玩家不可见的伏笔账本
    foreshadows: ForeshadowBook = field(default_factory=ForeshadowBook)
