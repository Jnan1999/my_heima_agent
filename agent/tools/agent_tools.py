"""
Agent 工具集模块

本模块定义了一系列供 LangChain Agent 使用的工具函数，涵盖以下功能：
1. RAG 知识库检索
2. 天气信息查询（模拟）
3. 用户上下文信息获取（模拟）
4. 外部业务数据加载与查询
5. 报告生成上下文注入钩子
"""

import os
import json
from pydantic import BaseModel, Field
from utils.logger_handler import logger
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from utils.user_context import get_user_context
from utils.weather_service import get_weather_service

import requests
from langchain_community.tools import ShellTool
from langchain_community.tools.file_management import ReadFileTool
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool
from bs4 import BeautifulSoup

rag = RagSummarizeService()
user_context = get_user_context()
weather_service = get_weather_service()

user_ids = [
    "1001",
    "1002",
    "1003",
    "1004",
    "1005",
    "1006",
    "1007",
    "1008",
    "1009",
    "1010",
]
month_arr = [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
]

external_data = {}


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


# class WeatherInput(BaseModel):
#     """查询天气的输入参数"""
#     city: str = Field(description="要查询的城市名称，例如 '北京'、'上海'")
#     is_forecast: bool = Field(default=False, description="True为查询预报，False为查询实时")
# @tool(args_schema=WeatherInput)
# def search_weather(city: str, is_forecast: bool) -> str:
#     """查询指定城市的实时天气或天气预报。"""
#     return f"{city}的天气是晴天，温度25度。"


@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    """获取指定城市的天气信息

    Args:
        city: 城市名称，如 '深圳'、'杭州'、'北京'

    Returns:
        天气信息字符串，包含温度、湿度、风向、风力等
    """
    if not city:
        user_location = user_context.get_user_location()
        if user_location:
            city = (
                user_location.split("-")[1]
                if len(user_location.split("-")) > 1
                else user_location
            )
        else:
            return "无法获取天气信息：请提供城市名称或先在侧边栏填写用户地址"

    weather_data = weather_service.get_weather(city)
    return weather_service.format_weather_message(weather_data)


@tool(description="获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location() -> str:
    """获取用户所在城市的名称

    Returns:
        用户地址，格式为 '省份-城市-区县'
    """
    location = user_context.get_user_location()
    if not location:
        return random.choice(["深圳", "合肥", "杭州"])
    return location


@tool(description="获取用户的ID，以纯字符串形式返回")
def get_user_id() -> str:
    """获取用户的ID

    Returns:
        用户ID字符串
    """
    user_id = user_context.get_user_id()
    if not user_id:
        return random.choice(user_ids)
    return user_id


@tool(description="获取当前月份，以纯字符串形式返回")
def get_current_month() -> str:
    """获取当前月份

    Returns:
        当前月份，格式为 'YYYY-MM'
    """
    return user_context.get_current_month()


def generate_external_data():
    """
    最终目的是获取如下格式的数据，检索user_id，然后再检索month
    {
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        ...
    }
    :return:
    """
    # 惰性加载：如果数据已存在则不重复加载
    if not external_data:
        # 从配置中获取文件绝对路径
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        # 解析 CSV 文件
        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:  # 第一行为表头，跳过
                arr: list[str] = line.strip().split(",")

                # 清洗数据（去除 CSV 文件中的引号）
                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                # 构建嵌套字典结构，说明Key为“user_id”的数据第一次向external_data字典中添加
                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }


@tool(
    description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回， 如果未检索到返回空字符串"
)
def fetch_external_data(user_id: str, month: str) -> str:
    # 先加载数据
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(
            f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据"
        )
        return ""


@tool(
    description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息"
)
def fill_context_for_report():
    return "fill_context_for_report已调用"


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

terminal = ShellTool()

read_file = ReadFileTool(root_dir=PROJECT_ROOT)


class CleanedRequestsGetTool(BaseTool):
    """清洗后的URL获取工具，用于获取网页内容并转换为Markdown格式"""

    name: str = "fetch_url"
    description: str = "获取指定URL的网页内容，返回清洗后的Markdown文本"

    def _run(self, url: str) -> str:
        """获取并清洗网页内容

        Args:
            url: 要获取的URL地址

        Returns:
            清洗后的文本内容
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.text
            if not result:
                return "未能获取到网页内容"

            soup = BeautifulSoup(result, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            if len(text) > 8000:
                text = text[:8000] + "\n\n[内容已截断...]"

            return text
        except Exception as e:
            return f"获取网页内容失败: {str(e)}"


fetch_url = CleanedRequestsGetTool()


python_repl = PythonREPLTool()


__all__ = [
    "rag_summarize",
    "get_weather",
    "get_user_location",
    "get_user_id",
    "get_current_month",
    "fetch_external_data",
    "fill_context_for_report",
    "terminal",
    "read_file",
    "fetch_url",
    "python_repl",
]

if __name__ == "__main__":
    print("工具名称:", get_weather.name)
    # print("工具描述:", search_weather.description)
    # print(json.dumps(get_weather.args_schema.model_json_schema(), indent=2, ensure_ascii=False))
    # formatted_tool = convert_to_openai_tool(search_weather)
    # print(json.dumps(formatted_tool, indent=2, ensure_ascii=False))
