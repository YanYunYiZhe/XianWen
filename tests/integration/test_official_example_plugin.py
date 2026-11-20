"""官方示例插件集成测试。

对应任务书 §6.4。B 的插件加载器与 docs/plugin-spec.md 合并前，
这些用例先 skip，不伪造运行成功结果；加载器落地后按公开 API 对齐并取消 skip。
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="等待 B 的插件加载器与插件契约合并后启用"
)


def test_plugin_event_registered_when_enabled() -> None:
    """§6.4-1: 启用插件后，注册表中出现插件事件。"""
    ...


def test_plugin_event_excluded_when_disabled() -> None:
    """§6.4-2: 禁用插件后，插件事件不参与候选，基础事件仍可用。"""
    ...


def test_plugin_event_completes_state_transition() -> None:
    """§6.4-3: 插件事件能通过核心完成一次状态迁移（talk → 修为 +1）。"""
    ...


def test_plugin_state_survives_save_reload() -> None:
    """§6.4-4: 保存并重新加载后，插件标识和必要状态仍存在。"""
    ...


def test_broken_plugin_does_not_crash_base_game() -> None:
    """§6.4-5: 模拟错误插件时，应用仍可继续使用基础事件。"""
    ...
