# Progress

## 当前状态
- `develop` 已包含最小回合、Web 闭环和 PR #8 的测试夹具。
- 本分支 `feat/plugin-loader` 实现第一周纯数据插件加载器，按 `docs/plugin-spec.md` 校验并转成 `Event`。
- 失败插件抛出 `PluginLoadError`。读文件的 `OSError` 也会转成该异常，不中断其他插件。
- 坏插件不移除 `base.morning_training`。
- 本地 `ruff`、`mypy` 和 `pytest` 已通过。本分支 CI 结果以 GitHub Actions 为准。

## 下一步
- 请 A 复审读文件失败时的隔离修复。C 仍需复核插件契约 PR #5。
- 契约和加载器都进入 `develop` 后，C 再启用官方示例插件的测试。
- `get_current_event()` 仍只返回基础事件，插件事件还没有进入回合候选。

## 已知问题
- PR #5 也新增 `docs/plugin-spec.md`，和本分支合并时可能冲突。
- 插件事件还不能在页面中被选中。
- 负数 `cultivation_delta` 可以加载；修为结果小于 0 时由存档拒绝，核心不把修为夹到 0。
- 状态迁移函数仍可从 `xianwen.core` 导入，隔离留到后续 PR。
