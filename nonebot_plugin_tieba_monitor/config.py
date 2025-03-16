from typing import Dict, List, Optional, Union, Any
from nonebot import get_plugin_config
from nonebot.log import logger
from pydantic import BaseModel, Field, validator
import os


# 默认系统提示
DEFAULT_AI_SYSTEM_PROMPT = """
你是一个帖子内容分析助手。请分析以下贴吧帖子内容，提取其中的关键信息，包括:
1. 主要话题: 帖子主要讨论的内容
2. 情感倾向: 必须为"积极"、"消极"或"中性"之一
3. 是否包含敏感内容: 政治敏感、暴力、色情等内容，返回true或false
4. 是否包含广告、营销信息: 引流、联系方式、产品推销等，返回true或false
5. 包含敏感话题: 政治敏感、暴力、色情等内容，返回true/false（与字段3同义）
6. 包含广告: 引流、联系方式、产品推销等，返回true/false（与字段4同义）

请严格审核内容，只要有一点敏感内容或广告信息就应该返回true。

请直接返回纯JSON格式，不要包含Markdown代码块标记(```)。
返回格式示例:
{
  "主要话题": "话题内容",
  "情感倾向": "积极/消极/中性",
  "是否包含敏感内容": true/false,
  "是否包含广告、营销信息": true/false,
  "包含敏感话题": true/false,
  "包含广告": true/false
}
"""


# 辅助函数：解析字符串布尔值
def parse_bool(value: Any) -> bool:
    """解析各种格式的布尔值"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        # 兼容各种格式的"true"
        return value.lower() in ('true', 't', 'yes', 'y', '1')
    # 当作数字处理
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return False


class Config(BaseModel):
    """贴吧监控插件配置"""
    # 贴吧监控设置
    tieba_check_interval_seconds: int = Field(default=300, description="检查新帖子的时间间隔（秒）")
    tieba_output_directory: str = Field(default="data/tieba_data", description="保存帖子数据的文件夹路径")
    tieba_threads_to_retrieve: int = Field(default=5, description="每次检查时获取的最新帖子数量")
    
    # 每个贴吧单独的通知群组配置 - 现在仅使用此配置决定要监控哪些贴吧和要发送到哪些群组
    tieba_forum_groups: Dict[str, List[int]] = Field(
        default={},
        description="每个贴吧特定的通知群组，格式为：{'贴吧名称': [群号1, 群号2]}"
    )
    
    # AI筛选配置 - 直接放在Config类中，避免嵌套
    tieba_ai_enabled: bool = Field(default=False, description="是否启用AI分析")
    tieba_ai_apikey: str = Field(default="", description="AI API密钥")
    tieba_ai_endpoint: str = Field(default="https://api.openai.com/v1", description="AI API端点")
    tieba_ai_model: str = Field(default="gpt-3.5-turbo", description="AI模型名称")
    tieba_ai_max_chars: int = Field(default=100, description="发送给AI的最大字符数")
    tieba_ai_filter_keys: List[str] = Field(
        default=["是否包含敏感内容", "是否包含广告、营销信息"],
        description="AI分析结果中的关键字段"
    )
    tieba_ai_system_prompt: str = Field(
        default=DEFAULT_AI_SYSTEM_PROMPT,
        description="AI分析使用的系统提示词"
    )
    
    @validator('tieba_ai_enabled', pre=True)
    def parse_enabled(cls, v, values, **kwargs):
        """处理各种格式的布尔值"""
        return parse_bool(v)
    
    class Config:
        # 允许额外字段
        extra = "ignore"
        # 允许从环境变量读取
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 确保环境变量正确设置
env_enabled = os.environ.get('TIEBA_AI_ENABLED', '')
if env_enabled:
    os.environ['TIEBA_AI_ENABLED'] = str(parse_bool(env_enabled)).lower()

# 获取插件配置
plugin_config = get_plugin_config(Config)

# 输出简化的配置信息
logger.info(f"贴吧监控配置加载完成: {len(plugin_config.tieba_forum_groups)}个贴吧, 间隔{plugin_config.tieba_check_interval_seconds}秒")
logger.info(f"AI分析状态: {'已启用' if plugin_config.tieba_ai_enabled else '未启用'}")

if plugin_config.tieba_ai_enabled:
    # 检查API密钥是否配置
    api_key_status = "已配置" if plugin_config.tieba_ai_apikey else "未配置"
    logger.info(f"AI配置: 模型={plugin_config.tieba_ai_model}, API密钥={api_key_status}")


def get_tieba_config():
    """获取贴吧监控的配置"""
    return {
        "forums": list(plugin_config.tieba_forum_groups.keys()),
        "check_interval_seconds": plugin_config.tieba_check_interval_seconds,
        "output_directory": plugin_config.tieba_output_directory,
        "threads_to_retrieve": plugin_config.tieba_threads_to_retrieve,
        "forum_groups": plugin_config.tieba_forum_groups
    }


def get_ai_config():
    """获取AI相关配置"""
    return {
        "enabled": plugin_config.tieba_ai_enabled,
        "api_key": plugin_config.tieba_ai_apikey,
        "api_endpoint": plugin_config.tieba_ai_endpoint,
        "model": plugin_config.tieba_ai_model,
        "max_chars": plugin_config.tieba_ai_max_chars,
        "system_prompt": plugin_config.tieba_ai_system_prompt,
        "filter_keys": plugin_config.tieba_ai_filter_keys
    }


def get_notify_groups_for_forum(forum_name: str) -> List[int]:
    """获取特定贴吧的通知群组列表"""
    return plugin_config.tieba_forum_groups.get(forum_name, [])