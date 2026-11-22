"""第一版存档结构与序列化。

存档只保存可序列化为 JSON 的数据；API Key 等秘密字段禁止进入存档。
"""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from xianwen.core.models import LegacyGameState

SAVE_SCHEMA_VERSION = 1


class SaveFormatError(ValueError):
    """当存档无法解析或字段不合法时抛出。"""


class SavedGame(BaseModel):
    """存档中的游戏状态快照。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    year: int = Field(ge=1)
    cultivation: int = Field(ge=0)
    ended: bool = False


class SaveDocument(BaseModel):
    """第一版存档信封。"""

    model_config = ConfigDict(extra="forbid")

    schema_version: int
    game: SavedGame
    plugin_state: dict[str, dict[str, Any]] = Field(default_factory=dict)
    plugin_versions: dict[str, str] = Field(default_factory=dict)
    usage: dict[str, int] = Field(default_factory=dict)


def build_save(state: LegacyGameState) -> SaveDocument:
    """把核心状态包装成可保存的存档信封。"""
    return SaveDocument(
        schema_version=SAVE_SCHEMA_VERSION,
        game=SavedGame(
            year=state.year,
            cultivation=state.cultivation,
            ended=state.ended,
        ),
    )


def restore_state(save: SaveDocument) -> LegacyGameState:
    """把存档信封还原为核心状态。"""
    return LegacyGameState(
        year=save.game.year,
        cultivation=save.game.cultivation,
        ended=save.game.ended,
    )


def dump_save(state: LegacyGameState) -> str:
    """序列化为 JSON 字符串，供页面隐藏字段或浏览器本地存储使用。"""
    return build_save(state).model_dump_json()


def load_save(text: str) -> LegacyGameState:
    """从 JSON 字符串恢复状态；非法存档抛出 SaveFormatError。"""
    try:
        payload: object = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SaveFormatError("存档不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise SaveFormatError("存档必须是 JSON 对象")
    try:
        save = SaveDocument.model_validate(payload)
    except ValidationError as exc:
        raise SaveFormatError("存档字段不合法") from exc
    if save.schema_version != SAVE_SCHEMA_VERSION:
        raise SaveFormatError(f"不支持的存档版本：{save.schema_version}")
    return restore_state(save)
