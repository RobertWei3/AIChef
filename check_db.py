import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ================= 配置 =================
# 必须和 ingestion 时保持完全一致
DB_PATH = "data/chroma_db_baai"
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# 强制使用镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

def check_quality():
    print(f"正在连接数据库: {DB_PATH} ...")
    
    # 1. 加载模型 (必须和入库时一样)
    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 2. 连接数据库
    vector_store = Chroma(
        collection_name="recipe_collection_v3",
        embedding_function=embeddings,
        persist_directory=DB_PATH
    )
    
    # --- 检查点 1: 数据总量 ---
    # Chroma 内部计数方法
    count = vector_store._collection.count()
    print(f"\n📊 [检查点 1] 数据总量: {count} 条")
    if count > 10000:
        print("   ✅ 数量正常 (符合预期)")
    else:
        print("   ⚠️ 数量偏少，请确认是否有大量数据被跳过")

    # --- 检查点 2: 语义检索测试 ---
    query = "适合冬天吃的暖身汤"
    print(f"\n🔎 [检查点 2] 语义检索测试")
    print(f"   测试问题: '{query}'")
    
    # search_type="similarity_score_threshold" 可以设置阈值，这里用基础检索看原始分数
    # k=3 取前三名
    results = vector_store.similarity_search_with_score(query, k=3)
    
    for i, (doc, score) in enumerate(results):
        print(f"\n   --- 结果 {i+1} (距离分数: {score:.4f}) ---")
        print(f"   菜名: {doc.metadata.get('name')}")
        print(f"   片段: {doc.page_content[:60]}...") # 只看前60个字
        
        # 解释分数: Chroma 默认用 L2 距离。
        # 0 表示完全一样。越小越好。
        # 通常 < 0.6 表示相关性不错。 > 1.0 表示很不相关。

    # --- 检查点 3: Metadata 修复验证 ---
    print(f"\n🛠 [检查点 3] Metadata 结构验证 (检查 Tags 和 Image)")
    first_meta = results[0][0].metadata
    
    # 验证 Image
    img = first_meta.get('image')
    print(f"   Image 字段值: '{img}' (类型: {type(img)})")
    if img is not None:
        print("   ✅ Image 字段存在且不为 None")
    else:
        print("   ❌ Image 依然是 None (修复失败)")
        
    # 验证 Tags
    tags = first_meta.get('tags')
    print(f"   Tags 字段值:  '{tags}' (类型: {type(tags)})")
    if isinstance(tags, str):
        print("   ✅ Tags 已成功转为字符串")
    elif isinstance(tags, list):
        print("   ❌ Tags 依然是列表 (可能导致过滤报错)")

if __name__ == "__main__":
    check_quality()