# Progress

## 当前状态
- 技术方案已写入 `docs/tech-design-v1.md`，锁定 Python、FastAPI、Jinja2、HTMX、Alpine、uv、Docker 和 GitHub Actions。
- 玩家状态采用浏览器 `localStorage`，服务端无状态；未来通过仓储层迁移到数据库。
- 插件采用独立包、声明式内容加受限 Python 规则，并通过 `api_version` 演进。
- 工程尚未初始化，类型检查、测试和 Lint 仍不可执行。

## 下一步
- 讨论并编写插件规范与官方示例包契约。
- 初始化 Python 工程并建立 ruff、mypy、pytest 可执行基线。
- 实测三家模型预设并选择 Docker 托管平台。

## 已知问题
- 托管平台、默认模型和有限模型列表尚未锁定。
- 插件字段、游戏状态 schema 和外部作者档期尚未落实。
- 内容预算仍待最终确认。
