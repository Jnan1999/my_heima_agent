# 提供模型对象

from abc import ABC, abstractmethod
from typing import Optional, Union

from langchain_community.chat_models.tongyi import ChatTongyi  # type: ignore[attr-defined]
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from utils.config_handler import rag_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[BaseChatModel]:
        """生成聊天模型实例

        Returns:
            ChatTongyi 实例，或 None（如果初始化失败）
        """
        return ChatTongyi(model=rag_conf["chat_model_name"])  # type: ignore[return-value]


class EmbeddingsFactory:
    def generator(self) -> Optional[Embeddings]:
        """生成 Embedding 模型实例

        Returns:
            DashScopeEmbeddings 实例，或 None（如果初始化失败）
        """
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])  # type: ignore[return-value]


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
