"""把 plugin.toml 和 events.toml 校验并转换成核心 Event。"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from xianwen.core.base_content import MORNING_TRAINING
from xianwen.core.models import Choice, ChoiceEffect, Event
from xianwen.plugins.errors import PluginLoadError
from xianwen.plugins.models import LoadedPlugin

_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9-]*$")
_EVENT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_CHOICE_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_PLUGIN_FIELDS = frozenset({"id", "name", "version", "api_version"})
_EVENT_FIELDS = frozenset({"id", "fallback_scene_text", "choices"})
_CHOICE_FIELDS = frozenset({"id", "fallback_label", "fallback_result_text", "effect"})
_EFFECT_FIELDS = frozenset({"cultivation_delta"})
_RESERVED_EVENT_ID = MORNING_TRAINING.id


def load_plugin(
    directory: Path,
    *,
    reserved_event_ids: frozenset[str] = frozenset({_RESERVED_EVENT_ID}),
) -> LoadedPlugin:
    """校验一个插件目录并返回核心事件。失败时抛出 PluginLoadError。"""
    folder_name = directory.name
    if not directory.is_dir():
        raise PluginLoadError(folder_name, "plugin path is not a directory")

    manifest_path = directory / "plugin.toml"
    events_path = directory / "content" / "events.toml"
    manifest = _read_toml(manifest_path, folder_name)
    plugin_id = _manifest_id(manifest, folder_name)
    _validate_manifest(manifest, directory, plugin_id)
    document = _read_toml(events_path, plugin_id)
    events = _validate_events(document, plugin_id, reserved_event_ids)
    plugin = manifest["plugin"]
    return LoadedPlugin(
        id=plugin_id,
        name=_required_text(plugin["name"], "plugin.name", plugin_id),
        version=_required_text(plugin["version"], "plugin.version", plugin_id),
        api_version="1",
        events=events,
    )


def _read_toml(path: Path, plugin_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise PluginLoadError(plugin_id, f"missing {path.name}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except UnicodeError as exc:
        raise PluginLoadError(plugin_id, f"{path.name} must be UTF-8") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PluginLoadError(plugin_id, f"invalid TOML in {path.name}") from exc
    return data


def _manifest_id(manifest: dict[str, Any], folder_name: str) -> str:
    plugin = manifest.get("plugin")
    if not isinstance(plugin, dict):
        return folder_name
    plugin_id = plugin.get("id")
    if isinstance(plugin_id, str) and plugin_id.strip():
        return plugin_id
    return folder_name


def _validate_manifest(
    manifest: dict[str, Any],
    directory: Path,
    plugin_id: str,
) -> None:
    _reject_unknown(set(manifest), {"plugin"}, "plugin.toml", plugin_id)
    plugin = manifest.get("plugin")
    if not isinstance(plugin, dict):
        raise PluginLoadError(plugin_id, "plugin.toml must contain [plugin]")
    _reject_unknown(set(plugin), _PLUGIN_FIELDS, "[plugin]", plugin_id)
    for field_name in ("id", "name", "version", "api_version"):
        if field_name not in plugin:
            raise PluginLoadError(plugin_id, f"missing plugin.{field_name}")
    declared_id = plugin["id"]
    if (
        not isinstance(declared_id, str)
        or not _PLUGIN_ID.fullmatch(declared_id)
        or declared_id == "base"
    ):
        raise PluginLoadError(plugin_id, "plugin.id is not a valid namespace")
    if directory.name != declared_id:
        raise PluginLoadError(plugin_id, "directory name must equal plugin.id")
    _required_text(plugin["name"], "plugin.name", plugin_id)
    _required_text(plugin["version"], "plugin.version", plugin_id)
    api_version = plugin["api_version"]
    if api_version != "1" or not isinstance(api_version, str):
        raise PluginLoadError(plugin_id, 'plugin.api_version must be "1"')


def _validate_events(
    document: dict[str, Any],
    plugin_id: str,
    reserved_event_ids: frozenset[str],
) -> tuple[Event, ...]:
    _reject_unknown(set(document), {"events"}, "events.toml", plugin_id)
    raw_events = document.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise PluginLoadError(plugin_id, "events.toml must contain at least one event")

    events: list[Event] = []
    seen_event_ids = set(reserved_event_ids)
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            raise PluginLoadError(plugin_id, "event must be a table")
        event = _validate_event(raw_event, plugin_id)
        if event.id in seen_event_ids:
            raise PluginLoadError(plugin_id, f"duplicate event id {event.id}")
        seen_event_ids.add(event.id)
        events.append(event)
    return tuple(events)


def _validate_event(raw_event: dict[str, Any], plugin_id: str) -> Event:
    _reject_unknown(set(raw_event), _EVENT_FIELDS, "event", plugin_id)
    for field_name in _EVENT_FIELDS:
        if field_name not in raw_event:
            raise PluginLoadError(plugin_id, f"missing event.{field_name}")
    event_id = _exact_identifier(raw_event["id"], "event.id", plugin_id)
    prefix, separator, event_name = event_id.partition(".")
    if (
        separator != "."
        or "." in event_name
        or prefix != plugin_id
        or not _EVENT_NAME.fullmatch(event_name)
    ):
        raise PluginLoadError(
            plugin_id,
            f"event id {event_id} is outside namespace {plugin_id}",
        )
    scene_text = _required_text(
        raw_event["fallback_scene_text"],
        "event.fallback_scene_text",
        plugin_id,
    )
    raw_choices = raw_event["choices"]
    if not isinstance(raw_choices, list) or not 2 <= len(raw_choices) <= 4:
        raise PluginLoadError(plugin_id, "event must contain 2 to 4 choices")

    choices: list[Choice] = []
    seen_choice_ids: set[str] = set()
    for raw_choice in raw_choices:
        if not isinstance(raw_choice, dict):
            raise PluginLoadError(plugin_id, "choice must be a table")
        choice = _validate_choice(raw_choice, plugin_id)
        if choice.id in seen_choice_ids:
            raise PluginLoadError(plugin_id, f"duplicate choice id {choice.id}")
        seen_choice_ids.add(choice.id)
        choices.append(choice)
    return Event(id=event_id, scene_text=scene_text, choices=tuple(choices))


def _validate_choice(raw_choice: dict[str, Any], plugin_id: str) -> Choice:
    _reject_unknown(set(raw_choice), _CHOICE_FIELDS, "choice", plugin_id)
    for field_name in _CHOICE_FIELDS:
        if field_name not in raw_choice:
            raise PluginLoadError(plugin_id, f"missing choice.{field_name}")
    choice_id = _exact_identifier(raw_choice["id"], "choice.id", plugin_id)
    if not _CHOICE_ID.fullmatch(choice_id):
        raise PluginLoadError(plugin_id, f"choice id {choice_id} is invalid")
    effect = raw_choice["effect"]
    if not isinstance(effect, dict):
        raise PluginLoadError(plugin_id, "choice.effect must be a table")
    _reject_unknown(set(effect), _EFFECT_FIELDS, "effect", plugin_id)
    if "cultivation_delta" not in effect:
        raise PluginLoadError(plugin_id, "missing effect.cultivation_delta")
    delta = effect["cultivation_delta"]
    if isinstance(delta, bool) or not isinstance(delta, int):
        raise PluginLoadError(plugin_id, "effect.cultivation_delta must be an integer")
    return Choice(
        id=choice_id,
        label=_required_text(
            raw_choice["fallback_label"],
            "choice.fallback_label",
            plugin_id,
        ),
        result_text=_required_text(
            raw_choice["fallback_result_text"],
            "choice.fallback_result_text",
            plugin_id,
        ),
        effect=ChoiceEffect(cultivation_delta=delta),
    )


def _exact_identifier(value: object, field_name: str, plugin_id: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise PluginLoadError(plugin_id, f"{field_name} must be a non-empty string")
    return value


def _required_text(value: object, field_name: str, plugin_id: str) -> str:
    if not isinstance(value, str):
        raise PluginLoadError(plugin_id, f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise PluginLoadError(plugin_id, f"{field_name} must not be empty")
    return text


def _reject_unknown(
    actual: set[str],
    allowed: set[str] | frozenset[str],
    location: str,
    plugin_id: str,
) -> None:
    unknown = actual - set(allowed)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise PluginLoadError(plugin_id, f"unknown {location} field: {names}")
