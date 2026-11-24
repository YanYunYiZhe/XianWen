"""扫描插件目录。一个插件失败不会阻止其他插件和基础事件。"""

from pathlib import Path

from xianwen.core.base_content import MORNING_TRAINING
from xianwen.plugins.errors import PluginLoadError
from xianwen.plugins.loader import load_plugin
from xianwen.plugins.models import LoadedPlugin, PluginRegistry


def load_plugins(root: Path) -> PluginRegistry:
    """按目录名顺序加载 root 下的插件。不修改基础事件。"""
    if not root.is_dir():
        raise PluginLoadError("", "plugin root is not a directory")

    plugins: list[LoadedPlugin] = []
    errors: list[PluginLoadError] = []
    seen_plugin_ids: set[str] = set()
    seen_event_ids: set[str] = {MORNING_TRAINING.id}
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        try:
            loaded = load_plugin(
                directory,
                reserved_event_ids=frozenset(seen_event_ids),
            )
        except PluginLoadError as exc:
            errors.append(exc)
            continue
        if loaded.id in seen_plugin_ids:
            errors.append(PluginLoadError(loaded.id, "plugin id is already registered"))
            continue
        seen_plugin_ids.add(loaded.id)
        seen_event_ids.update(event.id for event in loaded.events)
        plugins.append(loaded)
    return PluginRegistry(plugins=tuple(plugins), errors=tuple(errors))
