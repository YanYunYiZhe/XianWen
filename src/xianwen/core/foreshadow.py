"""伏笔账本数据结构。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ForeshadowAssessment:
    """第二个评审 agent 对伏笔候选的结构化评分。"""

    world_consistency: int  # 0-100，世界观一致性
    causal_clarity: int  # 0-100，因果清晰度
    payoff_feasibility: int  # 0-100，未来回收可行性
    narrative_value: int  # 0-100，叙事价值
    spoiler_risk: int  # 0-100，提前泄露风险
    total_score: int  # 0-100，综合评分
    recommendation: str  # accept / revise / reject
    reason: str  # 评分理由


@dataclass(frozen=True, slots=True)
class ForeshadowRecord:
    """认证后的隐藏伏笔事实。"""

    id: str  # 伏笔记录 ID
    source_event_id: str  # 来源事件 ID
    source_turn: int  # 提出伏笔的回合
    content: str  # 隐藏事实
    payoff_tags: tuple[str, ...]  # 未来回收事件匹配标签
    due_turn: int  # 最晚响应回合
    status: str  # certified / due / resolved / expired
    assessment: ForeshadowAssessment  # 认证评分记录


@dataclass(frozen=True, slots=True)
class ForeshadowBook:
    """当前局所有伏笔记录的隐藏账本。"""

    records: tuple[ForeshadowRecord, ...] = ()
    max_active: int = 0  # 活跃伏笔上限；0 表示尚未配置
