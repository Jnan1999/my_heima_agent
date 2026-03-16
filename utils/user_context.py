"""
用户上下文信息存储模块

用于在 Streamlit 前端和 Agent 工具之间共享用户信息：
- 用户ID
- 用户地址（省份-市-县）
- 当前会话状态
"""

from typing import Optional
from datetime import datetime


class UserContext:
    """用户上下文信息类"""

    def __init__(self):
        self.user_id: Optional[str] = None
        self.province: Optional[str] = None
        self.city: Optional[str] = None
        self.district: Optional[str] = None
        self.address: Optional[str] = None
        self.is_confirmed: bool = False

    def set_user_info(self, user_id: str, province: str, city: str, district: str):
        """设置用户信息"""
        self.user_id = user_id
        self.province = province
        self.city = city
        self.district = district
        self.address = (
            f"{province}-{city}-{district}" if district else f"{province}-{city}"
        )
        self.is_confirmed = True

    def get_user_id(self) -> str:
        """获取用户ID"""
        return self.user_id or ""

    def get_user_location(self) -> str:
        """获取用户位置"""
        return self.address or ""

    def get_current_month(self) -> str:
        """获取当前月份"""
        return datetime.now().strftime("%Y-%m")

    def clear(self):
        """清除用户信息"""
        self.user_id = None
        self.province = None
        self.city = None
        self.district = None
        self.address = None
        self.is_confirmed = False


user_context = UserContext()


def get_user_context() -> UserContext:
    """获取全局用户上下文实例"""
    return user_context
