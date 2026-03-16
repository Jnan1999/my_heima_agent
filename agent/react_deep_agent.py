"""
Deep Agent 实现模块

本模块使用 deepagents 框架创建智能客服 Agent，具备以下核心功能：
1. ReAct 思考链：模拟人类的思考→行动→观察→再思考流程
2. 工具调用：集成了 RAG 检索、天气查询、用户信息获取、报告生成等工具
3. 技能加载：支持 ask-user-question skill，主动向用户提问获取完整需求
4. 多轮对话：通过 checkpointer 自动保存和加载对话历史
5. 动态提示词：根据上下文自动切换普通对话/报告生成模式

依赖：
    - deepagents: Agent 框架
    - langgraph.checkpoint: 对话历史持久化
    - langchain_core.messages: 消息类型定义
"""

from typing import Any, Generator, Optional

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from agent.tools.agent_tools import (
    fetch_external_data,
    fill_context_for_report,
    get_current_month,
    get_user_id,
    get_user_location,
    get_weather,
    # 基础内置工具
    rag_summarize,
    terminal,
    read_file,
    fetch_url,
    python_repl,
)
from agent.tools.middleware import (
    log_before_model,
    monitor_tool,
    report_prompt_switch,
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts


class ReactDeepAgent:
    """基于 Deep Agents 框架的智能客服 Agent 类

    该类封装了 Agent 的创建和执行逻辑：
    - 初始化时创建 deep agent 实例，配置工具、中间件、技能和检查点
    - 提供流式执行（execute_stream）和同步执行（invoke）两种调用方式
    - 通过 thread_id 区分不同用户的对话会话

    Attributes:
        agent: deepagents 创建的 Agent 实例，支持 stream/invoke 方法

    Example:
        agent = ReactDeepAgent()

        # 流式输出
        for chunk in agent.execute_stream("我的机器人有问题", thread_id="user-123"):
            print(chunk, end="")

        # 同步调用
        result = agent.invoke("生成我的使用报告", thread_id="user-123")
    """

    def __init__(self):
        """初始化 Agent 实例

        创建过程：
        1. 创建 MemorySaver 作为 checkpointer，用于保存对话历史
        2. 配置模型、工具、中间件、技能等
        3. 返回配置好的 agent 实例
        """
        checkpointer = MemorySaver()

        # 获取聊天模型，确保类型正确
        model: Optional[BaseChatModel] = chat_model
        if model is None:
            raise ValueError("聊天模型初始化失败，请检查 model factory 配置")

        self.agent = create_deep_agent(
            model=model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize,
                get_weather,
                get_user_location,
                get_user_id,
                get_current_month,
                fetch_external_data,
                fill_context_for_report,
                terminal,
                read_file,
                fetch_url,
                python_repl,
            ],
            middleware=[
                monitor_tool,
                log_before_model,
                report_prompt_switch,
            ],
            backend=FilesystemBackend(
                root_dir=".",
                virtual_mode=True,
            ),
            skills=[
                "./agent/skills/ask-user-question/",
                "./agent/skills/memory-brush/",
            ],
            checkpointer=checkpointer,
        )

    def execute_stream(
        self, query: str, thread_id: str = "default"
    ) -> Generator[str, None, None]:
        """流式执行 Agent，返回生成器逐步输出结果

        该方法是异步流式输出，适用于需要实时显示 Agent 回复的场景。
        每次调用只需传入当前用户的消息，checkpointer 会自动加载历史对话。

        Args:
            query: str，用户输入的查询字符串
                例如："我的机器人清理不干净地面，怎么解决"
            thread_id: str，线程 ID，用于标识不同的对话会话
                同一个 thread_id 会共享对话历史
                默认值："default"

        Yields:
            str，逐步输出的回复内容片段
            每个片段是完整的句子或段落，以换行符结尾

        Example:
            agent = ReactDeepAgent()
            for chunk in agent.execute_stream("你好", thread_id="user-001"):
                print(chunk, end="", flush=True)
        """
        input_dict: dict[str, Any] = {"messages": [{"role": "user", "content": query}]}

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        for chunk in self.agent.stream(input_dict, config=config, stream_mode="values"):
            messages = chunk.get("messages", [])
            if not messages:
                continue
            latest_message = messages[-1]
            if hasattr(latest_message, "type") and latest_message.type == "human":
                continue
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

    def invoke(self, query: str, thread_id: str = "default") -> dict[str, Any]:
        """同步执行 Agent，等待完整结果返回

        该方法是阻塞式执行，适用于需要等待完整回复后再处理的场景。

        Args:
            query: str，用户输入的查询字符串
            thread_id: str，线程 ID，用于标识不同的对话会话
                默认值："default"

        Returns:
            dict，Agent 的执行结果
            包含完整的消息列表和其他状态信息

        Example:
            agent = ReactDeepAgent()
            result = agent.invoke("生成我的使用报告", thread_id="user-001")
            print(result["messages"])
        """
        input_dict: dict[str, Any] = {"messages": [{"role": "user", "content": query}]}

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        result = self.agent.invoke(input_dict, config=config)
        return result


if __name__ == "__main__":
    agent = ReactDeepAgent()

    # print("=" * 50)
    # print("测试问题：我的机器人清理不干净地面，怎么解决")
    # print("=" * 50)

    for chunk in agent.execute_stream("输出我的id，读取文件并输出我在2月的使用记录"):
        print(chunk, end="", flush=True)
