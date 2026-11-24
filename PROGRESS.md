# Progress

## 当前状态
- 本分支已合并最新 `develop`（含 PR #2 的新状态和 PR #8 的测试夹具）。
- 插件契约 v1 写明只服务 `LegacyGameState` 兼容回合，效果是 `ChoiceEffect.cultivation_delta`。
- 加载器在 PR #9，示例插件在草稿 PR #4，都还没有进入 `develop`。

## 下一步
- 请 C 复审更新后的 PR #5，通过后再合并进 `develop`。
- A、C 审核加载器 PR #9。
- 契约和加载器都进入 `develop` 后，C 再启用示例插件测试。

## 已知问题
- `get_current_event()` 仍只返回基础事件。
- 负数 `cultivation_delta` 可以加载；修为小于 0 由存档拒绝。
- `StandardEffect` 留到下一版 `api_version`。
