import sys
import os
import json
import torch
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 确保能导入 core 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 引入你的配置
try:
    from core.config import DB_PATH_V3, EMBEDDING_MODEL_NAME, COLLECTION_NAME
except ImportError:
    # 如果找不到 config，就临时硬编码一下（防止你 config 还没改好）
    print("⚠️ 警告: 无法导入 core.config，使用默认路径测试")
    DB_PATH_V3 = "data/chroma_db_baai" 
    EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
    COLLECTION_NAME = "recipe_collection_v3"

def check_database():
    print(f"🕵️‍♂️ 正在检查数据库: {DB_PATH_V3}")
    print(f"📚 集合名称: {COLLECTION_NAME}")

    # 1. 设置 Embedding (和入库时保持一致)
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    
    print(f"⚡️ 使用设备: {device}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )

    # 2. 连接数据库
    try:
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=DB_PATH_V3
        )
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    # 3. 随便搜一个词，看看出来的结果对不对
    test_query = "七彩虾仁"  # 或者你数据里确定的任意一个菜名
    print(f"\n🔍 正在搜索测试词: '{test_query}' ...")
    
    results = vector_store.similarity_search(test_query, k=1)

    if not results:
        print("❌ 未找到任何结果！请检查 ingest.py 是否执行成功，或者 COLLECTION_NAME 是否一致。")
        return

    # 4. 检查结果详情
    doc = results[0]
    meta = doc.metadata
    
    print("\n✅ 检索成功！")
    print(f"菜名 (Name): {meta.get('name')}")
    print(f"标签 (Tags): {meta.get('tags')}")
    print("-" * 30)
    
    # 重点检查 Instructions
    instructions_raw = meta.get('instructions')
    print(f"步骤数据类型: {type(instructions_raw)}")
    
    if isinstance(instructions_raw, str):
        print("✅ 格式正确：是 JSON 字符串")
        try:
            steps_list = json.loads(instructions_raw)
            print(f"✅ 解析成功：包含 {len(steps_list)} 个步骤")
            print(f"第一步预览: {steps_list[0].get('description')[:20]}...")
        except json.JSONDecodeError:
            print("❌ 解析失败：虽然是字符串，但不是合法的 JSON")
    elif isinstance(instructions_raw, list):
        print("⚠️ 格式警告：是 List 类型（这在旧版 Chroma 可能导致错误，但如果能读出来也行）")
    else:
        print("❌ 数据缺失：没有找到 instructions 字段")

if __name__ == "__main__":
    check_database()