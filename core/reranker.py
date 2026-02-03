import requests
import json
from core.config import RERANK_API_KEY, RERANK_BASE_URL, RERANK_MODEL_NAME

class Reranker:
    """
    Reranker (云端 API 版)
    不占用本地显存/内存，通过 HTTP 请求调用 SiliconFlow 的重排序服务。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Reranker, cls).__new__(cls)
            if not RERANK_API_KEY:
                print("⚠️ [Reranker] 未配置 RERANK_API_KEY，精排功能将跳过！")
            else:
                print(f"☁️ [Reranker] 已启用云端模式 (Model: {RERANK_MODEL_NAME})")
        return cls._instance

    def rerank(self, query: str, docs: list, top_k: int = 5):
        """
        调用云端 API 对文档列表进行打分重排
        """
        # 1. 前置检查：如果没有 API Key 或者文档列表为空，直接返回原列表的前 k 个
        if not RERANK_API_KEY or not docs:
            return docs[:top_k]

        # 2. 准备数据：将文档对象转换为纯文本列表
        # Rerank 模型需要同时看标题、食材和做法摘要才能准确判断
        documents_text = []
        for d in docs:
            # 拼接文本: "Title: 西红柿炒蛋 | Ingredients: ['西红柿', '蛋'] | Content: ..."
            # 注意: 这里只取 content 的前 200 字符，避免超出 API 的 Token 限制
            content_snippet = d.get('content', '')[:300]
            ingredients_str = str(d.get('ingredients', []))
            
            # 组合成一段语义完整的文本给模型看
            full_text = f"菜名: {d.get('title', '未知')} | 食材: {ingredients_str} | 内容: {content_snippet}"
            documents_text.append(full_text)

        # 3. 构造请求 Payload
        payload = {
            "model": RERANK_MODEL_NAME,
            "query": query,
            "documents": documents_text,
            "top_n": top_k, 
            "return_documents": False # 只需要分数，不需要它把文本再传回来，节省流量
        }

        headers = {
            "Authorization": f"Bearer {RERANK_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            # 4. 发送请求
            # print(f"⚖️ [Reranker] 正在请求云端打分 ({len(docs)} 条)...")
            response = requests.post(RERANK_BASE_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status() # 如果状态码不是 200，抛出异常
            
            result = response.json()
            api_results = result.get('results', [])
            
            # print(f"✅ [Reranker] API 响应成功，耗时: {response.elapsed.total_seconds():.2f}s")

            # 5. 解析并重组结果
            final_results = []
            for item in api_results:
                # API 返回格式通常包含: index (原列表索引), relevance_score (相关性分数)
                idx = item['index']
                score = item['relevance_score']
                
                # 找到对应的原始文档对象
                doc = docs[idx]
                doc['rerank_score'] = score # 把分数写进去，方便调试查看
                final_results.append(doc)

            # (API 通常已经排好序了，但为了保险我们再排一次)
            final_results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return final_results

        except Exception as e:
            print(f"❌ [Reranker] 云端调用失败: {e}")
            print("🔄 [Reranker] 自动降级：返回原始检索顺序")
            # 兜底：如果 API 挂了，不要让程序崩，直接返回粗排结果
            return docs[:top_k]