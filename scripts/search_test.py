import sys
import os
import torch
from dotenv import load_dotenv
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- 1. 环境配置 ---
# 加载 .env 环境变量
load_dotenv()

# 动态添加项目根目录，确保能导入 core.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DB_PATH_V3, EMBEDDING_MODEL_NAME, COLLECTION_NAME

# --- 2. 初始化 LLM 客户端 (智能搜索代理) ---
# 这里以 SiliconFlow 为例，兼容 OpenAI SDK
api_key = os.getenv("SILICONFLOW_API_KEY")
base_url = os.getenv("SILICONFLOW_BASE_URL")
model_name = os.getenv("SILICONFLOW_MODEL_NAME")

# 如果没有 Key，会发出警告但允许程序运行（降级为普通搜索）
if not api_key:
    print("⚠️ 警告: 未找到 SILICONFLOW_API_KEY，智能意图识别功能将不可用。")
    client = None
else:
    client = OpenAI(api_key=api_key, base_url=base_url)

def rewrite_query(user_query):
    """
    🧠 AI 大脑: 执行“拼音纠错”和“语言一致性”优化
    """
    if not client:
        return user_query

    print(f"🤔 AI 正在分析意图: '{user_query}' ...")

    # 核心 Prompt: 强制要求语言一致性
    prompt = f"""
    You are a search query optimizer for a bilingual recipe database (English & Chinese).
    
    Your Goal: Convert the User Input into the BEST keywords for vector search, adhering to the "Language Consistency" rule.
    
    Rules:
    1. **Pinyin Handling**: If input is Chinese Pinyin (e.g., "hong shao rou", "gong bao ji ding"), convert it to **Chinese Characters** (e.g., "红烧肉", "宫保鸡丁"). DO NOT translate to English.
    2. **Language Consistency**: 
       - If the user uses **Chinese** (or Pinyin), output **Chinese** keywords.
       - If the user uses **English**, output **English** keywords.
    3. **Intent Expansion**: 
       - If input is vague (e.g., "rainy day"), expand to concrete food names in the SAME language (e.g., "汤 炖菜" for Chinese, "Soup Stew" for English).
    4. **Output**: ONLY output the keywords, no explanations.
    
    User Input: {user_query}
    Optimized Keywords:
    """

    try:
        response = client.chat.completions.create(
            model=model_name, # 或者 deepseek-ai/DeepSeek-R1
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, # 低温度确保结果稳定
            max_tokens=50
        )
        keywords = response.choices[0].message.content.strip()
        print(f"✨ 优化后的搜索词: [{keywords}]")
        return keywords
    except Exception as e:
        print(f"⚠️ LLM 调用失败，使用原始词: {e}")
        return user_query

def main():
    # --- 3. 数据库检查 ---
    if not os.path.exists(DB_PATH_V3):
        print(f"❌ 错误：找不到数据库文件夹 {DB_PATH_V3}")
        print("   请先运行 core/ingest.py 进行入库！")
        return

    print("🚀 正在加载 Embedding 模型 (这可能需要几秒钟)...")
    
    # 自动选择设备
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

    print(f"📂 连接数据库: {DB_PATH_V3}")
    vector_store = Chroma(
        persist_directory=DB_PATH_V3,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    print("\n✅ 系统就绪！支持功能：")
    print("   1. 中文搜中文 (如: '红烧肉')")
    print("   2. 英文搜英文 (如: 'Banana Bread')")
    print("   3. 拼音搜中文 (如: 'hong shao rou')")
    print("   4. 意图理解 (如: '下雨天吃什么')")
    print("-" * 50)

    while True:
        try:
            raw_query = input("\n🔍 请输入搜索关键词 (输入 'q' 退出): ").strip()
        except KeyboardInterrupt:
            break

        if raw_query.lower() in ['q', 'exit', 'quit']:
            break
        
        if not raw_query:
            continue

        # --- 4. 核心流程 ---
        
        # Step A: AI 优化查询 (拼音转汉字 / 意图补全)
        optimized_query = rewrite_query(raw_query)

        # Step B: 向量检索
        # k=3 表示返回前 3 个结果
        results = vector_store.similarity_search_with_score(optimized_query, k=3)

        if not results:
            print("⚠️ 未找到相关结果。")
            continue

        print(f"\n🏆 找到 {len(results)} 个结果:\n")
        
        for idx, (doc, score) in enumerate(results):
            meta = doc.metadata
            
            # 分数越低越好，给用户一个直观的百分比匹配度 (仅供参考)
            # 假设 0.0 是 100%，1.0 是 0%
            match_score = max(0, (1 - score)) * 100
            
            print(f"--- 结果 #{idx + 1} (匹配度: {match_score:.1f}%) ---")
            print(f"🍳 菜名: {meta.get('title') or meta.get('name', '未知')}")
            print(f"🔗 来源: {meta.get('source_site', 'unknown')}")
            
            # 显示图片路径
            img_path = meta.get('image_path') or meta.get('image', '无')
            print(f"🖼️ 图片: {img_path}")
            
            # 打印内容预览 (截取前 150 字符)
            content_preview = doc.page_content[:150].replace('\n', ' ')
            print(f"📝 内容: {content_preview}...")
            print("-" * 30)

if __name__ == "__main__":
    main()