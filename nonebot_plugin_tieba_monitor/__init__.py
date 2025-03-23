from nonebot import get_driver, require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
import asyncio

# 导入调度器
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

# 导入配置
from .config import Config, plugin_config
from .tieba import check_and_save_new_threads_and_notify

__plugin_meta__ = PluginMetadata(
    name="贴吧监控",
    description="监控指定贴吧的新帖子并发送到QQ群",
    usage="在NoneBot配置中设置参数，插件会自动运行",
    type="application",
    homepage="https://github.com/su-liu-guang/nonebot-plugin-tieba-monitor",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# 获取Bot实例的函数
def get_bot() -> Bot:
    """获取可用的Bot实例"""
    from nonebot import get_bot as _get_bot
    try:
        return _get_bot()
    except ValueError:
        return None

# 贴吧检查函数
async def check_tieba_updates():
    """检查贴吧更新的任务"""
    try:
        bot = get_bot()
        if not bot:
            logger.warning("无法获取Bot实例，跳过本次贴吧检查")
            return
        forums = list(plugin_config.tieba_forum_groups.keys())
        for tieba_name in forums:
            await check_and_save_new_threads_and_notify(tieba_name, bot)
    except Exception as e:
        logger.error(f"贴吧检查过程中出错: {e}")

# 启动时初始化定时任务
@get_driver().on_startup
async def init_tieba_monitor():
    """初始化贴吧监控"""   
    forums = list(plugin_config.tieba_forum_groups.keys())
    
    if not forums:
        logger.warning("没有配置任何贴吧监控，插件将不会执行任何操作")
        return
        
    # 设置定时任务
    interval = plugin_config.tieba_check_interval_seconds
    scheduler.add_job(
        check_tieba_updates,
        "interval", 
        seconds=interval,
        id="tieba_monitor",
        replace_existing=True
    )
    
    logger.info(f"贴吧监控已启动: {len(forums)}个贴吧，间隔{interval}秒")
    
    # 启动后延迟2秒执行一次初始检查
    asyncio.create_task(delayed_initial_check())

async def delayed_initial_check():
    """延迟执行初始检查，确保Bot已完全初始化"""
    await asyncio.sleep(2)
    await check_tieba_updates()