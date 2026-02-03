import os
import sys
# 确保能找到项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import (
    DB_PATH_V3, 
    COLLECTION_NAME, 
    EMBEDDING_MODEL_NAME
)

class VectorDBManager:
    _instance = None
    _vector_store = None

    def __new__(cls):
        """单例模式：确保数据库只被加载一次"""
        if cls._instance is None:
            cls._instance = super(VectorDBManager, cls).__new__(cls)
            print("💾 [VectorDB] 正在初始化向量数据库连接...")
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={'device': 'cpu'}, 
                encode_kwargs={'normalize_embeddings': True}
            )

            if os.path.exists(DB_PATH_V3):
                self._vector_store = Chroma(
                    persist_directory=DB_PATH_V3,
                    embedding_function=self.embeddings,
                    collection_name=COLLECTION_NAME
                )
                print("✅ [VectorDB] 数据库连接成功！")
            else:
                print(f"❌ [VectorDB] 错误：找不到数据库文件 {DB_PATH_V3}")
                self._vector_store = None
                
        except Exception as e:
            print(f"❌ [VectorDB] 初始化失败: {e}")
            self._vector_store = None

    def get_vector_store(self):
        """🚀 关键方法：外部获取数据库实例"""
        if self._vector_store is None:
            if not getattr(self, '_vector_store', None):
                 self._initialize()
            if self._vector_store is None:
                raise ValueError("向量数据库未初始化！")
        return self._vector_store