from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
import os

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def get_retriever(self):
        """
        获取向量检索器对象
        :return: LangChain Retriever 对象，用于后续的相似度搜索
        """
        # 将向量库转换为检索器，并设置搜索时返回最相似的 k 个结果
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def load_document(self):
        """
        从数据文件夹(chroma.yml中定义为-data_path: data)内读取数据文件，转为向量存入向量库
        要计算文件的MD5做去重
        :return: None
        """

        def check_md5_hex(md5_for_check: str) -> bool:
            """
            [内部函数] 检查文件的 MD5 值是否已存在（即文件是否已被处理过）
            :param md5_for_check: 待检查的 MD5 哈希值
            :return: True 表示已处理过，False 表示未处理
            """
            # 如果 MD5 记录文件不存在
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                # 创建一个空的 MD5 记录文件
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False  # 文件刚创建，肯定没处理过

            # 打开 MD5 记录文件读取
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                # 遍历文件中的每一行
                for line in f.readlines():
                    line = line.strip()
                    # 如果发现当前 MD5 已在文件中
                    if line == md5_for_check:
                        return True  # 表示该文件已处理过

                return False  # 循环结束没找到，说明没处理过

        def save_md5_hex(md5_for_check: str):
            """
            [内部函数] 将处理过的文件 MD5 写入记录文件
            :param md5_for_check: 待保存的 MD5 哈希值
            """
            # 以追加模式打开文件
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                # 写入 MD5 并换行
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str) -> list[Document]:
            """
            [内部函数] 根据文件后缀选择对应的加载器读取文件
            :param read_path: 文件路径
            :return: LangChain Document 对象列表
            """
            # 如果是 txt 文件
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            # 如果是 pdf 文件
            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            # 其他不支持的文件类型返回空列表
            return []

        # 1. 获取数据目录下所有允许类型的文件路径列表
        allowed_files_path: list[str] = listdir_with_allowed_type(
            # 从配置获取知识库数据文件夹的绝对路径
            get_abs_path(chroma_conf["data_path"]),
            # 从配置获取允许的文件后缀名（如 .pdf, .txt）
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        # 2. 遍历处理每一个文件
        for path in allowed_files_path:
            # 计算当前文件的 MD5 哈希值（用于文件去重）
            md5_hex = get_file_md5_hex(path)

            # 检查此 MD5 是否已经处理过
            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue  # 跳过当前循环，处理下一个文件

            try:
                # 3. 加载文件内容为 Document 对象
                documents: list[Document] = get_file_documents(path)
                # 检查文档是否为空
                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                # 4. 使用分割器将文档切分成小块 (Chunks)
                split_document: list[Document] = self.spliter.split_documents(documents)
                # 检查切分后是否为空
                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 5. 将切分好的文档块存入向量数据库（这一步会自动调用 Embedding 模型向量化）
                self.vector_store.add_documents(split_document)

                # 6. 记录该文件的 MD5，防止下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                # 捕获加载过程中的任何异常
                # exc_info=True 会在日志中打印详细的错误堆栈信息，方便调试
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue  # 报错也不中断程序，继续处理下一个文件


if __name__ == '__main__':
    # 实例化向量存储服务
    vs = VectorStoreService()

    # 执行文档加载流程（扫描文件夹 -> 读取 -> 切片 -> 向量化 -> 入库）
    vs.load_document()

    # 获取检索器对象
    retriever = vs.get_retriever()

    # 测试检索：输入问题“迷路”，在向量库中搜索最相关的文本片段
    res = retriever.invoke("迷路")
    
    # 打印检索到的结果
    for r in res:
        print(r.page_content)  # 打印文本内容
        print("-"*20)         # 打印分割线