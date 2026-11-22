# Progress

## 当前状态
- 当前在草稿分支 `feat/seed-contract-draft`，不合并到 `develop`。
- 已实现 `SeedEvent`、`SeedChoice`、`NarrativeBrief` 和条件结构。
- 已实现无 AI 后备渲染及 `NarrativeDraft` 确定性校验。
- ruff、format、mypy、31 个测试和 build 均通过。

## 下一步
- 实现候选种子筛选和固定种子选择。
- 实现 `StandardEffect` 到 `PlayerState` 的最小应用。
- 实现 `PlayerState + WorldSnapshot` 的同版本原子回合结算。

## 已知问题
- 条件 DSL 和 `StateRequirement` 求值器尚未实现。
- `StandardEffect` 白名单和数值边界尚未冻结。
- AI 适配器和模型响应解析尚未实现。
- 草稿分支基于未合并的 PR #2，合并前必须 rebase 到最新 `develop`。