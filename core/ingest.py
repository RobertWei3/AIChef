import json
import os
import shutil
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from core.config import DB_PATH_V3, EMBEDDING_MODEL_NAME, COLLECTION_NAME

# 1. 配置路径
# SOURCE_FILE = "data/recipe_rag_ready_fixed.json" 
# 源文件在pull的时候没有找到，这里线换乘rag ready的文件
SOURCE_FILE = "data/recipe_rag_ready.json"

def ingest_data():
    # 检查源文件
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ 错误：找不到源文件 {SOURCE_FILE}")
        return

    # 检查数据库是否已存在
    if os.path.exists(DB_PATH_V3):
        print(f"🗑️ 发现旧数据库 {DB_PATH_V3}，正在删除以进行重建...")
        shutil.rmtree(DB_PATH_V3)
    
    print("🚀 开始加载 Embedding 模型 (BAAI)...")
    
    # 自动检测设备
    if torch.backends.mps.is_available():
        device = "mps"
        print("⚡️ 检测到 Mac GPU (MPS)，已启用加速模式！")
    elif torch.cuda.is_available():
        device = "cuda"
        print("⚡️ 检测到 NVIDIA GPU (CUDA)，已启用加速模式！")
    else:
        device = "cpu"
        print("🐢 未检测到 GPU，正在使用 CPU 模式...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )

    print(f"📖 正在读取数据: {SOURCE_FILE}")
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 转换格式
    documents = []
    for item in raw_data:
        meta = item['metadata'].copy()
        
        # -------------------------------------------------------
        # ✅ 核心修复：把 List/Dict 类型的数据转成 JSON 字符串
        # -------------------------------------------------------
        
        # 1. 处理 tags (List -> String)
        # 例如: ['菌菇', '海鲜'] -> "['菌菇', '海鲜']"
        if 'tags' in meta and isinstance(meta['tags'], list):
            meta['tags'] = json.dumps(meta['tags'], ensure_ascii=False)
            
        # 2. 处理 instructions (List of Dicts -> String)
        # 这一步非常关键！否则 instructions 也会报错
        if 'instructions' in meta and isinstance(meta['instructions'], list):
            meta['instructions'] = json.dumps(meta['instructions'], ensure_ascii=False)

        doc = Document(
            page_content=item['page_content'],
            metadata=meta 
        )
        documents.append(doc)

    print(f"📦 正在将 {len(documents)} 条数据写入向量库...")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=DB_PATH_V3,
        collection_name=COLLECTION_NAME
    )
    
    print("✅ 入库完成！复杂数据已序列化存储。")

if __name__ == "__main__":
    ingest_data()