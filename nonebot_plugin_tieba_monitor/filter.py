import json
from openai import AsyncOpenAI
from nonebot.log import logger

from .config import plugin_config


async def filter_with_ai(text, thread_info=None):
    """使用OpenAI库筛选帖子内容"""
    
    # 限制文本长度（如果配置了max_chars并且大于0）
    max_chars = plugin_config.tieba_ai_max_chars
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]
    
    # 初始化OpenAI客户端
    client = AsyncOpenAI(
        api_key=plugin_config.tieba_ai_apikey,
        base_url=plugin_config.tieba_ai_endpoint
    )
    
    try:
        messages = [
            {"role": "system", "content": plugin_config.tieba_ai_system_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await client.chat.completions.create(
            model=plugin_config.tieba_ai_model,
            messages=messages
        )
        
        ai_response = response.choices[0].message.content
        
        # 清理 AI 响应，移除Markdown代码块标记
        if ai_response.startswith("```"):
            first_newline = ai_response.find("\n")
            if (first_newline != -1):
                ai_response = ai_response[first_newline + 1:]
            
            if ai_response.endswith("```"):
                ai_response = ai_response[:-3].strip()
        
        # 尝试解析JSON响应
        try:
            ai_analysis = json.loads(ai_response)
            
            # 检查是否含有敏感内容或广告
            should_notify = True
            filtered_reason = []
            
            filter_keys = plugin_config.tieba_ai_filter_keys
            for key in filter_keys:
                if key in ai_analysis and ai_analysis[key] is True:
                    should_notify = False
                    filtered_reason.append(key)
            
            # 在thread_info中设置过滤标记
            if not should_notify and thread_info:
                thread_info["should_notify"] = False
                thread_info["filtered_reason"] = filtered_reason
            
            return ai_analysis
        except json.JSONDecodeError as e:
            return {"raw_response": ai_response, "parse_error": str(e)}
            
    except Exception as e:
        logger.error(f"AI筛选过程中出错: {e}")
        return {"error": str(e)}