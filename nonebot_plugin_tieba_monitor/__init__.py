from nonebot import get_driver, require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
import asyncio

# 导入调度器
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .config import Config, plugin_config, get_tieba_config, get_ai_config

__plugin_meta__ = PluginMetadata(
    name="贴吧监控",
    description="监控指定贴吧的新帖子并发送到QQ群",
    usage="在.env文件中配置参数，插件会自动运行",
    type="application",
    homepage="https://github.com/su-liu-guang/nonebot-plugin-tieba-monitor",
    config=Config,
    supported_adapters={"~onebot.v11"},

)

from .tieba import check_and_save_new_threads_and_notify

# 启动时初始化定时任务
@get_driver().on_startup
async def _():
    tieba_config = get_tieba_config()
    forums = tieba_config["forums"]
    
    if not forums:
        logger.warning("没有配置任何贴吧监控，插件将不会执行任何操作")
        return
        
    # 设置定时任务，按照配置的时间间隔执行检查
    scheduler.add_job(
        check_tieba_updates,
        "interval", 
        seconds=tieba_config["check_interval_seconds"],
        id="tieba_monitor",
        replace_existing=True
    )
    
    logger.info(f"贴吧监控已启动: {len(forums)}个贴吧，间隔{tieba_config['check_interval_seconds']}秒")
    
    # 启动后立即执行一次贴吧检查
    asyncio.create_task(initial_check_tieba_updates())

async def initial_check_tieba_updates():
    """启动时执行的贴吧更新检查"""
    # 延迟2秒，确保Bot已完全初始化
    await asyncio.sleep(2)
    tieba_config = get_tieba_config()
    
    try:
        bot = get_bot()
        
        for tieba_name in tieba_config["forums"]:
            await check_and_save_new_threads_and_notify(tieba_name, bot)
    except Exception as e:
        logger.error(f"启动初始检查过程中出错: {e}")

async def check_tieba_updates():
    """定时检查贴吧更新的任务"""
    tieba_config = get_tieba_config()
    bot = get_bot()
    
    if not bot:
        logger.warning("无法获取Bot实例，跳过本次贴吧检查")
        return
        
    for tieba_name in tieba_config["forums"]:
        await check_and_save_new_threads_and_notify(tieba_name, bot)

def get_bot() -> Bot:
    """获取可用的Bot实例"""
    from nonebot import get_bot as _get_bot
    try:
        return _get_bot()
    except ValueError:
        return None