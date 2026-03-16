# 智扫通智能客服 Agent 项目文档

本文档详细介绍智扫通智能客服 Agent 的完整开发过程和核心技术点。

---

## 1. Agent 智能体介绍

### 什么是 Agent？

Agent（智能体）是一种基于大语言模型（LLM）的智能系统，能够：
- 理解用户意图
- 自主进行思考和推理
- 调用外部工具完成复杂任务
- 与用户进行多轮对话

### 本项目 Agent 特点

本项目使用 **LangChain** 和 **Deep Agents** 框架构建智能客服，具有以下特点：
- **ReAct 思考框架**：遵循"思考→行动→观察→再思考"的推理流程
- **工具调用能力**：可调用 RAG、天气查询、用户信息等多种工具
- **流式输出**：实时逐字返回回答，提升用户体验
- **中间件支持**：可在关键节点插入日志、监控、提示词切换等逻辑
- **多轮对话**：通过 checkpointer 保持会话上下文
- **长期记忆**：支持用户偏好和会话历史的持久化存储

---

## 2. Agent 智能体初体验

### 快速开始

```python
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询城市天气"""
    return f"{city}天气：晴天"

agent = create_agent(
    model=chat_model,
    tools=[get_weather],
    system_prompt="你是智能助手"
)

result = agent.invoke({"messages": [{"role": "user", "content": "深圳天气如何"}]})
```

### 核心组件

| 组件 | 作用 |
|------|------|
| `create_agent` | 创建 Agent 实例 |
| `model` | 大语言模型（GPT、通义千问等） |
| `tools` | Agent 可调用的工具列表 |
| `system_prompt` | 系统提示词，定义 Agent 行为 |
| `middleware` | 中间件，扩展 Agent 能力 |

---

## 3. Agent 的流式输出

### 流式输出的必要性

传统的同步调用需要等待模型完整生成后才返回结果，用户体验较差。流式输出可以逐字实时显示模型生成的内容。

### 实现方式

使用 LangChain 的 `stream` 方法配合 `stream_mode="values"`：

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "你好"}]},
    stream_mode="values"
):
    latest_message = chunk['messages'][-1]
    if latest_message.content:
        print(latest_message.content, end="", flush=True)
```

### 关键点说明

- **`stream_mode="values"`**：以"完整的消息步骤"为单位进行流式处理
- **逐字符输出**：在循环中逐字符 yield，实现打字机效果
- **消息过滤**：需要过滤掉用户消息，只输出 AI 回复

---

## 4. Agent 的 ReAct 行动框架

### 什么是 ReAct？

ReAct（Reasoning + Acting）是一种让 Agent 结合推理和行动的问题解决方法：

```
思考 (Thought) → 行动 (Action) → 观察 (Observation) → 再思考 (Reasoning)
```

### 本项目的 ReAct 实现

```python
system_prompt = """你是严格遵循ReAct框架的智能体，必须按「思考→行动→观察→再思考」的流程解决问题。
每轮仅能思考并调用1个工具，禁止单次调用多个工具。
并告知我你的思考过程，工具的调用原因，按思考、行动、观察三个结构告知我"""
```

### 执行流程

1. **分析需求**：判断是否需要调用工具
2. **选择工具**：根据需求选择合适的工具
3. **执行工具**：传入正确参数调用工具
4. **观察结果**：分析工具返回的信息
5. **再次判断**：决定是否需要继续调用工具

---

## 5. Agent 的 Middleware 中间件

### 中间件类型

LangChain Agent 提供多种中间件：

| 类型 | 说明 |
|------|------|
| `@before_agent` | Agent 执行前调用 |
| `@after_agent` | Agent 执行后调用 |
| `@before_model` | 模型调用前调用 |
| `@after_model` | 模型调用后调用 |
| `@wrap_tool_call` | 包装工具调用 |
| `@wrap_model_call` | 包装模型调用 |
| `@dynamic_prompt` | 动态生成提示词 |

### 本项目中间件实现

#### 1. 工具监控中间件 (`monitor_tool`)

```python
@wrap_tool_call
def monitor_tool(request, handler):
    logger.info(f"执行工具：{request.tool_call['name']}")
    logger.info(f"传入参数：{request.tool_call['args']}")
    result = handler(request)
    logger.info(f"工具调用成功")
    return result
```

#### 2. 模型调用前日志 (`log_before_model`)

```python
@before_model
def log_before_model(state, runtime):
    logger.info(f"即将调用模型，带有{len(state['messages'])}条消息")
