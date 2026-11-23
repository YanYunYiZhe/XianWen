# Progress

## 当前状态
- 草稿分支 `feat/seed-contract-draft` 已 rebase 到最新 `develop`，暂不合并。
- 已实现受控内容草案、策略结构、确定性校验和正式 ID 分配。
- 已实现 ValidatedGeneratedContent 到 GeneratedContentStore 的原子登记。
- ruff、format、mypy、66 个测试和 build 均通过。

## 下一步
- 实现候选种子筛选，从基础与生成内容中选出 2-3 个候选。
- 接入 AI Mock，返回 ContentGenerationDraft 并验证失败回退。
- 补充存档序列化与恢复测试。

## 已知问题
- 条件 DSL 和 `StateRequirement` 求值器尚未实现。
- `StandardEffect` 白名单和数值边界尚未冻结。
- 当前仅支持 cultivation_delta 和 luck_delta。
- 生成事件已能转换为 SeedEvent，下一步实现候选种子筛选。
- 新 `GameState` 的 Web 对接和后续存档迁移尚未完成。