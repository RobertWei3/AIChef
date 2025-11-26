from core.retriever import retrieve_docs
from core.generator import generate_rag_answer

def rag_chain(query: str):
    """
    RAG 标准流水线: Retrieve -> Generate
    """
    # 1. 检索 (Retrieve)
    docs = retrieve_docs(query, top_k=3)
    
    # 2. 生成 (Generate)
    answer = generate_rag_answer(query, docs)
    
    # 3. 返回完整结果 (包含引用来源，方便前端展示)
    return {
        "answer": answer,
        "source_docs": docs
    }