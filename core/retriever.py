import os
import sys
import json
import torch
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from core.config import SOURCE_FILE
from core.vector_db import VectorDBManager 

class HybridRetrieverManager:
    _ensemble_retriever = None

    @classmethod
    def get_retriever(cls):
        if cls._ensemble_retriever:
            return cls._ensemble_retriever

        # 1. 获取向量库 Retriever
        db_manager = VectorDBManager() 
        vector_store = db_manager.get_vector_store() 
        
        if not vector_store: return None
        
        # 向量检索配置 (Top 20)
        chroma_retriever = vector_store.as_retriever(search_kwargs={"k": 20})

        # 2. 构建 BM25 Retriever (关键词索引)
        print("📚 [Retriever] 正在初始化 BM25 索引 (全字段模式)...")
        docs_for_bm25 = []
        if os.path.exists(SOURCE_FILE):
            try:
                with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        # =================================================
                        # 🚀 核心修改开始：暴力拼接所有字段
                        # =================================================
                        meta = item.get('metadata', {})
                        title = meta.get('title', '')
                        
                        # 处理可能是列表也可能是字符串的字段
                        def safe_str(val):
                            if isinstance(val, list):
                                return " ".join(str(x) for x in val)
                            return str(val)

                        ingredients = safe_str(meta.get('ingredients', ''))
                        instructions = safe_str(meta.get('instructions', ''))
                        original_content = item.get('page_content', '') # 这是原本的简介

                        # 拼成一个超级字符串！
                        # 格式：[标题] + [原料] + [步骤] + [简介]
                        # 这样 BM25 就能看见每一个角落的关键词了
                        full_search_text = f"{title} {ingredients} {instructions} {original_content}"
                        
                        docs_for_bm25.append(Document(
                            page_content=full_search_text,  # 👈 这里变了，不再只用 item['page_content']
                            metadata=meta
                        ))
                        # =================================================
                        # 🚀 修改结束
                        # =================================================

            except Exception as e:
                print(f"⚠️ 读取源文件失败，BM25 将不可用: {e}")

        if docs_for_bm25:
            bm25_retriever = BM25Retriever.from_documents(docs_for_bm25)
            bm25_retriever.k = 20
            
            # 3. 混合 (50% 向量 + 50% 关键词)
            cls._ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, chroma_retriever],
                weights=[0.5, 0.5]
            )
            print("✅ [Retriever] 混合检索器 (Hybrid) 就绪")
        else:
            print("⚠️ 未建立 BM25 索引，降级为纯向量检索")
            cls._ensemble_retriever = chroma_retriever

        return cls._ensemble_retriever

def retrieve_docs(query: str, top_k: int = 50):
    """
    执行混合召回
    """
    hybrid_r = HybridRetrieverManager.get_retriever()
    if not hybrid_r:
        return []

    print(f"🔎 [Retriever] 正在执行混合检索: {query} ...")
    try:
        results = hybrid_r.invoke(query)
    except Exception as e:
        print(f"❌ 检索出错: {e}")
        return []
    
    # 格式化结果
    formatted_results = []
    for doc in results:
        # 安全解析 JSON
        def safe_json(val):
            if isinstance(val, str):
                try: return json.loads(val)
                except: return val
            return val

        formatted_results.append({
            "id": doc.metadata.get('id', ''),
            "title": doc.metadata.get('title') or doc.metadata.get('name', '未知'),
            "image": doc.metadata.get('image', ''),
            "ingredients": safe_json(doc.metadata.get('ingredients', [])),
            "instructions": safe_json(doc.metadata.get('instructions', [])),
            "content": doc.page_content, # 注意：这里返回给 Reranker 的还是拼接后的长文本，有助于 Reranker 也没问题
            "score": 0 
        })
    
    # 去重
    unique_results = {d['title']: d for d in formatted_results}.values()
    return list(unique_results)