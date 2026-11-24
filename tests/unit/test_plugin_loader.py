"""第一周纯数据插件加载器测试。"""

from pathlib import Path

import pytest

from xianwen.core.engine import apply_choice, get_current_event, new_game
from xianwen.plugins import PluginLoadError, load_plugin, load_plugins

_MANIFEST = """\
[plugin]
id = "official-example"
name = "官方示例插件"
version = "0.1.0"
api_version = "1"
"""

_EVENTS = """\
# 注释和空行必须被允许

[[events]]
id = "official-example.meet_traveler"
fallback_scene_text = "青石镇外，一位旅人正在歇脚。"

[[events.choices]]
id = "talk"
fallback_label = "上前攀谈"
fallback_result_text = "你与旅人论道，修为有所增长。"
effect = { cultivation_delta = 1 }

[[events.choices]]
id = "leave"
fallback_label = "绕开离开"
fallback_result_text = "你继续赶路，修为没有变化。"
effect = { cultivation_delta = 0 }
"""


def _write_plugin(
    root: Path,
    plugin_id: str = "official-example",
    *,
    manifest: str | None = None,
    events: str | None = None,
) -> Path:
    directory = root / plugin_id
    content = directory / "content"
    content.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        manifest if manifest is not None else _MANIFEST,
        encoding="utf-8",
    )
    (content / "events.toml").write_text(
        events if events is not None else _EVENTS,
        encoding="utf-8",
    )
    return directory


def test_legal_plugin_registers_event(tmp_path: Path) -> None:
    loaded = load_plugin(_write_plugin(tmp_path))

    assert loaded.id == "official-example"
    assert loaded.events[0].id == "official-example.meet_traveler"
    assert loaded.events[0].scene_text == "青石镇外，一位旅人正在歇脚。"
    assert loaded.events[0].choices[0].effect.cultivation_delta == 1


def test_multiple_events_are_all_registered(tmp_path: Path) -> None:
    events = (
        _EVENTS
        + """\

[[events]]
id = "official-example.night_meditation"
fallback_scene_text = "入夜后你在院中盘坐。"

[[events.choices]]
id = "meditate"
fallback_label = "继续打坐"
fallback_result_text = "修为又进了一分。"
effect = { cultivation_delta = 1 }

[[events.choices]]
id = "sleep"
fallback_label = "收功就寝"
fallback_result_text = "今夜修为没有增加。"
effect = { cultivation_delta = 0 }
"""
    )
    loaded = load_plugin(_write_plugin(tmp_path, events=events))

    assert [event.id for event in loaded.events] == [
        "official-example.meet_traveler",
        "official-example.night_meditation",
    ]


def test_negative_cultivation_delta_is_accepted(tmp_path: Path) -> None:
    events = _EVENTS.replace("cultivation_delta = 0", "cultivation_delta = -1", 1)
    loaded = load_plugin(_write_plugin(tmp_path, events=events))

    assert loaded.events[0].choices[1].effect.cultivation_delta == -1


def test_missing_scene_text_raises_plugin_load_error(tmp_path: Path) -> None:
    events = _EVENTS.replace(
        'fallback_scene_text = "青石镇外，一位旅人正在歇脚。"\n',
        "",
    )

    with pytest.raises(PluginLoadError) as caught:
        load_plugin(_write_plugin(tmp_path, events=events))

    assert caught.value.plugin_id == "official-example"
    assert "fallback_scene_text" in caught.value.reason
    assert caught.value.plugin_id in str(caught.value)
    assert caught.value.reason in str(caught.value)


def test_missing_result_text_raises_plugin_load_error(tmp_path: Path) -> None:
    events = _EVENTS.replace(
        'fallback_result_text = "你与旅人论道，修为有所增长。"\n',
        "",
    )

    with pytest.raises(PluginLoadError) as caught:
        load_plugin(_write_plugin(tmp_path, events=events))

    assert "fallback_result_text" in caught.value.reason


def test_padded_plugin_id_is_rejected(tmp_path: Path) -> None:
    manifest = _MANIFEST.replace(
        'id = "official-example"',
        'id = " official-example"',
    )

    with pytest.raises(PluginLoadError) as caught:
        load_plugin(_write_plugin(tmp_path, manifest=manifest))

    assert "namespace" in caught.value.reason


def test_event_id_outside_namespace_is_rejected(tmp_path: Path) -> None:
    events = _EVENTS.replace(
        "official-example.meet_traveler",
        "other-plugin.meet_traveler",
    )

    with pytest.raises(PluginLoadError) as caught:
        load_plugin(_write_plugin(tmp_path, events=events))

    assert "outside namespace" in caught.value.reason


def test_failed_plugin_does_not_remove_base_event(tmp_path: Path) -> None:
    _write_plugin(tmp_path, events=_EVENTS.replace("fallback_scene_text", "scene"))
    _write_plugin(
        tmp_path,
        "road-notes",
        manifest=_MANIFEST.replace("official-example", "road-notes"),
        events=_EVENTS.replace("official-example", "road-notes"),
    )

    registry = load_plugins(tmp_path)
    state = new_game()
    event = get_current_event(state)
    result = apply_choice(state, event.id, "cultivate")

    assert [item.id for item in registry.plugins] == ["road-notes"]
    assert registry.errors[0].plugin_id == "official-example"
    assert event.id == "base.morning_training"
    assert result.state.year == 2
    assert result.state.cultivation == 1
