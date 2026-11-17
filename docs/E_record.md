# E 岗位工作记录

- 岗位：E — AI、测试与发布（朱开滢）
- 计划依据：`docs/E_plan.md`、`docs/第一阶段任务书.md` §8
- 更新约定：覆盖更新本节，不追加长日志

---

## 第一阶段（工程与 CI 基线）— 已完成

- 完成日期：2026-11-17
- 范围说明：对应任务书 §8 / 计划书「阶段 1」；**本阶段未接入真实 AI**（符合任务书「本阶段不包含真实模型调用」）。
- 建议分支 / 提交（待开 PR）：`chore/project-foundation` / `chore: initialize Python project and CI`
- 主要审查人：D 张板板

### 已交付文件

| 文件 | 作用 |
| --- | --- |
| `pyproject.toml` | 项目元数据；依赖；ruff / mypy / pytest / hatch 配置 |
| `uv.lock` | 可复现锁定依赖 |
| `.gitignore` | 排除 `.env`、venv、缓存、构建物、IDE 文件 |
| `README.md` | 安装、启动、质量命令说明 |
| `src/xianwen/__init__.py` | 包入口，`__version__ = "0.1.0"` |
| `src/xianwen/main.py` | FastAPI 入口与 `GET /health` |
| `tests/test_smoke.py` | 导入冒烟 + `/health` 断言 |
| `.github/workflows/ci.yml` | PR / `master` 推送时跑 sync → ruff → mypy → pytest → build |

### 健康检查约定

`GET /health` → `200`，固定 JSON：

```json
{"status": "ok", "service": "xianwen"}
```

### 本地已验证命令（退出码均为 0）

```powershell
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv build
```

实测结果摘要：

- Python：经 `uv` 安装并使用 **3.12.16**（满足 ≥3.12）。
- `pytest`：2 passed（`test_package_importable`、`test_health_returns_ok`）。
- `mypy src`：无问题。
- `ruff check` / `ruff format --check`：通过。
- `uv build`：产出 `dist/xianwen-0.1.0.tar.gz` 与 wheel。

### CI 真实状态

- 工作流文件已写入 `.github/workflows/ci.yml`。
- **尚未推送到 GitHub，因此尚无 Actions 真实运行记录。** 推送 / 开 PR 后须把成功或失败如实记入 `PROGRESS.md` 与本节。

### 未做（本阶段明确不做）

- 真实模型调用与主模型选型。
- AI 适配器、Mock、预算、后备模式实现（计划书阶段 4）。
- 发行 Tag / ZIP / `release/RELEASE.md`（计划书阶段 6）。
- 第 2–3 天任务：Web 测试夹具维护、插件测试纳入 CI（依赖 A/D/B/C 合并后再做）。

### 完成标准对照（任务书 §8.5）

| 标准 | 状态 |
| --- | --- |
| 所有质量命令退出码为 0 | 本地已满足 |
| GitHub Actions 至少触发一次并如实记录 | 待推送后补记 |
| 他人可从最新代码直接跑测试 | 本地骨架已具备；合并 `master` 后生效 |
| 未提交 `.env` / API Key | 满足（仓库无密钥文件） |

---

## 当前状态

- E 第一阶段工程基线代码与本地质量门禁已就绪。
- 待：建分支、开 PR 请 D Review、合并后触发 CI 并记录真实结果。

## 下一步

1. 推送 `chore/project-foundation` 并请 D Review。
2. CI 跑通后覆盖更新本节「CI 真实状态」与 `PROGRESS.md`。
3. A/D 合并后进入计划书阶段 2（维护 CI、Web 测试夹具、审 D）。

## 阻塞 / 备注

- 本机直连 PyPI / GitHub Release 曾失败；安装 `uv` 与同步依赖时使用了清华镜像 `https://pypi.tuna.tsinghua.edu.cn/simple`。CI（ubuntu-latest）通常可直连，若失败再改 workflow 镜像策略。
- `uv` 安装在用户 Scripts 目录；若终端找不到 `uv`，将 `AppData\Roaming\Python\Python311\Scripts` 加入 PATH，或用 `python -m uv`。
