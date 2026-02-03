import sys
import os
import time
import json

# 添加路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.pipeline import rag_chain

def run_test_case(query):
    print("="*60)
    print(f"🗣️  用户 Query: 【{query}】")
    print("-" * 60)
    
    start_total = time.time()
    
    # 运行 RAG 链
    try:
        result = rag_chain(query)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return

    duration = time.time() - start_total
    
    # --- 🔍 深入解剖 RAG 内部 ---
    
    # 1. 意图理解层
    print(f"🧠 [Agent] 优化后关键词: '{result.get('optimized_query')}'")
    
    # 2. 检索层 (查看最终交给 Generator 的 Top Docs)
    docs = result.get('source_docs', [])
    print(f"📚 [Rerank] 最终选出 {len(docs)} 个最佳参考文档:")
    for i, doc in enumerate(docs):
        # 打印 Rerank 分数，验证精排是否生效
        score = doc.get('rerank_score', 'N/A')
        # score 如果是 float，格式化一下
        score_str = f"{score:.4f}" if isinstance(score, float) else score
        print(f"   {i+1}. [{score_str}] {doc.get('title')} (ID: {doc.get('id')})")
        # print(f"      摘要: {doc.get('content')[:50]}...")

    # 3. 生成层
    print("-" * 60)
    print(f"🤖 [Chef AI] 回复:\n{result.get('answer')}")
    print("-" * 60)
    print(f"⚡️ 总耗时: {duration:.2f} 秒")
    print("="*60 + "\n")

if __name__ == "__main__":
    # 定义几个具有代表性的测试用例
    test_queries = [
        # 1. 拼音 + 模糊搜索 (测试 Agent + Vector)
        "xihongshi", 
        
        # 2. 具体的复杂需求 (测试 Reranker 是否能排对)
        "做法简单不需要烤箱的甜点", 
        
        # 3. 离谱/攻击性测试 (测试 Generator 的幽默排雷)
        "我想吃西瓜炒肉，最好是加点板蓝根",
        
        # 4. 英文输入 (测试 Agent 双语能力)
        "How to cook spicy tofu" 
    ]

    print("🚀 启动全链路集成测试 (End-to-End Pipeline Test)...\n")
    
    # 首次运行通常较慢（加载模型），预热一下
    print("⏳ 系统预热中 (加载 Embedding/Rerank 模型)...")
    try:
        rag_chain("warm up") 
        print("✅ 预热完成，开始正式测试。\n")
    except:
        print("⚠️ 预热失败，直接开始测试。\n")

    for q in test_queries:
        run_test_case(q)
        time.sleep(1) # 稍微歇一下，防止 LLM API 限流