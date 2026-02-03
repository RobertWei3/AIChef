import json
from concurrent.futures import ThreadPoolExecutor
from core.retriever import retrieve_docs
from core.generator import generate_rag_answer
from core.search_agent import SearchAgent
from core.reranker import Reranker
from core.image_generator import ImageGenerator  # 👈 新增导入
from core.cache import CacheManager              # 👈 新增导入

# 初始化组件
search_agent = SearchAgent()
reranker = Reranker()
image_generator = ImageGenerator()               # 👈 初始化画师
cache = CacheManager()                           # 👈 初始化缓存

def rag_chain(query: str):
    """
    高级 RAG 流水线: 
    Cache -> Rewrite -> Hybrid Retrieve -> Rerank -> Filter -> Parallel(Generate Text + Image)
    """
    
    # =================================================
    # 🚀 1. 结果缓存检查 (Result Caching)
    # =================================================
    # 如果用户问过完全一样的问题，直接返回上次的完整结果（含图片URL）
    # 这样既能秒回，又能省 DALL-E 3 的钱 ($0.04/张)
    cache_key = f"rag_final_response:{query.strip().lower()}"
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"⚡️ [Pipeline] 命中完整结果缓存，直接返回！")
        return json.loads(cached_result)

    # =================================================
    # 🔄 2. RAG 核心链路
    # =================================================
    
    # 2.1 意图重写
    optimized_query = search_agent.rewrite_query(query)
    
    # 2.2 混合召回
    initial_docs = retrieve_docs(optimized_query, top_k=50)
    
    # 2.3 深度精排
    ranked_docs = reranker.rerank(optimized_query, initial_docs, top_k=5)
    
    # 2.4 分数过滤
    SCORE_THRESHOLD = 0.35 
    final_docs = []
    for doc in ranked_docs:
        score = doc.get('rerank_score', 0)
        if score > SCORE_THRESHOLD:
            final_docs.append(doc)
    
    # 兜底：如果过滤太狠，强制保留 Top 1
    if not final_docs and ranked_docs:
        print(f"⚠️ [Pipeline] 强制兜底保留 Top 1")
        final_docs = [ranked_docs[0]]
    
    print(f"🧐 [Pipeline] 最终采用 {len(final_docs)} 个文档进行生成")

    # =================================================
    # ⚡️ 3. 并行生成 (Parallel Execution)
    # =================================================
    # 我们使用线程池同时跑 "写文案" 和 "画图"
    
    answer = ""
    image_url = None
    
    # 只有当找到了相关食谱时，才去生成图片，否则没素材画不出来
    should_generate_image = len(final_docs) > 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        # --- 任务 A: LLM 写点评 (CPU/IO 密集) ---
        future_text = executor.submit(generate_rag_answer, query, final_docs)
        
        # --- 任务 B: DALL-E 画图 (IO 密集, 耗时久) ---
        future_img = None
        if should_generate_image:
            # 我们取相关性最高的 Top 1 菜谱来画图
            top_doc = final_docs[0]
            # 这里的 safe_get 防止字段缺失报错
            dish_title = top_doc.get('title', 'Delicious Food')
            # 确保 ingredients 是列表
            ingredients = top_doc.get('ingredients', [])
            if isinstance(ingredients, str):
                # 简单容错处理
                ingredients = [ingredients]

            future_img = executor.submit(image_generator.generate, dish_title, ingredients)
        
        # --- 等待结果 ---
        # 1. 获取文本 (通常较快)
        answer = future_text.result()
        
        # 2. 获取图片 (通常较慢，会阻塞直到完成)
        if future_img:
            image_url = future_img.result()

    # =================================================
    # 💾 4. 组装与缓存
    # =================================================
    final_response = {
        "original_query": query,
        "optimized_query": optimized_query,
        "answer": answer,
        "image": image_url,       # 👈 新增图片字段
        "source_docs": final_docs 
    }

    # 存入 Redis，有效期设为 2 小时 (7200秒)
    # 注意：这里我们缓存的是整个字典的 JSON 字符串
    try:
        cache.set(cache_key, json.dumps(final_response, ensure_ascii=False), ttl=7200)
    except Exception as e:
        print(f"⚠️ [Pipeline] 缓存写入失败: {e}")
    
    return final_response