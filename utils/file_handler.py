import os
import hashlib
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(filepath: str):    # 获取文件的md5的十六进制字符串

    if not os.path.exists(filepath):    # 判断文件是否存在
        logger.error(f"[md5计算]文件{filepath}不存在")
        return

    if not os.path.isfile(filepath):    # 判断路径是否是文件
        logger.error(f"[md5计算]路径{filepath}不是文件")
        return

    md5_obj = hashlib.md5()

    chunk_size = 4096       # 4KB分片，避免文件过大爆内存
    try:
        with open(filepath, "rb") as f:     # 必须二进制读取
            while chunk := f.read(chunk_size):  # 海象运算符:= 把“读取 -> 赋值 -> 判断”合并成了一步
                md5_obj.update(chunk)
            """
            增量哈希机制：
                关键点: MD5 算法支持 “流水线作业”，不需要一次性看到所有数据。
                当调用 update(chunk_1) 时，它内部的状态机就基于这 4KB 进行一轮计算。
                接着调用 update(chunk_2) 时，它基于上一次的状态，继续计算新的 4KB。
                直到所有片都 update 完，最后调用 hexdigest()，得到的就是整个文件的 MD5 值。
                这就是为什么分片读取不会影响最终 MD5 结果的原因。
            """
            """
            chunk = f.read(chunk_size)
            while chunk:
                
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None

"""
传入：  
    path-文件夹路径
    allowed_types-允许的文件后缀
"""
def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):        # 返回文件夹内的文件列表（允许的文件后缀）
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return allowed_types

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)


def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    return PyPDFLoader(filepath, passwd).load()


def txt_loader(filepath: str) -> list[Document]:
    return TextLoader(filepath, encoding="utf-8").load()
