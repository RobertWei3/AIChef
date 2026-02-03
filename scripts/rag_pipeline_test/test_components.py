import sys
import os
import time

# 将项目根目录加入路径，确保能 import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.search_agent import SearchAgent
from core.reranker import Reranker

def test_search_agent():
    print("\n🧪 [1/3] 测试 Search Agent (意图理解 + 缓存)...")
    agent = SearchAgent()
    
    # 测试 Query 1: 拼音
    q1 = "xihongshi"
    print(f"   输入: {q1}")
    start = time.time()
    res1 = agent.rewrite_query(q1)
    print(f"   输出: {res1} (耗时: {time.time()-start:.2f}s)")
    
    if "西红柿" in res1 or "番茄" in res1:
        print("   ✅ 意图理解通过")
    else:
        print("   ❌ 意图理解失败")

    # 测试 Query 2: 缓存命中
    print("   👉 再次输入相同词 (测试缓存)...")
    start = time.time()
    res2 = agent.rewrite_query(q1)
    print(f"   输出: {res2} (耗时: {time.time()-start:.4f}s)")
    
    if (time.time() - start) < 0.1:
        print("   ✅ 缓存命中成功 (极速响应)")
    else:
        print("   ⚠️ 缓存似乎未生效 (或者是第一次运行/Redis未连接)")

def test_reranker():
    print("\n🧪 [2/3] 测试 Reranker (打分模型)...")
    reranker = Reranker()
    
    query = "西红柿做法"
    # 模拟两个文档：一个强相关，一个弱相关
    docs = [
        {"title": "清蒸鲈鱼", "ingredients": ["鲈鱼", "葱姜"], "content": "这是做鱼的..."}, # 干扰项
        {"title": "西红柿炒蛋", "ingredients": ["西红柿", "鸡蛋"], "content": "先炒鸡蛋..."},  # 正确项
    ]
    
    print(f"   Query: {query}")
    print("   正在重排序...")
    ranked = reranker.rerank(query, docs, top_k=2)
    
    for i, doc in enumerate(ranked):
        print(f"   Rank {i+1}: {doc['title']} (Score: {doc.get('rerank_score', 0):.4f})")
    
    if ranked[0]['title'] == "西红柿炒蛋":
        print("   ✅ Reranker 排序逻辑正确")
    else:
        print("   ❌ Reranker 排序失败，模型可能未加载或逻辑错误")

if __name__ == "__main__":
    print("🚀 开始组件单元测试...")
    try:
        test_search_agent()
        test_reranker()
        print("\n🎉 所有组件测试完成！如果全绿，请运行 test_pipeline.py")
    except Exception as e:
        print(f"\n❌ 测试中断，发生错误: {e}")