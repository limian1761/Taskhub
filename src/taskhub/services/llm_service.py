"""
LLM service for the Taskhub system.
"""

import logging
import os
from openai import OpenAI
from taskhub.utils.config import config

logger = logging.getLogger(__name__)

# 从配置或环境变量获取API密钥
api_key = os.getenv("OPENAI_API_KEY", config.get("llm.api_key"))
client = OpenAI(api_key=api_key) if api_key else None


async def summarize_task_for_knowledge(task_details: str, report_result: str) -> tuple[str, str]:
    """
    Uses an LLM to summarize a task and its result into a knowledge item.
    Returns a tuple of (title, content).
    """
    if not client:
        logger.warning("LLM client not initialized. Skipping knowledge generation.")
        return "Knowledge Generation Skipped", "LLM client not initialized."
    
    logger.info("Generating knowledge summary with LLM...")
    prompt = f"""
    Based on the following task description and its successful result, please generate a concise and reusable knowledge item.

    The output should be in two parts, separated by "---":
    1. A short, clear title for the knowledge item.
    2. The main content of the knowledge, written in a way that is helpful for others facing a similar task.

    ---
    Task Description:
    {task_details}

    ---
    Successful Result/Report:
    {report_result}
    ---
    """
    try:
        response = client.chat.completions.create(
            model=config.get("llm.model_name"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        summary = response.choices[0].message.content
        if "---" in summary:
            title, content = summary.split("---", 1)
            return title.strip(), content.strip()
        else:
            # 如果没有按预期格式返回，将整个响应作为内容
            return "Task Summary", summary.strip()
    except Exception as e:
        logger.error(f"LLM summarization failed: {e}")
        # 在失败时返回一个明确的错误，而不是让整个流程崩溃
        return "Knowledge Generation Failed", f"Could not summarize task. Error: {e}"