"""
Deep Agent 实现模块

使用 deepagents 框架创建的 Agent，集成 ask-user-question skill 用于主动向用户提问。
"""

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (
    rag_summarize,
    get_weather,
    get_user_location,
    get_user_id,
    get_current_month,
    fetch_external_data,
    fill_context_for_report,
)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactDeepAgent:
    """基于 Deep Agents 框架的 Agent 实现"""

    def __init__(self):
        self.agent = create_deep_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize,
                get_weather,
                get_user_location,
                get_user_id,
                get_current_month,
                fetch_external_data,
                fill_context_for_report,
            ],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
            backend=FilesystemBackend(
                root_dir=".",
                virtual_mode=True,
            ),
            skills=["./agent/skills/ask-user-question/"],
        )

    def execute_stream(self, query: str, thread_id: str = "default"):
        """流式执行 Agent

        Args:
            query: 用户输入的查询
            thread_id: 线程 ID，用于保持对话上下文
        """
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        config = {"configurable": {"thread_id": thread_id}}

        for chunk in self.agent.stream(input_dict, config=config, stream_mode="values"):
            messages = chunk.get("messages", [])
            if messages:
                latest_message = messages[-1]
                if hasattr(latest_message, "content") and latest_message.content:
                    yield latest_message.content.strip() + "\n"

    def invoke(self, query: str, thread_id: str = "default"):
        """同步执行 Agent

        Args:
            query: 用户输入的查询
            thread_id: 线程 ID，用于保持对话上下文

        Returns:
            Agent 执行结果
        """
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        config = {"configurable": {"thread_id": thread_id}}

        result = self.agent.invoke(input_dict, config=config)
        return result


if __name__ == "__main__":
    agent = ReactDeepAgent()

    for chunk in agent.execute_stream("我的机器人清理不干净地面，怎么解决"):
        print(chunk, end="", flush=True)
