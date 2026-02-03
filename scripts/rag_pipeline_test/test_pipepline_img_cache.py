import sys
import os
import time
import json

# 保持你原有的路径配置逻辑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.pipeline import rag_chain

def run_test_case(query, description=""):
    print("="*60)
    if description:
        print(f"📋 测试场景: {description}")
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

    # 3. 生成层 (文字 + 图片)
    print("-" * 60)
    print(f"🤖 [Chef AI] 回复:\n{result.get('answer')}")
    
    # NEW: 打印图片链接 ---------------------------------------
    image_url = result.get('image')
    if image_url:
        print(f"\n🎨 [DALL-E] 美食绘图已生成: \n👉 {image_url}")
    else:
        print(f"\n🎨 [DALL-E] 未生成图片 (可能未搜到菜谱或使用了缓存但无图)")
    # --------------------------------------------------------

    print("-" * 60)
    print(f"⚡️ 总耗时: {duration:.2f} 秒")
    print("="*60 + "\n")

if __name__ == "__main__":
    
    print("🚀 启动全链路集成测试 (End-to-End Pipeline Test)...\n")
    
    # 1. 系统预热
    print("⏳ 系统预热中...")
    try:
        rag_chain("warm up") 
        print("✅ 预热完成。\n")
    except:
        print("⚠️ 预热失败，直接开始。\n")

    # 2. 基础功能测试
    test_queries = [
        ("xihongshi", "拼音 + 模糊搜索"),
        ("做法简单不需要烤箱的甜点", "复杂语义 + 排除法"),
        ("我想吃西瓜炒肉，最好是加点板蓝根！！！", "黑暗料理防御测试"),
    ]

    for q, desc in test_queries:
        run_test_case(q, desc)
        # time.sleep(1) # 并行模式下通常不需要 sleep，除非怕触发 API 速率限制

    # 3. 🔥 缓存命中测试 (重点)
    print("\n" + "#"*60)
    print("🔁  CACHE 性能测试 (验证 Redis 是否生效)")
    print("#"*60 + "\n")
    
    cache_query = "红烧肉怎么做"
    
    print("🔻 第 1 次请求 (冷启动 - 应该较慢，因为要生成图片)...")
    run_test_case(cache_query, "首次请求 (无缓存)")
    
    print("🔻 第 2 次请求 (热启动 - 应该极快，命中 Cache)...")
    run_test_case(cache_query, "重复请求 (期望命中缓存)")