import asyncio
import random
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.log import logger


async def send_thread_notification(bot: Bot, group_id: int, thread_info):
    """发送帖子通知到QQ群"""
    if bot is None:
        logger.error("无法发送通知，Bot实例不可用")
        return False
    
    try:
        # 构建通知消息
        message = Message()
        
        # 添加贴吧名和标题
        tieba_name = thread_info.get('tieba_name', '未知贴吧')
        message += MessageSegment.text(f"【{tieba_name}吧】{thread_info['title']}\n")
        
        # 添加作者
        message += MessageSegment.text(f"作者: {thread_info['author_id']}\n")
        
        # 添加内容摘要（限制长度）
        content = thread_info['text']
        if len(content) > 100:
            content = content[:100] + "..."
        message += MessageSegment.text(f"内容: {content}\n")
        
        # 添加链接
        message += MessageSegment.text(f"链接: {thread_info['url']}\n")
        
        # 添加发布时间
        message += MessageSegment.text(f"发布时间: {thread_info['create_time']}\n")
        
        # 如果有AI分析，添加分析结果
        if 'ai_analysis' in thread_info and thread_info['ai_analysis']:
            ai_analysis = thread_info['ai_analysis']
            analysis_text = "\n【AI分析】\n"
            
            # 格式化AI分析内容
            if "主要话题" in ai_analysis:
                analysis_text += f"主要话题: {ai_analysis['主要话题']}\n"
                
            if "情感倾向" in ai_analysis:
                analysis_text += f"情感倾向: {ai_analysis['情感倾向']}\n"
                
            message += MessageSegment.text(analysis_text)
        
        # 如果有图片，添加所有图片
        if thread_info['images'] and len(thread_info['images']) > 0:
            for image_url in thread_info['images']:
                message += MessageSegment.image(image_url)
        
        # 发送消息到群
        await bot.send_group_msg(group_id=group_id, message=message)
        return True
    except Exception as e:
        logger.error(f"发送通知到群 {group_id} 时出错: {e}")
        return False


async def send_notifications_to_groups(new_threads, notify_groups, bot, tieba_name):
    """向多个群组发送新帖子通知"""
    if not new_threads or not notify_groups or not bot:
        return 0, 0  # 成功0条，失败0条
    
    logger.info(f"向 {len(notify_groups)} 个群组发送 {len(new_threads)} 条通知")
    success_count = 0
    fail_count = 0
    
    for group_id in notify_groups:
        for thread_info in new_threads:
            result = await send_thread_notification(bot, group_id, thread_info)
            if result:
                success_count += 1
            else:
                fail_count += 1
            # 添加随机延迟10-50毫秒，避免风控
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    logger.info(f"通知发送完成: 成功{success_count}条，失败{fail_count}条")
    return success_count, fail_count 