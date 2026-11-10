# Progress

## 当前状态
- 5 人分组已获教师批准；课程 MVP 已收窄为 10 回合、2 结局、2 世界线、1 个主模型和 1 个组内扩展。
- PRD 已改为由组内非核心成员完成独立扩展，不再要求外部作者。
- 五人分工说明已写入 `docs/分工说明.md`；角色姓名、首次 PR 和实际 Review 记录待确认。
- GitHub 远程 `origin/master` 已配置；当前文档改动尚未提交。
- 工程、测试、CI、正式设计文档和发行物仍未建立。

## 下一步
- 确认成员与角色，并固定交叉 Review 配对。
- 初始化 Python 工程和质量基线。
- 编写插件公开契约，并由非核心成员据此实现独立扩展。
- 选择唯一主模型预设并准备 Mock/后备路径。
- 建立 GitHub Actions、Tag 和 release/RELEASE.md 流程。

## 已知问题
- 岗位最终人选和 Review 配对尚未确认。
- 无 pyproject.toml、uv.lock、源码和测试，类型检查、Lint、测试不可执行。
- README、LICENSE、docs/DESIGN.docx、CI 和发行物尚未完成。
- 插件字段、状态 schema、内容预算和主模型预设尚未锁定。