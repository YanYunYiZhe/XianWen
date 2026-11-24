# E 岗位工作记录

- 岗位：E — AI、测试与发布（朱开滢）
- 计划依据：`docs/E_plan.md`、`docs/第一阶段任务书.md`
- 更新约定：覆盖更新本节，不追加长日志

---

## 第一阶段（工程与 CI 基线）— 已合并，历史 CI 待核验

- 完成日期：2026-11-17
- 合并：`chore/project-foundation` → `master`（PR #1）
- 本地 Git 记录确认实现提交 `da04424` 与合并提交 `2946cad`。待补 PR #1 的 Actions 运行链接、提交和结果。
- 交付：`pyproject.toml`、`uv.lock`、`/health`、冒烟测试、ruff/mypy/pytest、`.github/workflows/ci.yml`、README
- 本阶段未接入真实 AI

---

## 第二阶段（维护 CI + 支撑 Web 闭环）— 本地验证通过，待 CI 和 Review 验收

- 初版记录日期：2026-11-23
- 基于分支：`origin/develop`（已含 A 核心 + D Web 最小闭环）
- 工作分支：`feat/e-stage2-web-fixtures`
- 建议提交：`test: add shared web fixtures and no-model guards`
- 主要审查对象：D 的 Web / 存档实现（审查记录见下）

### 本阶段任务对照（E_plan §阶段 2）

| 任务 | 结果 |
| --- | --- |
| 跟进 A/D 合并后的测试失败，修工程配置 | develop 上本地门禁已绿；无需改游戏规则。CI workflow 已覆盖 `master`/`develop` |
| 为 D 的 Web 集成测试提供稳定夹具 | `tests/conftest.py` 提供客户端夹具，每次测试创建独立客户端，应用实例共享 |
| 确认测试不调用真实模型 | 回合测试省略 Key，阻断套接字连接，验证开局、选项结算和回合推进，断言零连接尝试 |
| 审查 D 的 PR | 已记录合并后复查和 2 条非阻塞提醒，待 D 回应与 E 复核 |
| 更新 `PROGRESS.md` | 已覆盖更新 |

### 已交付 / 改动文件

| 文件 | 作用 |
| --- | --- |
| `tests/conftest.py` | 共享应用实例与 TestClient 夹具 |
| `tests/integration/test_web.py` | 使用客户端夹具，修炼回合增加无 Key、零出站连接断言 |
| `tests/test_smoke.py` | `/health` 改用共享 `client` 夹具 |

### 对 D（Web / 存档）的 Review 记录

合并后复查：[D 的 Web PR #3](https://github.com/YanYunYiZhe/XianWen/pull/3)，实现提交 `e334894`、合并提交 `d9b1cb5`。复查覆盖路由、存档、模板和 Web 集成测试。

| 检查点 | 结论 |
| --- | --- |
| 路由是否直接修改 `GameState` | 通过。只调用 `new_game` / `apply_choice` / `get_current_event` |
| 非法选项错误是否清晰 | 通过。`InvalidChoiceError` → 400 +「该选项无效」 |
| 损坏存档处理 | 通过。`SaveFormatError` → 400 + 存档提示 |
| 存档是否含 API Key | 通过。`SaveDocument(extra="forbid")`；有 `api_key` 拒绝用例 |
| 页面状态来源 | 通过。展示字段来自核心返回值与事件公开字段 |

非阻塞提醒（不挡合并，记入后续）：

1. Web 仍使用 `LegacyGameState`，与新 `GameState` 迁移需单独 PR。
2. 集成测试原先使用模块级 `TestClient`；本阶段已改为夹具，后续 PR 请继续用 `client` fixture。

处理进度：E 已在本分支落实提醒 2。提醒 1 待 D 确认迁移安排，之后由 E 记录复核结果。D 对本阶段 E 的 PR 复核待开展。

### 本地已验证命令（退出码均为 0）

```powershell
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv build
```

实测：`pytest` **28 passed**（含 Web 8、冒烟 2 和核心单测 18）。无 Key、零出站连接检查并入 Web 回合用例。

### CI 真实状态

- workflow 已监听 `master` / `develop` 的 push 与 PR。
- 本机无法代替 GitHub Actions 成功证明；**推送本分支 / 开 PR 后须把 Actions 成败如实补记本节**。

### 本阶段明确不做

- 真实模型接入、Mock 适配器本体（计划书阶段 4）
- 插件测试纳入 CI（计划书阶段 3，依赖 B/C）
- 发行 Tag / ZIP / `RELEASE.md`

---

## 当前状态

- 阶段 1 工程基线已合并；阶段 2 已通过本地验证，待 CI 和 Review 验收。
- 待推送 `feat/e-stage2-web-fixtures` 并请 D 复核夹具改动；补记 CI 真实结果。

## 下一步

1. 推送本分支并开向 `develop` 的 PR。
2. B/C 插件闭环就绪后进入阶段 3（插件测试进 CI）。
3. 第一阶段全组验收通过后再做 AI / 发行。

## 阻塞 / 备注

- CI 真实成功记录仍待本分支推送后补全。
- `master` 仍落后于 `develop`；集成以 `develop` 为准。
