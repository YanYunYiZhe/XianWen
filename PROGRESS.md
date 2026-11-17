# Progress

## 当前状态
- 第一阶段任务书已定；成员：A 顾婷婷、B 田梦婷、C 田代文利、D 张板板、E 朱开滢。
- E 工程基线已落地：`pyproject.toml`、`uv.lock`、`src/xianwen`、`/health`、冒烟测试、ruff/mypy/pytest、`.github/workflows/ci.yml`、README。
- 本地质量命令均已跑通（退出码 0）：`uv sync --frozen`、ruff、mypy、pytest（2 passed）、`uv build`。
- E 工作记录见 `docs/E_record.md`；计划书见 `docs/E_plan.md`。
- CI 工作流已写好，**尚未推送，无 GitHub Actions 真实运行记录**。

## 下一步
- E：开 `chore/project-foundation` PR，请 D Review；合并后记录 CI 真实结果。
- A：基于骨架实现最小核心回合；D：页面接入；B/C：插件契约与样例。
- E 在 A/D 合并后维护 Web 测试夹具；插件测试进 CI；阶段一全过后再做 AI/发行。

## 已知问题
- GitHub Actions 尚未触发，不能宣称 CI 已成功。
- LICENSE、docs/DESIGN.docx、发行物尚未完成。
- 插件字段、完整状态 schema、内容预算和主模型预设尚未锁定。
- 本机曾需清华 PyPI 镜像才能安装依赖；CI 环境待首次推送验证。
