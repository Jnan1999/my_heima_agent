# AGENTS.md - Agent 代码指南

本文档为在项目中工作的 AI Agent 提供编码指南和项目规范。

## 1. 项目概述

- **Python 版本**: 3.11+
- **主要框架**: LangChain 1.2、LangGraph、Pydantic
- **依赖管理**: uv + pyproject.toml
- **虚拟环境**: .venv

## 2. 命令

### 2.1 安装依赖

```bash
# 使用 uv 安装项目依赖
uv sync

# 或使用 pip 安装 editable 模式
uv pip install -e .
```

### 2.2 运行项目

```bash
# 运行主程序
python main.py

# 运行 Web 应用（如果存在）
python app.py
```

### 2.3 虚拟环境激活

```bash
# 激活虚拟环境
source .venv/bin/activate
```

## 3. 代码风格

### 3.1 命名规范

- **函数/变量**: snake_case（如 `get_weather`, `user_name`）
- **类名**: PascalCase（如 `ReactAgent`, `ChatModelFactory`）
- **常量**: UPPER_SNAKE_CASE（如 `MAX_RETRIES`, `DEFAULT_TIMEOUT`）
- **文件命名**: snake_case（如 `agent_tools.py`, `config_handler.py`）

### 3.2 导入顺序

遵循以下顺序，组内按字母排序：

```python
# 1. 标准库
import os
import json
from typing import Dict, List, Optional

# 2. 第三方库
from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 3. 本地模块
from model.factory import chat_model
from utils.logger_handler import logger
from agent.tools.middleware import monitor_tool
```

### 3.3 类型提示

- 所有函数参数和返回值应添加类型注解
- 使用 `Optional` 而 `| None` 取决于项目风格一致性
- 复杂类型使用 `typing` 模块

```python
# 推荐
def get_user_info(user_id: str) -> Optional[Dict[str, str]]:
    pass

def process_items(items: List[int]) -> Dict[str, int]:
    pass
```

### 3.4 文档字符串

- 所有公开函数和类需要 docstring
- 使用中文编写（与现有代码保持一致）
- 采用 Google 风格或简洁描述

```python
def calculate_sum(a: int, b: int) -> int:
    """计算两个整数之和。
    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        两个整数的和
    """
    return a + b
```

### 3.5 注释规范

- 使用中文注释（与现有代码风格一致）
- 关键逻辑处添加注释说明
- 避免冗余注释

```python
# 正确：说明为什么要这样做
# 调用原工具函数，获取执行结果
result = handler(request)

# 错误：只是重复代码内容
# 调用 handler 函数
result = handler(request)
```

### 3.6 异常处理

- 使用 try-except 捕获异常
- 记录日志后根据需要重新抛出异常
- 不捕获过于宽泛的异常

```python
try:
    result = handler(request)
    logger.info(f"工具调用成功: {tool_name}")
except Exception as e:
    logger.error(f"工具调用失败: {str(e)}")
    raise e  # 重新抛出，让调用者感知到错误
```

### 3.7 日志记录

- 使用 `utils.logger_handler` 模块获取日志器
- 不同级别使用不同方法：
  - `logger.debug()`: 调试信息
  - `logger.info()`: 一般信息
  - `logger.warning()`: 警告信息
  - `logger.error()`: 错误信息

```python
from utils.logger_handler import logger

logger.info("开始执行任务")
logger.error(f"发生错误: {error_message}")
```

## 4. 关键模式

### 4.1 Agent 创建

使用 LangChain 的 `create_agent()` 方法创建 Agent：

```python
from langchain.agents import create_agent

agent = create_agent(
    model=chat_model,
    system_prompt="你是一个有帮助的助手",
    tools=[tool1, tool2],
    middleware=[middleware1, middleware2],
)
```

### 4.2 工具定义

