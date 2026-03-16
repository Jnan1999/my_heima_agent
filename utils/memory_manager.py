"""
会话记忆管理模块

提供会话存储和长期记忆管理功能：
1. 会话存储：memory/sessions/{session_id}.md
2. 长期记忆：memory/{user_id}/MEMORY.md
3. 归档备份：memory/archives/
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from utils.logger_handler import logger
from utils.path_tool import get_abs_path


MEMORY_BASE_DIR = "memory"
SESSIONS_DIR = os.path.join(MEMORY_BASE_DIR, "sessions")
ARCHIVES_DIR = os.path.join(MEMORY_BASE_DIR, "archives")


def ensure_dirs():
    """确保目录存在"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(ARCHIVES_DIR, exist_ok=True)


def get_session_file_path(user_id: str, session_id: str) -> str:
    """获取会话文件路径"""
    ensure_dirs()
    return os.path.join(SESSIONS_DIR, f"{user_id}_{session_id}.md")


def get_memory_file_path(user_id: str) -> str:
    """获取长期记忆文件路径"""
    ensure_dirs()
    user_dir = os.path.join(MEMORY_BASE_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "MEMORY.md")


def get_archive_file_path(user_id: str) -> str:
    """获取归档文件路径"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(ARCHIVES_DIR, f"{user_id}_{timestamp}.md")


def list_user_sessions(user_id: str) -> List[Dict[str, str]]:
    """列出用户的所有会话

    Args:
        user_id: 用户ID

    Returns:
        会话列表，每个元素包含 session_id, title, created_at, updated_at
    """
    ensure_dirs()
    sessions = []

    if not os.path.exists(SESSIONS_DIR):
        return sessions

    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".md") and filename.startswith(f"{user_id}_"):
            filepath = os.path.join(SESSIONS_DIR, filename)
            session_id = filename[:-3].replace(f"{user_id}_", "")

            stat = os.stat(filepath)
            created_at = datetime.fromtimestamp(stat.st_ctime).strftime(
                "%Y-%m-%d %H:%M"
            )
            updated_at = datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )

            title = extract_session_title(filepath)

            sessions.append(
                {
                    "session_id": session_id,
                    "title": title,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )

    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


def extract_session_title(filepath: str, max_len: int = 30) -> str:
    """从会话文件中提取标题"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
            for line in lines:
                if line.startswith("## "):
                    return line[3:].strip()
            if lines:
                first_line = lines[0].strip()
                return (
                    first_line[:max_len] + "..."
                    if len(first_line) > max_len
                    else first_line
                )
    except Exception as e:
        logger.warning(f"提取会话标题失败: {e}")
    return "新会话"


def save_session(user_id: str, session_id: str, messages: List[Dict[str, str]]):
    """保存会话内容到文件

    Args:
        user_id: 用户ID
        session_id: 会话ID
        messages: 消息列表
    """
    filepath = get_session_file_path(user_id, session_id)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# 会话记录\n\n")
            f.write(f"- **用户ID**: {user_id}\n")
            f.write(f"- **会话ID**: {session_id}\n")
            f.write(
                f"- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write("---\n\n")

            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                f.write(f"### {role.upper()}\n\n")
                f.write(f"{content}\n\n")

        logger.info(f"会话已保存: {filepath}")
    except Exception as e:
        logger.error(f"保存会话失败: {e}")


def load_session(user_id: str, session_id: str) -> List[Dict[str, str]]:
    """加载会话内容

    Args:
        user_id: 用户ID
        session_id: 会话ID

    Returns:
        消息列表
    """
    filepath = get_session_file_path(user_id, session_id)

    if not os.path.exists(filepath):
        return []

    messages = []
    current_role = None
    current_content = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_header = True
        for line in lines:
            line = line.rstrip()

            if in_header:
                if line.startswith("### "):
                    in_header = False
                    role = line[4:].lower()
                    if role in ["user", "assistant", "system"]:
                        current_role = role
                        current_content = []
                continue

            if line.startswith("### "):
                if current_role and current_content:
                    messages.append(
                        {
                            "role": current_role,
                            "content": "\n".join(current_content).strip(),
                        }
                    )
                role = line[4:].lower()
                current_role = (
                    role if role in ["user", "assistant", "system"] else current_role
                )
                current_content = []
            elif line.strip():
                current_content.append(line)
            elif current_content and not line.strip():
                pass

        if current_role and current_content:
            messages.append(
                {"role": current_role, "content": "\n".join(current_content).strip()}
            )

    except Exception as e:
        logger.error(f"加载会话失败: {e}")

    return messages


def delete_session(user_id: str, session_id: str) -> bool:
    """删除会话文件

    Args:
        user_id: 用户ID
        session_id: 会话ID

    Returns:
        是否删除成功
    """
    filepath = get_session_file_path(user_id, session_id)

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"会话已删除: {filepath}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    return False


def create_new_session(user_id: str) -> str:
    """创建新会话

    Args:
        user_id: 用户ID

    Returns:
        新的会话ID
    """
    session_id = str(uuid.uuid4())[:8]
    save_session(user_id, session_id, [])
    return session_id


def get_memory_content(user_id: str) -> str:
    """获取用户长期记忆内容"""
    filepath = get_memory_file_path(user_id)

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取长期记忆失败: {e}")

    return ""


def save_memory(user_id: str, content: str, backup: bool = True):
    """保存长期记忆

    Args:
        user_id: 用户ID
        content: 记忆内容
        backup: 是否备份旧文件
    """
    filepath = get_memory_file_path(user_id)

    if backup and os.path.exists(filepath):
        archive_path = get_archive_file_path(user_id)
        try:
            import shutil

            shutil.copy(filepath, archive_path)
            logger.info(f"旧记忆已归档: {archive_path}")
        except Exception as e:
            logger.warning(f"归档失败: {e}")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"长期记忆已保存: {filepath}")
    except Exception as e:
        logger.error(f"保存长期记忆失败: {e}")


def list_daily_logs(user_id: str) -> List[Dict[str, str]]:
    """列出用户的所有会话日志（用于刷盘）"""
    ensure_dirs()
    logs = []

    if not os.path.exists(SESSIONS_DIR):
        return logs

    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".md") and filename.startswith(f"{user_id}_"):
            filepath = os.path.join(SESSIONS_DIR, filename)
            stat = os.stat(filepath)
            updated_at = datetime.fromtimestamp(stat.st_mtime)

            logs.append(
                {
                    "filename": filename,
                    "filepath": filepath,
                    "updated_at": updated_at,
                }
            )

    logs.sort(key=lambda x: x["updated_at"], reverse=True)
    return logs
