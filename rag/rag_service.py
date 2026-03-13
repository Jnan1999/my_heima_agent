"""
总结服务模块 (rag_summarize.py)
==================================
文件作用：
    实现基于检索增强生成 (RAG, Retrieval-Augmented Generation) 的问答服务。
    核心流程：
        1. 接收用户的自然语言提问 (Query)
        2. 在向量数据库中检索与问题相关的参考资料 (Context)
        3. 将 "提问 + 参考资料" 组装成 Prompt
        4. 提交给大语言模型 (LLM)，让模型基于参考资料进行总结并回复

主要组件：
    - RagSummarizeService: RAG 服务的主类
"""

# 导入 LangChain 核心文档对象，用于封装检索到的文本片段
from langchain_core.documents import Document
# 导入 LangChain 字符串输出解析器，用于将模型的输出（通常是 AIMessage）转换为纯字符串
from langchain_core.output_parsers import StrOutputParser
# 导入自定义的向量存储服务类（即上一个文件中定义的 VectorStoreService）
from rag.vector_store import VectorStoreService
# 导入自定义的提示词加载工具，用于从文件或配置中读取 RAG 提示词模板
from utils.prompt_loader import load_rag_prompts
# 导入 LangChain 提示词模板类，用于动态填充变量（如用户问题、参考资料）
from langchain_core.prompts import PromptTemplate
# 导入在 factory.py 中创建好的聊天模型实例 (如 ChatTongyi)
from model.factory import chat_model


def print_prompt(prompt):
    """
    【调试工具函数】打印完整的 Prompt 内容
    
    作用：
        在 LangChain 的执行链 (Chain) 中插入一个节点，
        用于打印发送给 LLM 的最终完整提示词，方便调试和查看 Prompt 组装是否正确。
    
    参数:
        prompt (PromptValue): LangChain 传递过来的 Prompt 对象
    返回:
        PromptValue: 原封不动地返回 prompt 对象，以便链能继续传递给下一个环节 (Model)
    """
    print("="*20 + " [DEBUG] 发送给模型的完整 Prompt " + "="*20)
    # 将 Prompt 对象转换为字符串并打印
    print(prompt.to_string())
    print("="*60)
    # 必须返回 prompt，否则链会在这里中断
    return prompt


class RagSummarizeService(object):
    """
    RAG 总结服务主类
    
    封装了从“检索”到“生成”的完整逻辑。
    """
    
    def __init__(self):
        """
        初始化 RAG 服务：
        1. 初始化向量存储连接
        2. 加载提示词模板
        3. 初始化 LLM 模型
        4. 组装 LangChain 执行链 (Chain)
        """
        # 1. 实例化向量存储服务
        self.vector_store = VectorStoreService()
        
        # 2. 获取检索器 (Retriever)，用于根据提问搜索向量库
        self.retriever = self.vector_store.get_retriever()
        
        # 3. 从rag_summarize.txt文件加载 RAG 提示词文本
        self.prompt_text = load_rag_prompts()
        
        # 4. 将字符串转换为 LangChain 的 PromptTemplate 对象，方便后续变量填充
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        
        # 5. 指定使用的大语言模型
        self.model = chat_model
        
        # 6. 初始化 LangChain 执行链 (Chain)
        self.chain = self._init_chain()

    def _init_chain(self):
        """
        这里的下划线_是约定俗成的 “内部使用” 标记，提醒外部使用者不要直接调用。

        【内部方法】组装 LangChain LCEL (LangChain Expression Language) 链
        
        链的执行顺序 (Pipe 语法 |):
            PromptTemplate -> print_prompt (调试) -> Model -> OutputParser
            
        返回:
            Chain: 一个可调用的 LangChain 链对象
        """
        # 使用 LCEL 语法组装链
        # 1. self.prompt_template: 接收字典变量，生成 Prompt
        # 2. print_prompt: (可选) 打印 Prompt 用于调试
        # 3. self.model: 接收 Prompt，调用 LLM 生成回复
        # 4. StrOutputParser(): 提取模型回复中的文本内容
        chain = self.prompt_template | print_prompt | self.model | StrOutputParser()
        return chain

    def retriever_docs(self, query: str) -> list[Document]:
        """
        执行检索步骤
        
        参数:
            query (str): 用户的原始提问字符串 
        返回:
            list[Document]: 一个包含 LangChain Document 对象的列表，
                           每个对象包含 page_content (文本内容) 和 metadata (元数据)
        """
        # 调用检索器的 invoke 方法获取相关文档
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        """
        【主业务方法】执行完整的 RAG 问答流程
        
        流程:
            1. 根据 query 检索文档
            2. 将多个文档拼接成一个上下文字符串 (Context String)
            3. 将 query 和 context 传入链中
            4. 获取模型的最终总结回复
        
        参数:
            query (str): 用户的问题，例如 "小户型应该关注扫地机器人的哪些功能"
        返回:
            str: 大模型基于参考资料生成的最终回答文本
        """
        # 步骤 1: 获取相关文档列表
        context_docs = self.retriever_docs(query)
        
        # 步骤 2: 拼接上下文字符串
        # 初始化空字符串用于存放整理后的参考资料
        context = ""
        counter = 0
        # 遍历每一个检索到的 Document 对象
        for doc in context_docs:
            counter += 1
            # 格式化拼接：将内容和元数据组装在一起，方便模型查看
            # 格式示例: 【参考资料1】: 参考资料：xxx | 参考元数据：xxx
            context += f"【参考资料{counter}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"

        # 步骤 3: 调用链 (Chain)
        # 传入一个字典，key 必须与 prompt_template 中的占位符一致
        # rag_summarize.txt中的模板包括 "input" (用户问题) 和 "context" (组装好的参考资料)
        res = self.chain.invoke(
            {
                "input": query,
                "context": context
            }
        )

        # 步骤 4: 返回最终结果
        return res


if __name__ == '__main__':
    """
    脚本入口：用于测试 RagSummarizeService
    """
    # 1. 实例化 RAG 服务对象
    rag = RagSummarizeService()

    # 2. 调用主方法进行提问，并打印结果
    print(rag.rag_summarize("小户型应该关注扫地机器人的哪些功能"))
