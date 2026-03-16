from utils.config_handler import prompts_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger
import os


def load_system_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_conf["main_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_system_prompts]在yaml配置项中没有main_prompt_path配置项")
        raise e

    try:
        prompts_dir = os.path.dirname(system_prompt_path)

        prompt_files = [
            "IDENTITY.md",
            "SOUL.md",
            "AGENTS.md",
        ]

        parts = [open(system_prompt_path, "r", encoding="utf-8").read()]

        for pf in prompt_files:
            pf_path = os.path.join(prompts_dir, pf)
            if os.path.exists(pf_path):
                content = open(pf_path, "r", encoding="utf-8").read()
                parts.append(f"\n\n=== {pf} ===\n\n{content}")

        return "\n".join(parts)
    except Exception as e:
        logger.error(f"[load_system_prompts]解析系统提示词出错，{str(e)}")
        raise e


def load_user_prompt(user_id: str) -> str:
    """加载指定用户ID的用户画像"""
    try:
        prompts_dir = get_abs_path(
            prompts_conf.get("user_prompts_dir", "prompts/users")
        )
        user_prompt_path = os.path.join(prompts_dir, f"USER_{user_id}.md")

        if os.path.exists(user_prompt_path):
            return open(user_prompt_path, "r", encoding="utf-8").read()
        else:
            logger.info(f"[load_user_prompt]未找到用户 {user_id} 的画像文件")
            return ""
    except Exception as e:
        logger.error(f"[load_user_prompt]加载用户画像出错，{str(e)}")
        return ""


def load_rag_prompts():
    try:
        rag_prompt_path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])
    except KeyError as e:
        logger.error(
            f"[load_rag_prompts]在yaml配置项中没有rag_summarize_prompt_path配置项"
        )
        raise e

    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_rag_prompts]解析RAG总结提示词出错，{str(e)}")
        raise e


def load_report_prompts():
    try:
        report_prompt_path = get_abs_path(prompts_conf["report_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_report_prompts]在yaml配置项中没有report_prompt_path配置项")
        raise e

    try:
        return open(report_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_report_prompts]解析报告生成提示词出错，{str(e)}")
        raise e


if __name__ == "__main__":
    print(load_system_prompts())
