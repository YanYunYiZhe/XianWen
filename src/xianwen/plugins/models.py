"""加载成功后的插件快照。"""

from dataclasses import dataclass

from xianwen.core.models import Event
from xianwen.plugins.errors import PluginLoadError


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """一份已通过校验的纯数据插件。"""

    id: str
    name: str
    version: str
    api_version: str
    events: tuple[Event, ...]


@dataclass(frozen=True, slots=True)
class PluginRegistry:
    """一次目录扫描的结果。失败插件不会进入 plugins。"""

    plugins: tuple[LoadedPlugin, ...] = ()
    errors: tuple[PluginLoadError, ...] = ()

    @property
    def events(self) -> tuple[Event, ...]:
        """已注册的插件事件，不包含基础事件。"""
        return tuple(event for plugin in self.plugins for event in plugin.events)
