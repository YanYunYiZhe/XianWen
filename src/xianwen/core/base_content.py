"""
游戏核心的内置默认内容
内置内容数据，不放逻辑(场景文字、选项文字、结果文字、效果)
"""

from xianwen.core.models import Choice, ChoiceEffect, Event

# 命名规则：
# 事件 ID：  base.morning_training
#            └──┬──┘ └──────┬──────┘
#             命名空间      事件名

MORNING_TRAINING = Event(
    id="base.morning_training",  # 内置基础内容；插件内容必须使用自己的命名空间
    scene_text="清晨灵气尚可，你准备如何度过今日？",
    choices=(
        Choice(
            id="cultivate",
            label="修炼",
            result_text="你凝神静气，运转功法，修为增长了一分。",
            effect=ChoiceEffect(cultivation_delta=1),
        ),
        Choice(
            id="rest",
            label="休息",
            result_text="你暂且休息，养足精神，准备明日再行修炼。",
            effect=ChoiceEffect(cultivation_delta=0),
        ),
    ),
)
