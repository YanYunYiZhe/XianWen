"""插件加载失败。"""


class PluginLoadError(Exception):
    """一个插件未通过校验。宿主应捕获它并继续运行基础事件。"""

    def __init__(self, plugin_id: str, reason: str) -> None:
        self.plugin_id = plugin_id
        self.reason = reason
        super().__init__(f"{plugin_id}: {reason}")
