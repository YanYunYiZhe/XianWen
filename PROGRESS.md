# Progress

## 当前状态
- 当前在草稿分支 `feat/seed-contract-draft`，不合并到 `develop`。
- 已实现种子、叙事草稿、后备渲染和确定性校验。
- 已实现最小种子回合原子结算，当前支持 `cultivation_delta`。
- ruff、format、mypy、38 个测试和 build 均通过。

## 下一步
- 实现候选种子筛选和 2-3 个候选的确定性选择。
- 增加物品、关系、声望和标记效果的核心应用规则。
- 接入 AI 叙事 Mock，并验证 AI 失败时自动回退。

## 已知问题
- 条件 DSL 和 `StateRequirement` 求值器尚未实现。
- `StandardEffect` 白名单和数值边界尚未冻结。
- `SeedTurnResult` 尚未与旧 `TurnResult` 统一。
- 草稿分支基于未合并的 PR #2，合并前必须 rebase 到最新 `develop`。