# nonebot-plugin-tieba-monitor

基于 [NoneBot2](https://nonebot.dev/) 的贴吧帖子监控插件，用于监控指定贴吧的新帖子并发送到 QQ 群。

## 功能特性

- 监控多个贴吧的新帖子
- 支持自定义检查时间间隔
- 支持多群组通知
- 支持 AI 内容分析与过滤（可选）

## 安装

### 使用 nb-cli

```bash
nb plugin install nonebot-plugin-tieba-monitor
```

## 使用方法

1. 在 NoneBot2 项目中，确保配置了 OneBot 适配器
2. 在 `.env` 文件中添加插件配置
3. 启动 NoneBot2，插件将自动运行并按照配置的时间间隔监控贴吧

## 配置项

在 `.env` 文件中，你可以配置以下参数：

### 基础配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `tieba_check_interval_seconds` | int | 300 | 检查新帖子的时间间隔（秒） |
| `tieba_output_directory` | str | "data/tieba_data" | 保存帖子数据的文件夹路径 |
| `tieba_threads_to_retrieve` | int | 5 | 每次检查时获取的最新帖子数量 |
| `tieba_forum_groups` | Dict[str, List[int]] | {} | 每个贴吧特定的通知群组，格式为：`{'贴吧名称': [群号1, 群号2]}` |

### AI 分析配置（可选）

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `tieba_ai_enabled` | bool | false | 是否启用 AI 分析 |
| `tieba_ai_apikey` | str | "" | AI API 密钥 |
| `tieba_ai_endpoint` | str | "https://api.openai.com/v1" | AI API 端点 |
| `tieba_ai_model` | str | "gpt-3.5-turbo" | AI 模型名称 |
| `tieba_ai_max_chars` | int | 100 | 发送给 AI 的最大字符数 |
| `tieba_ai_system_prompt` | str | (见代码) | AI 分析使用的系统提示词，用于自定义 AI 的分析行为 |
| `tieba_ai_filter_keys` | List[str] | ["是否包含敏感内容", "是否包含广告、营销信息"] | AI 分析结果中的关键字段(搭配系统提示词使用) |

## 配置示例

```dotenv
# 基础配置
tieba_check_interval_seconds=300
tieba_output_directory=data/tieba_data
tieba_threads_to_retrieve=10

# 贴吧监控配置 - 格式: {'贴吧名': [群号1, 群号2]}
# 例如监控"王者荣耀"贴吧并发送到群 123456789 和 987654321
tieba_forum_groups={"王者荣耀": [123456789, 987654321], "英雄联盟": [123456789]}

# AI 分析配置（可选）
tieba_ai_enabled=false
tieba_ai_apikey=your_api_key
tieba_ai_endpoint=https://api.openai.com/v1
tieba_ai_model=gpt-3.5-turbo
tieba_ai_max_chars=500
tieba_ai_filter_keys=["是否包含敏感内容", "是否包含广告、营销信息"]
tieba_ai_system_prompt="""你是一个帖子内容分析助手。分析以下内容并返回JSON格式的结果..."""
```


## 注意事项

- 请确保 `.env` 文件中的 `tieba_forum_groups` 参数格式正确
- 若启用 AI 分析功能，请提供有效的 API 密钥
- 首次启动时，插件将立即执行一次贴吧检查
- 如需自定义 AI 提示词，请确保返回格式与默认提示词一致

## 更多信息

- 本插件利用 `aiotieba` 库进行贴吧内容获取
- 使用 `nonebot-plugin-apscheduler` 进行定时任务管理
- 插件会将帖子数据保存在配置的输出目录中


## 许可证
本项目使用 [GNU AGPLv3](https://choosealicense.com/licenses/agpl-3.0/) 作为开源许可证。
