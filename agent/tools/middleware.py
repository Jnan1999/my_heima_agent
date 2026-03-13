"""
Agent 中间件核心模块

本模块是 LangChain/LangGraph Agent 的执行层中间件集合，负责在 Agent 运行的各个关键节点插入横切逻辑。
主要实现三大核心功能：
1. **工具调用监控** (`monitor_tool`): 拦截所有工具执行，记录日志并处理特殊工具的上下文标记
2. **模型调用前日志** (`log_before_model`): 在 LLM 推理前记录对话状态
3. **动态提示词切换** (`report_prompt_switch`): 根据上下文标志在“通用对话”和“报告生成”两套提示词间自动切换
"""

from typing import Callable
from utils.prompt_loader import load_system_prompts, load_report_prompts
from langchain.agents import AgentState
from langchain.agents.middleware import (
    wrap_tool_call,
    before_model,
    dynamic_prompt,
    ModelRequest,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger


@wrap_tool_call
def monitor_tool(
    # 请求的数据封装
    request: ToolCallRequest,
    # 执行的函数本身
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:  # 工具执行的监控
    """
    【工具调用监控中间件】

    功能说明：
    作为所有 Agent 工具的“包装器”，在工具执行前后插入日志记录逻辑，并能针对特定工具进行上下文标记。

    执行流程：
    1. 记录工具名称和入参 -> 2. 调用原工具函数 -> 3. 记录执行结果/异常 -> 4. (特殊工具)设置上下文标志

    Args:
        request: ToolCallRequest 对象，包含本次工具调用的完整元数据
            - request.tool_call: 字典，包含 'name' (工具名) 和 'args' (参数字典)
            - request.runtime: LangGraph Runtime 对象，可访问 context (上下文字典)

        handler: Callable，被装饰的“原工具执行函数”
            - 输入：ToolCallRequest
            - 输出：ToolMessage (工具执行结果) 或 Command (图流转指令)

    Returns:
        ToolMessage | Command: 原工具函数的返回值，不做修改直接透传

    Raises:
        Exception: 若原工具执行抛出异常，记录错误日志后**重新抛出**，不改变原有错误流
    """
    # 记录 INFO 级别日志：工具名称
    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")
    # 记录 INFO 级别日志：工具入参（注意：生产环境若含敏感数据需脱敏）
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")

    try:
        # 【核心】调用被包装的原工具函数，获取执行结果
        result = handler(request)
        # 记录 INFO 级别日志：工具调用成功
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

        # 【特殊逻辑】若调用的是 "fill_context_for_report" 工具
        # 在 state 中设置 "is_report" 标志位，供后续动态提示词中间件使用
        # （方案一：使用 state 替代 runtime.context，解决 deep agents 中 context 为 None 的问题）
        if request.tool_call["name"] == "fill_context_for_report":
            # 尝试写入 state（适用于 LangChain 和 Deep Agents）
            if hasattr(request, "state") and isinstance(request.state, dict):
                request.state["is_report"] = True
            # 备用方案：写入 runtime.context（适用于传统 LangChain Agent）
            # if request.runtime is not None and request.runtime.context is not None:
            #     request.runtime.context["report"] = True

        # 透传原工具的返回结果
        return result
    except Exception as e:
        # 捕获所有异常，记录 ERROR 级别日志（包含工具名和错误原因）
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        # 重新抛出异常，确保 Agent 能感知到工具执行失败
        raise e


@before_model
def log_before_model(
    state: AgentState,  # 整个Agent智能体中的状态记录
    runtime: Runtime,  # 记录了整个执行过程中的上下文信息
):  # 在模型执行前输出日志
    """
    【模型调用前日志中间件】

    功能说明：
    在 LLM（大语言模型）每次被调用前执行，用于记录当前 Agent 的内部状态，便于调试和问题追踪。

    Args:
        state: AgentState 对象，LangChain Agent 的核心状态字典
            - state['messages']: 列表，包含完整的对话历史消息
              (消息类型可能是 HumanMessage, AIMessage, ToolMessage 等)

        runtime: Runtime 对象，LangGraph 的运行时上下文
            - 包含配置信息、图状态、自定义 context 等（本函数未直接使用，但为中间件签名要求）

    Returns:
        None: 该中间件仅用于观察，不修改 state 或 runtime，也不返回任何值
    """
    # 记录 INFO 级别日志：当前对话历史的消息总数
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")

    # 记录 DEBUG 级别日志：最后一条消息的类型和内容（仅在调试模式下可见）
    # type(...).__name__: 获取消息类名（如 "HumanMessage"）
    # .strip(): 去除内容首尾空白
    logger.debug(
        f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}"
    )

    # 显式返回 None（符合中间件“无操作”的语义）
    return None


@dynamic_prompt  # 每一次在生成提示词之前，调用此函数
def report_prompt_switch(request: ModelRequest):  # 动态切换提示词
    """
    【动态提示词切换中间件】

    功能说明：
    在每次构建 LLM 请求时动态决定使用哪套系统提示词（System Prompt）。
    基于 `runtime.context` 中的 "report" 标志位进行判断：
    - 标志位为 True：使用“报告生成”提示词
    - 标志位为 False/不存在：使用默认“系统”提示词

    Args:
        request: ModelRequest 对象，包含即将发送给 LLM 的请求数据
            - request.runtime: Runtime 对象，可通过 .context 获取之前设置的标志位
            - request.messages: 列表，当前的消息列表（本函数未直接修改）

    Returns:
        Prompt | str: 返回加载后的提示词对象（或字符串）
            - 该返回值会替换掉 Agent 原有的系统提示词
    """
    # 获取报告模式标志位
    # （方案一：优先从 state 获取，解决 deep agents 中 context 为 None 的问题）
    is_report = False

    # 方案一：优先从 state 获取（适用于 LangChain 和 Deep Agents）
    if hasattr(request, "state") and isinstance(request.state, dict):
        is_report = request.state.get("is_report", False)

    # 备用方案：从 runtime.context 获取（适用于传统 LangChain Agent）
    # runtime_context = {}
    # if request.runtime is not None and hasattr(request.runtime, "context"):
    #     runtime_context = request.runtime.context or {}
    # is_report = runtime_context.get("report", False)

    if is_report:  # 是报告生成场景，返回报告生成提示词内容
        # 调用工具函数加载报告生成专用的提示词
        return load_report_prompts()

    # 非报告生成场景，返回默认的系统提示词
    return load_system_prompts()
