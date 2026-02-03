from langchain_openai import ChatOpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
from core.cache import CacheManager  # 👈 1. 必须引入缓存管理器

class SearchAgent:
    def __init__(self):
        # 初始化 LLM
        if LLM_API_KEY:
            self.llm = ChatOpenAI(
                model=LLM_MODEL_NAME,
                api_key=LLM_API_KEY,
                base_url=LLM_BASE_URL,
                temperature=0.1
            )
        else:
            self.llm = None
            
        # 👇 2. 关键：初始化缓存 (这行代码会触发 Redis 连接并打印日志)
        self.cache = CacheManager()

    def rewrite_query(self, user_query: str) -> str:
        """
        将用户查询转化为最佳搜索关键词
        """
        # 0. 预处理 Key (去空格、转小写，增加命中率)
        cache_key = f"query_rewrite:{user_query.strip().lower()}"

        # 👇 3. 查缓存 (先看 Redis 有没有)
        cached_res = self.cache.get(cache_key)
        if cached_res:
            # 如果命中了，直接返回，不再往下走 (所以速度会极快)
            return cached_res

        # --- 以下是缓存未命中的逻辑 (LLM 思考) ---
        
        # 兜底：如果没有 LLM，直接返回原词
        if not self.llm:
            return user_query

        # 精简版 Prompt
        prompt = f"""
        Act as a bilingual search optimizer. Convert user queries into keywords for vector retrieval.
        Rules:
        1. Keep language consistency.
        2. Normalization (Pinyin -> Chinese).
        3. Remove conversational fillers.
        4. Output ONLY keywords.

        User Input: {user_query}
        Keywords:
        """

        try:
            response = self.llm.invoke(prompt)
            optimized_query = response.content.strip()
            
            # 清洗一下可能的引号
            optimized_query = optimized_query.replace('"', '').replace("'", "")
            
            print(f"🧠 [SearchAgent] 意图重写: '{user_query}' -> '{optimized_query}'")

            # 👇 4. 写缓存 (把结果存进 Redis，下次就不用想了)
            # 只有当结果有效且和原词不一样时才存 (防止存垃圾数据)
            if optimized_query:
                self.cache.set(cache_key, optimized_query, ttl=86400) # 存 24 小时
            
            return optimized_query

        except Exception as e:
            print(f"❌ [SearchAgent] 优化失败: {e}")
            return user_query