使用 `@tool` 装饰器定义工具：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。
    
    Args:
        city: 城市名称
    
    Returns:
        天气信息字符串
    """
    # 工具逻辑
    return f"{city} 的天气是晴天"
```

### 4.3 中间件模式

项目中使用以下中间件装饰器：

- `@wrap_tool_call`: 工具调用拦截，用于监控和修改工具行为
- `@before_model`: 模型调用前执行，常用于日志记录
- `@dynamic_prompt`: 动态生成提示词

```python
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt

@wrap_tool_call
def monitor_tool(request, handler):
    """监控工具调用"""
    # 前置逻辑
    result = handler(request)
    # 后置逻辑
    return result

@before_model
def log_before_model(state, runtime):
    """模型调用前日志"""
    logger.info(f"消息数量: {len(state['messages'])}")

@dynamic_prompt
def switch_prompt(request):
    """动态切换提示词"""
    return system_prompt
```

### 4.4 配置管理

- 配置文件位于 `config/` 目录
- 使用 YAML 格式
- 通过 `utils.config_handler` 模块加载

```python
from utils.config_handler import rag_conf, agent_conf

# 读取配置
model_name = rag_conf["chat_model_name"]
```

## 5. 第三方包源码读取

### 5.1 包路径说明

当需要阅读 LangChain、LangGraph 等第三方包的源码时，应读取 `.venv` 虚拟环境中的代码，而非系统级安装的包。

### 5.2 常用包路径

```
.venv/lib/python3.11/site-packages/
```

具体路径：

| 包名 | 路径 |
|------|------|
| langchain_core | .venv/lib/python3.11/site-packages/langchain_core/ |
| langchain | .venv/lib/python3.11/site-packages/langchain/ |
| langgraph | .venv/lib/python3.11/site-packages/langgraph/ |
| langchain_community | .venv/lib/python3.11/site-packages/langchain_community/ |
| langchain_anthropic | .venv/lib/python3.11/site-packages/langchain_anthropic/ |
| langchain_openai | .venv/lib/python3.11/site-packages/langchain_openai/ |

### 5.3 常用源码文件位置

- **@tool 装饰器**: `langchain_core/tools/convert.py`
- **BaseTool 类**: `langchain_core/tools/base.py`
- **StructuredTool**: `langchain_core/tools/structured.py`
- **convert_to_openai_tool**: `langchain_core/utils/function_calling.py`
- **create_agent**: `langchain/agents/__init__.py` 或 `langchain/agents/lc_agent.py`
- **LangGraph StateGraph**: `langgraph/graph/state.py`

## 6. 目录结构

```
my_heima_agent/
├── agent/                    # Agent 核心模块
│   ├── react_agent.py       # Agent 实现
│   └── tools/               # 工具定义
│       ├── agent_tools.py   # 工具函数
│       └── middleware.py   # 中间件
├── model/                   # 模型配置
│   └── factory.py          # 模型工厂
├── utils/                   # 工具模块
│   ├── logger_handler.py   # 日志
│   ├── config_handler.py   # 配置加载
│   ├── prompt_loader.py    # 提示词加载
│   └── path_tool.py        # 路径工具
├── rag/                    # RAG 相关
├── config/                 # 配置文件
├── prompts/                # 提示词模板
├── data/                   # 数据文件
├── chroma_db/              # Chroma 向量数据库
├── logs/                   # 日志输出
└── .venv/                  # 虚拟环境
```

## 7. 开发注意事项

### 7.1 避免的操作

- 不要在代码中硬编码敏感信息（如 API Key），使用环境变量或配置文件
- 不要使用 `from module import *`，明确导入需要的符号
- 不要忽略类型提示

### 7.2 推荐的做法

- 使用 Pydantic 进行数据验证
- 使用 `Optional` 处理可能为 None 的值
- 在修改公共接口时添加文档说明
- 保持函数职责单一

## 8. 调试技巧

### 8.1 查看 LangChain 源码

当遇到不确定的行为时，可以阅读第三方包源码进行排查：

```bash
# 查看 langchain_core tools 模块
cat .venv/lib/python3.11/site-packages/langchain_core/tools/convert.py
```

### 8.2 启用 LangSmith 追踪

```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
```

---

本指南会随着项目发展持续更新。
