import asyncio
import json
import os
import datetime

import aiotieba
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger

from .config import get_tieba_config, get_ai_config, get_notify_groups_for_forum
from .filter import filter_with_ai
from .notification import send_notifications_to_groups


async def check_and_save_new_threads_and_notify(tieba_name, bot=None):
    """检查并保存指定贴吧的新帖子，并发送通知"""
    # 获取配置
    tieba_config = get_tieba_config()
    ai_config = get_ai_config()
    
    # 提取配置项
    output_dir = tieba_config["output_directory"]
    threads_to_retrieve = tieba_config["threads_to_retrieve"]
    ai_enabled = ai_config["enabled"]
    
    logger.info(f"检查贴吧[{tieba_name}]")
    
    # 获取通知群组，如无则跳过
    notify_groups = get_notify_groups_for_forum(tieba_name)
    if not notify_groups:
        return True
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建输出文件路径
    output_path = os.path.join(output_dir, f"{tieba_name}.json")
    
    # 加载现有帖子数据
    existing_threads = []
    existing_tids = set()
    ai_analyzed_tids = set()
    
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_threads = json.load(f)
                existing_tids = {thread["tid"] for thread in existing_threads}
                ai_analyzed_tids = {
                    thread["tid"] for thread in existing_threads 
                    if "ai_analysis" in thread and thread["ai_analysis"]
                }
        except Exception as e:
            logger.error(f"读取贴吧[{tieba_name}]现有文件时出错: {e}")
    
    new_threads_added = False
    updates_made = False  
    new_threads = []  
    
    try:
        async with aiotieba.Client() as client:
            # 获取帖子，按创建时间排序
            threads = await client.get_threads(tieba_name, sort=aiotieba.ThreadSortType.CREATE)
            for thread in threads[0:threads_to_retrieve]:
                thread_is_new = thread.tid not in existing_tids
                
                if thread_is_new:
                    # 处理新帖子
                    thread_info = {
                        "tid": thread.tid,
                        "title": thread.title,
                        "author_id": thread.user.nick_name_new,
                        "url": f"https://tieba.baidu.com/p/{thread.tid}",
                        "create_time": datetime.datetime.fromtimestamp(thread.create_time).strftime("%Y-%m-%d %H:%M:%S"),
                        "text": thread.text,
                        "images": [],
                        "tieba_name": tieba_name
                    }
                    
                    # 获取图片
                    if thread.contents.imgs:
                        base_url = "https://imgsa.baidu.com/forum/pic/item/"
                        thread_info["images"] = [f"{base_url}{img.hash}.jpg" for img in thread.contents.imgs]
                    
                    # AI分析
                    if ai_enabled and thread.tid not in ai_analyzed_tids:
                        thread_info["ai_analysis"] = await filter_with_ai(thread.text, thread_info)
                        ai_analyzed_tids.add(thread.tid)
                    
                    existing_threads.append(thread_info)
                    
                    # 只有未被过滤的帖子才加入通知列表
                    if thread_info.get("should_notify", True):
                        new_threads.append(thread_info)
                        
                    new_threads_added = True
                    updates_made = True
                elif ai_enabled and thread.tid not in ai_analyzed_tids:
                    # 为已存在但未分析的帖子添加AI分析
                    for existing_thread in existing_threads:
                        if existing_thread["tid"] == thread.tid:
                            existing_thread["ai_analysis"] = await filter_with_ai(existing_thread["text"], existing_thread)
                            ai_analyzed_tids.add(thread.tid)
                            updates_made = True
                            break
        
        # 更新文件
        if updates_made:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(existing_threads, f, ensure_ascii=False, indent=4)
                
            if new_threads_added:
                # 统计过滤数据
                total_new = sum(1 for t in existing_threads 
                               if t["tid"] in [thread.tid for thread in threads[0:threads_to_retrieve]] 
                               and t["tid"] not in (existing_tids - {t["tid"] for t in new_threads}))
                filtered_count = total_new - len(new_threads)
                
                logger.info(f"贴吧[{tieba_name}]发现{total_new}条新帖子，过滤{filtered_count}条，将发送{len(new_threads)}条通知")
            else:
                logger.info(f"贴吧[{tieba_name}]更新了AI分析结果")
        
        # 发送通知
        if new_threads and notify_groups and bot:
            await send_notifications_to_groups(new_threads, notify_groups, bot, tieba_name)
        
        return True
    except Exception as e:
        logger.error(f"获取贴吧[{tieba_name}]帖子或发送通知时出错: {e}")
        return False


# 测试入口
if __name__ == "__main__":
    tieba_config = get_tieba_config()
    forums = tieba_config["forums"]
    
    if forums:
        print(f"将检查以下贴吧: {', '.join(forums)}")
        for tieba_name in forums:
            asyncio.run(check_and_save_new_threads_and_notify(tieba_name))
    else:
        print("没有配置任何贴吧监控，请检查环境变量")

