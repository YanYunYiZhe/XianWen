"""事件簿条目数据结构。"""

from dataclasses import dataclass

from xianwen.core.world_state import StandardEffect


@dataclass(frozen=True, slots=True)
class ChronicleEntry:
    """一次选择结算后的结构化事件簿记录。"""

    id: str  # 事件簿记录 ID
    turn: int  # 发生回合
    year: int  # 发生年份
    event_id: str  # 实际执行的事件 ID
    choice_id: str  # 玩家选择的选项 ID
    location_id: str | None  # 发生地点，可为空
    involved_character_ids: tuple[str, ...]  # 涉及的人物 ID
    summary: str  # 一到两句摘要
    applied_effects: tuple[StandardEffect, ...]  # 实际应用的效果
    summary_source: str  # 摘要来源："ai" 或 "fallback"
    tags: tuple[str, ...] = ()  # 检索和伏笔匹配标签
