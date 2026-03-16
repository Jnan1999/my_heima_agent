"""
ReAct Agent 服务模块 (react_agent.py)
=======================================
文件作用：
    基于 LangChain 框架实现的 ReAct（Reasoning + Acting）智能体封装。
    该模块负责将大语言模型、自定义工具、中间件组装成完整的 Agent，
    并提供流式输出接口，支持用户查询的实时响应。

核心功能：
    1. 初始化 ReAct Agent，绑定模型、工具和中间件
    2. 提供流式执行方法 `execute_stream`，实现实时对话
    3. 支持上下文标记（如 report 标记），用于提示词动态切换

依赖说明：
    - langchain.agents: LangChain Agent 创建工具
    - model.factory: 自定义聊天模型工厂
    - utils.prompt_loader: 自定义提示词加载工具
    - agent.tools.agent_tools: 自定义 Agent 工具集
    - agent.tools.middleware: 自定义 Agent 中间件
"""

# 导入 LangChain 提供的 Agent 创建函数
from langchain.agents import create_agent
# 导入自定义工厂模块中初始化好的聊天模型实例（如 ChatTongyi）
from model.factory import chat_model
# 导入自定义提示词加载工具，用于读取系统提示词
from utils.prompt_loader import load_system_prompts
# 导入自定义 Agent 工具集（所有工具函数，如 RAG 总结、天气查询等）
from agent.tools.agent_tools import *
# 导入自定义中间件（用于工具监控、模型调用前日志、提示词切换等）
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch


class ReactAgent:
    """
    ReAct 智能体封装类
    
    该类封装了 LangChain ReAct Agent 的初始化与执行逻辑，
    提供统一的接口供上层调用，支持流式输出和上下文控制。
    """
    
    def __init__(self):
        """
        初始化 ReAct Agent
        
        核心步骤：
            1. 加载聊天模型
            2. 加载系统提示词
            3. 绑定自定义工具集
            4. 绑定自定义中间件
            5. 调用 LangChain 的 create_agent 完成组装
        """
        # 调用 LangChain 的 create_agent 函数创建 ReAct Agent
        self.agent = create_agent(
            # 指定使用的大语言模型
            model=chat_model,
            # 加载并指定系统提示词（定义 Agent 的人设、行为规范等）
            system_prompt=load_system_prompts(),
            # 绑定 Agent 可调用的工具列表
            tools=[
                rag_summarize,          # RAG 知识库总结工具
                get_weather,            # 天气查询工具
                get_user_location,      # 用户位置获取工具
                get_user_id,            # 用户 ID 获取工具
                get_current_month,      # 当前月份获取工具
                fetch_external_data,    # 外部数据拉取工具
                fill_context_for_report # 报告上下文填充工具
            ],
            # 绑定中间件列表（在工具调用、模型调用前后执行）
            middleware=[
                monitor_tool,           # 工具调用监控中间件
                log_before_model,       # 模型调用前日志记录中间件
                report_prompt_switch    # 报告场景提示词切换中间件
            ],
        )

    def execute_stream(self, query: str):
        """
        流式执行用户查询
        
        作用：
            接收用户的自然语言查询，通过 Agent 进行推理和工具调用，
            并以流式方式返回生成的内容，实现实时对话体验。
        
        参数:
            query (str): 用户的自然语言查询字符串，例如 "给我生成我的使用报告"
        
        返回:
            Generator[str, None, None]: 生成器，逐段返回 Agent 的回复内容（字符串）
        """
        # 构建 Agent 的输入字典，符合 LangChain 的消息格式
        input_dict = {
            "messages": [
                # 封装用户查询为标准消息格式
                {"role": "user", "content": query},
            ]
        }

        # 调用 Agent 的 stream 方法进行流式执行
        # 参数说明：
        #   input_dict: 包含用户消息的输入字典
        #   stream_mode="values": 流式输出模式，返回完整的状态值
        #   context={"report": False}: 上下文运行时信息，用于提示词切换的标记
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            # 从流式返回的 chunk 中提取最新的一条消息
            latest_message = chunk["messages"][-1]
            # 仅当消息有内容时才返回（过滤空内容）
            if latest_message.content:
                # 去除内容首尾空白并添加换行，通过生成器逐段返回
                yield latest_message.content.strip() + "\n"


if __name__ == '__main__':
    """
    模块测试入口
    
    当直接运行该文件时，执行以下测试逻辑：
        1. 实例化 ReactAgent
        2. 调用 execute_stream 方法测试流式输出
        3. 逐段打印生成的内容
    """
    # 实例化 ReAct Agent
    agent = ReactAgent()

    # 调用流式执行方法，传入测试查询
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        # 逐段打印生成的内容，end="" 避免额外换行，flush=True 确保实时输出
        print(chunk, end="", flush=True)