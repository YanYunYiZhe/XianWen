# XianWen

浏览器端修仙文字游戏（课程 MVP）。规则由确定性 Python 代码执行，AI 只负责允许范围内的剧情扩写。

## 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## 安装

```powershell
uv sync
```

若本机尚无 Python 3.12，可先执行：

```powershell
uv python install 3.12
uv sync
```

## 启动

```powershell
uv run uvicorn xianwen.main:app --reload
```

健康检查：访问 `http://127.0.0.1:8000/health`，应返回 `{"status":"ok","service":"xianwen"}`。

## 质量命令

本地与 CI 使用同一组命令：

```powershell
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv build
```

## 项目结构（第一阶段）

```text
src/xianwen/     应用源码（core / plugins / web / ai 由各岗位后续补齐）
tests/           测试
.github/workflows/ci.yml
docs/            产品与分工文档
```

## 安全提示

- 不要提交 `.env`、API Key 或真实模型凭据。
- 用户 Key 只应存在于页面内存，经服务端即时转发，不写入存档或日志。

## 文档

- 产品范围：`docs/prd-v1.md`
- 技术方案：`docs/tech-design-v1.md`
- 分工说明：`docs/分工说明.md`
- 第一阶段任务：`docs/第一阶段任务书.md`
- 当前进度：`PROGRESS.md`