```

#### 3. 动态提示词切换 (`report_prompt_switch`)

根据上下文标志自动切换提示词：

```python
@dynamic_prompt
def report_prompt_switch(request):
    if request.runtime.context.get("is_report"):
        return load_report_prompts()
    return load_system_prompts()
```

---

## 6. Agent 智能体项目介绍

### 项目概述

**智扫通智能客服**是一个基于 LangChain/Deep Agents 的扫地机器人智能客服系统。

### 技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| Python | 3.11+ | 编程语言 |
| LangChain | 1.2.x | Agent 框架 |
| LangGraph | 1.0.x | 图结构执行 |
| Deep Agents | 0.4.x | 高级 Agent 封装 |
| Chroma | 1.5.x | 向量数据库 |
| Streamlit | 1.54.x | Web 前端 |

### 项目目录结构

```
my_heima_agent/
├── agent/                    # Agent 核心模块
│   ├── react_deep_agent.py  # Deep Agent 实现
│   ├── tools/
│   │   ├── agent_tools.py   # 工具定义
│   │   └── middleware.py    # 中间件
│   └── skills/              # Agent 技能
├── model/                   # 模型配置
│   └── factory.py          # 模型工厂
├── utils/                   # 工具模块
│   ├── logger_handler.py   # 日志
│   ├── config_handler.py   # 配置加载
│   ├── prompt_loader.py    # 提示词加载
│   ├── path_tool.py        # 路径工具
│   ├── user_context.py     # 用户上下文
│   ├── weather_service.py  # 天气服务
│   └── memory_manager.py   # 会话记忆管理
├── rag/                    # RAG 相关
│   ├── vector_store.py     # 向量存储
│   └── rag_service.py      # RAG 服务
├── prompts/                # 提示词模板
│   ├── main_prompt.txt    # 主提示词
│   ├── IDENTITY.md        # 身份定义
│   ├── SOUL.md           # 服务人格
│   ├── AGENTS.md         # 操作指令
│   └── users/            # 用户画像
├── config/                 # 配置文件
├── memory/                 # 会话记忆存储
├── app.py                 # Streamlit 前端
└── main.py                # 入口文件
```

---

## 7. [Agent项目] 日志和路径工具开发

### 日志工具 (`logger_handler.py`)

使用 Python 标准库 `logging` 模块，实现双通道日志输出：

```python
def get_logger(name: str = "agent"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 文件 Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

**特性**：
- 单例模式：相同 name 返回同一 logger 对象
- 双通道输出：同时输出到控制台和文件
- 可配置级别：分别设置控制台和文件日志级别
- 自动创建目录：确保日志目录存在

### 路径工具 (`path_tool.py`)

处理项目中的路径问题，支持相对路径转绝对路径：

```python
def get_abs_path(relative_path: str) -> str:
    """将相对路径转换为绝对路径"""
    root_dir = Path(__file__).parent.parent
    return str(root_dir / relative_path)
```

---

## 8. [Agent项目] 配置文件和提示词加载工具

### 配置文件 (`config_handler.py`)

使用 YAML 格式管理配置：

```python
import yaml

def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

# 加载各模块配置
rag_conf = load_config("config/rag.yml")
chroma_conf = load_config("config/chroma.yml")
prompts_conf = load_config("config/prompts.yml")
agent_conf = load_config("config/agent.yml")
```

### 提示词加载 (`prompt_loader.py`)

支持多文件组合和用户画像动态加载：

```python
def load_system_prompts():
    # 读取主提示词
    parts = [open(main_prompt_path).read()]
    
    # 组合多个提示词文件
    for pf in ["IDENTITY.md", "SOUL.md", "AGENTS.md"]:
        parts.append(read_file(pf))
    
    return "\n".join(parts)

def load_user_prompt(user_id: str) -> str:
    """加载指定用户的画像"""
    path = f"prompts/users/USER_{user_id}.md"
    return read_file(path) if exists(path) else ""
```

---

## 9. [Agent项目] 向量存储服务开发

### 向量存储 (`vector_store.py`)

基于 Chroma 向量数据库实现文档向量化存储：

```python
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"],
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
        )
    
    def load_document(self):
        """加载文档到向量库"""
        # 1. 扫描数据目录
        # 2. 计算 MD5 去重
        # 3. 加载文件内容
        # 4. 文本分块
        # 5. 向量化入库
    
    def get_retriever(self):
        """获取检索器"""
        return self.vector_store.as_retriever(
            search_kwargs={"k": chroma_conf["k"]}
        )
```

### 核心特性

- **MD5 去重**：通过文件 MD5 避免重复入库
- **自动分块**：使用 RecursiveCharacterTextSplitter 智能分块
- **配置驱动**：所有参数从配置文件读取
- **持久化存储**：数据保存在本地硬盘

---

## 10. [Agent项目] RAG 总结服务开发

### RAG 服务 (`rag_service.py`)

实现检索增强生成的问答服务：

```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class RagSummarizeService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_template = PromptTemplate.from_template(
            load_rag_prompts()
        )
        self.chain = self.prompt_template | self.model | StrOutputParser()
    
    def rag_summarize(self, query: str) -> str:
        # 1. 检索相关文档
        docs = self.retriever.invoke(query)
        
        # 2. 组装上下文
        context = "\n".join([doc.page_content for doc in docs])
        
        # 3. 调用链生成回答
        return self.chain.invoke({
            "input": query,
            "context": context
        })
```

### RAG 流程

```
用户提问 → 向量检索 → 上下文组装 → LLM 生成 → 返回回答
```

---

## 11. [Agent项目] Tools 工具开发

### 工具定义方式

使用 `@tool` 装饰器定义工具：

```python
from langchain_core.tools import tool

@tool(description="获取指定城市的天气")
def get_weather(city: str) -> str:
    """获取城市天气信息"""
    return weather_service.get_weather(city)

@tool(description="获取用户ID")
def get_user_id() -> str:
    """获取当前用户ID"""
    return user_context.get_user_id()
```

### 本项目工具列表

| 工具名 | 功能 |
|--------|------|
| `rag_summarize` | RAG 知识库检索 |
| `get_weather` | 天气查询 |
| `get_user_location` | 获取用户位置 |
| `get_user_id` | 获取用户ID |
| `get_current_month` | 获取当前月份 |
| `fetch_external_data` | 获取外部使用数据 |
| `fill_context_for_report` | 报告生成上下文注入 |
| `terminal` | Shell 命令执行 |
| `read_file` | 文件读取 |
| `fetch_url` | URL 内容获取 |
| `python_repl` | Python 代码执行 |

### 第三方 LangChain 工具

```python
# Shell 命令工具
from langchain_community.tools import ShellTool
terminal = ShellTool()

# 文件读取工具
from langchain_community.tools.file_management import ReadFileTool
read_file = ReadFileTool(root_dir=PROJECT_ROOT)

# Python 执行工具
from langchain_experimental.tools import PythonREPLTool
python_repl = PythonREPLTool()
```

---

## 12. [Agent项目] 中间件和 Agent 创建

### 中间件开发

#### 工具监控中间件

```python
@wrap_tool_call
def monitor_tool(request, handler):
    logger.info(f"执行工具：{request.tool_call['name']}")
    logger.info(f"传入参数：{request.tool_call['args']}")
    
    result = handler(request)
    
    logger.info(f"工具{request.tool_call['name']}调用成功")
    
    # 特殊工具处理
    if request.tool_call["name"] == "fill_context_for_report":
        if hasattr(request, "state"):
            request.state["is_report"] = True
    
    return result
```

#### 模型调用前日志

```python
@before_model
def log_before_model(state, runtime):
    logger.info(f"即将调用模型，带有{len(state['messages'])}条消息")
```

### Agent 创建

使用 `create_deep_agent` 创建完整的 Agent：

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_deep_agent(
    model=chat_model,
    system_prompt=load_system_prompts(),
    tools=[
        rag_summarize,
        get_weather,
        get_user_id,
        get_user_location,
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
```

### Agent 执行

```python
# 流式输出
for chunk in agent.execute_stream(query="你好", thread_id="user-123"):
    print(chunk, end="", flush=True)

# 同步调用
result = agent.invoke(
    {"messages": [{"role": "user", "content": "查询天气"}]},
    config={"configurable": {"thread_id": "user-123"}}
)
```

---

## 附录

### 配置文件示例

**config/rag.yml**
```yaml
embedding_model_name: your-embedding-model
chunk_size: 500
chunk_overlap: 50
```

**config/chroma.yml**
```yaml
collection_name: rag-chroma
persist_directory: chroma_db
data_path: data
k: 3
```

**config/prompts.yml**
```yaml
main_prompt_path: prompts/main_prompt.txt
rag_summarize_prompt_path: prompts/rag_summarize.txt
report_prompt_path: prompts/report_prompt.txt
user_prompts_dir: prompts/users
```

### 依赖安装

```bash
uv sync
# 或
pip install -e .
```
