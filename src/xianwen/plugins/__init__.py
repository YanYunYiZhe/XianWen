"""第一周纯数据插件的加载入口。"""

from xianwen.plugins.errors import PluginLoadError
from xianwen.plugins.loader import load_plugin
from xianwen.plugins.models import LoadedPlugin, PluginRegistry
from xianwen.plugins.registry import load_plugins

__all__ = [
    "LoadedPlugin",
    "PluginLoadError",
    "PluginRegistry",
    "load_plugin",
    "load_plugins",
]
