from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from core.config import DB_PATH_V3, EMBEDDING_MODEL_NAME, COLLECTION_NAME
import torch
import json

class VectorDBManager:
    """
    单例模式管理数据库连接，防止重复加载模型导致内存爆炸
    """
    _instance = None
    _vector_store = None

    @classmethod
    def get_vector_store(cls):
        if cls._vector_store is None:
            print(f"🔄 [Retriever] 正在初始化向量库: {DB_PATH_V3}")
            try:
                if torch.backends.mps.is_available():
                    device = "mps"
                elif torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"
                embeddings = HuggingFaceEmbeddings(
                    model_name=EMBEDDING_MODEL_NAME,
                    model_kwargs={'device': device},
                    encode_kwargs={'normalize_embeddings': True}
                )
                # ⚠️ collection_name 必须和你 ingest 入库时的一致！
                # 之前我们用的是 "recipe_collection_v3"
                cls._vector_store = Chroma(
                    collection_name=COLLECTION_NAME, 
                    embedding_function=embeddings,
                    persist_directory=DB_PATH_V3
                )
                print("✅ [Retriever] 向量库加载完成")
            except Exception as e:
                print(f"❌ [Retriever] 数据库加载失败: {e}")
                return None
        return cls._vector_store

# def retrieve_docs(query: str, top_k: int = 4, score_threshold: float = 0.8):
#     """
#     检索核心函数
#     :param query: 用户问题
#     :param top_k: 返回几条结果
#     :param score_threshold: 相似度阈值 (越低越严格, >0.8 通常就不太相关了)
#     """
#     db = VectorDBManager.get_vector_store()
#     if not db:
#         return []

#     # 执行检索
#     results = db.similarity_search_with_score(query, k=top_k)
    
#     # 格式化结果
#     filtered_results = []
#     for doc, score in results:
#         # 过滤掉不太相关的结果 (分数越低越好)
#         if score <= score_threshold:
#             filtered_results.append({
#                 "name": doc.metadata.get('name', '未知'),
#                 "tags": doc.metadata.get('tags', ''),
#                 "image": doc.metadata.get('image', ''),
#                 "content": doc.page_content,
#                 "score": score
#             })
            
#     return filtered_results
# ... (前面的引用不变)

def retrieve_docs(query: str, top_k: int = 4, score_threshold: float = 1.0):
    """
    检索核心函数
    """
    db = VectorDBManager.get_vector_store()
    if not db:
        return []

    # 执行检索
    results = db.similarity_search_with_score(query, k=top_k)
    
    # 格式化结果
    filtered_results = []
    print(f"🔎 [Retriever] 检索到 {len(results)} 条，阈值: {score_threshold}")

    for doc, score in results:
        if score <= score_threshold:
            
            # 1. 核心修复：解析 JSON 字符串回列表
            # 如果 ingest 时存的是 json.dumps() 后的字符串，这里必须 loads 回来
            instructions = doc.metadata.get('instructions', [])
            if isinstance(instructions, str):
                try:
                    instructions = json.loads(instructions)
                except:
                    pass # 解析失败则保持原样

            ingredients = doc.metadata.get('ingredients', [])
            if isinstance(ingredients, str):
                try:
                    ingredients = json.loads(ingredients)
                except:
                    pass
            
            # 2. 构造返回对象
            filtered_results.append({
                "id": doc.metadata.get('id', ''),
                "title": doc.metadata.get('title') or doc.metadata.get('name', '未知'), # 兼容 title/name
                "image": doc.metadata.get('image', ''),
                "ingredients": ingredients,   # 返回列表
                "instructions": instructions, # 返回列表
                "score": score
            })
    
    # for doc, score in results:
    #     print(f"   - {doc.metadata.get('name')} (Score: {score:.4f})")
    #     # 恢复正常的阈值过滤
    #     if score <= score_threshold:
    #         filtered_results.append({
    #             "id": doc.metadata.get('id', ''),          # 建议加上 ID
    #             "name": doc.metadata.get('name', '未知'),
    #             "tags": doc.metadata.get('tags', ''),
    #             "image": doc.metadata.get('image', ''),
                
    #             # ✅【新增关键修改】提取步骤数据
    #             "instructions": doc.metadata.get('instructions', []), 
                
    #             "content": doc.page_content,
    #             "score": score
    #         })


            
    return filtered_results