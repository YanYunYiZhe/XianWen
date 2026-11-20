# XianWen 插件契约 v1

- 状态：第一周有效
- 更新时间：2026-11-20
- 适用代码：`develop` 上已经合并的 `Event`、`Choice`、`ChoiceEffect`
- 读者：插件作者和后续的加载器实现

本文是第一周纯数据插件的文件格式。加载器按本文把插件事件转换成核心公开类型。插件不读取、不修改 `GameState`。

`docs/契约文档.md` 里的 `SeedEvent`、`SeedChoice` 和 `StandardEffect` 是后续契约。第一周加载器不读取那些字段。地点、声望、好感、物品和 `PlayerState.location_id` 等 PR #2 合并并且边界确认后再改本文。

## 1. 插件目录

```text
plugins/<plugin-id>/
├── plugin.toml
└── content/
    └── events.toml
```

目录名必须等于 `plugin.toml` 里的 `id`。第一周不读取 `rules.py`、`locations.toml`、`characters.toml` 或 `endings.toml`。这些文件即使存在也不执行、不注册。

## 2. plugin.toml

必须是一个 `[plugin]` 表，且只包含下面四个字段。

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `id` | 字符串 | 插件命名空间。匹配 `^[a-z][a-z0-9-]*$`。不能是 `base`。全库唯一。 |
| `name` | 字符串 | 显示名称。去掉首尾空白后不能为空。 |
| `version` | 字符串 | 插件自身版本。去掉首尾空白后不能为空。第一周不解析语义化版本，也不读取兼容范围。推荐写成 `0.1.0`。 |
| `api_version` | 字符串 | 必须正好是 `"1"`。整数 `1` 不合法。 |

```toml
[plugin]
id = "official-example"
name = "官方示例插件"
version = "0.1.0"
api_version = "1"
```

## 3. events.toml

文件只包含 `[[events]]` 数组。每个插件至少有一个事件。不认识的表或字段一律拒绝。

每个事件的字段：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `id` | 字符串 | 见第 4 节。 |
| `fallback_scene_text` | 字符串 | 固定场景文本。去掉首尾空白后不能为空。无 AI 时原样展示。 |
| `choices` | 数组 | 2 到 4 个选项，不能多也不能少。 |

任务书中的 `fallback_text` 就是本文件的 `fallback_scene_text`。

每个选项的字段：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `id` | 字符串 | 见第 4 节。同一事件内唯一。 |
| `fallback_label` | 字符串 | 选项上显示的固定文字。去掉首尾空白后不能为空。 |
| `fallback_result_text` | 字符串 | 选择后展示的固定结果文本。去掉首尾空白后不能为空。 |
| `effect` | 表 | 见第 5 节。必须存在。 |

## 4. ID

事件 ID 必须正好是 `<plugin-id>.<事件名>`。

- `<plugin-id>` 与清单里的 `id` 完全相同。
- `<事件名>` 匹配 `^[a-z][a-z0-9_]*$`。
- 整个 ID 里只能有一个点。
- 作者自己写完整 ID。加载器只校验，不自动补前缀。
- 事件 ID 在全库唯一，不能占用 `base.morning_training`。

选项 ID 匹配 `^[a-z][a-z0-9_]*$`。它只需要在所属事件内唯一，不需要全局唯一，也不加插件前缀。

## 5. 效果

第一周只允许一种效果，对应现在核心里的 `ChoiceEffect`：

```toml
effect = { cultivation_delta = 1 }
```

- `effect` 里只能有 `cultivation_delta` 这一个键。
- 值必须是整数。
- 负数在类型上允许。当前存档要求结算后的修为大于等于 0，作者应使用不会把修为降到 0 以下的值。
- 声望、好感、物品、标记、地点切换都不是 `api_version = "1"` 的效果。
- 新效果以后用新的 `api_version` 增加，不在 `"1"` 里追加字段。

## 6. 转换成核心类型

加载器成功后，每个事件变成一个核心 `Event`：

| 插件字段 | 核心字段 |
| --- | --- |
| `id` | `Event.id` |
| `fallback_scene_text` | `Event.scene_text` |
| `choices[].id` | `Choice.id` |
| `choices[].fallback_label` | `Choice.label` |
| `choices[].fallback_result_text` | `Choice.result_text` |
| `choices[].effect.cultivation_delta` | `ChoiceEffect.cultivation_delta` |

状态变化仍只由 `apply_choice()` 应用。插件文件里不能出现 `GameState`，也不能提交新的状态快照。

## 7. 拒绝插件

出现下列任一情况时，拒绝整个插件，不注册它的任何事件：

- 缺少必填字段，或文本去掉空白后为空。
- `api_version` 不是 `"1"`。
- 插件 ID、事件 ID 或选项 ID 不符合第 4 节。
- 事件 ID 的命名空间不属于该插件。
- 选项数量不是 2 到 4 个。
- `effect` 缺少 `cultivation_delta`，或出现其他效果字段。
- 出现本文没有列出的字段或文件内容。
- 插件 ID 与已经成功加载的插件重复。后加载的那一个被拒绝，先加载的保留。

错误必须说明插件 ID 和失败原因。不能静默跳过，也不能让这个错误中断进程。

一个插件被拒绝后，基础事件 `base.morning_training` 仍然可用。其他已经成功加载的插件也保留。

## 8. 完整示例

```toml
# plugins/official-example/plugin.toml
[plugin]
id = "official-example"
name = "官方示例插件"
version = "0.1.0"
api_version = "1"
```

```toml
# plugins/official-example/content/events.toml
[[events]]
id = "official-example.meet_traveler"
fallback_scene_text = "青石镇外，老槐树下有一位披蓑衣的旅人正在歇脚。镇外山道通往后山，竹篮里飘出淡淡的草药香。"

[[events.choices]]
id = "talk"
fallback_label = "上前与旅人攀谈几句"
fallback_result_text = "旅人笑了笑，与你论了几句吐纳之道，你只觉灵台清朗，修为隐隐有所增长。"
effect = { cultivation_delta = 1 }

[[events.choices]]
id = "leave"
fallback_label = "默默绕开，继续赶路"
fallback_result_text = "你没有打扰旅人，沿着石板路继续往前走，今日修为一无所增。"
effect = { cultivation_delta = 0 }
```

地点背景写在 `fallback_scene_text` 里。不要写 `location_id`、`location_name` 或 `locations.toml`。

## 9. 加载器完成前

本文还没有加载函数，也没有 pytest 入口。加载器会另开 PR。在那之前，示例插件的集成测试保持跳过，不能把未执行的加载写成成功。

加载器 PR 需要证明：

- 合法插件能转成核心 `Event` 并注册。
- 缺少 `fallback_scene_text` 时加载失败。
- 缺少 `fallback_result_text` 时加载失败。
- 事件 ID 不属于插件命名空间时加载失败。
- 该插件失败后，`base.morning_training` 仍然可以游玩。
