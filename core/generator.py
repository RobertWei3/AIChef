from openai import OpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
import re

# 初始化客户端
client = None
if LLM_API_KEY:
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

def smart_select_and_comment(query: str, candidates: list):
    """
    智能优选 Rerank (灵活版)
    不再死板过滤，而是侧重于“推荐 + 建议”
    """
    if not client:
        return 0, "API Key 未配置，默认推荐："
    
    if not candidates:
        return 0, "没有候选菜谱。"

    # 1. 构建候选列表
    candidates_str = ""
    for i, doc in enumerate(candidates):
        snippet = doc.get('content', '')[:150].replace('\n', ' ')
        candidates_str += (
            f"选项[{i}]: {doc.get('name')}\n"
            f"   - 标签: {doc.get('tags', [])}\n"
            f"   - 简介: {snippet}...\n\n"
        )

    # =====================================================
    # ✅ 优化后的 Prompt：更像一个懂得变通的大厨
    # =====================================================
    system_prompt = """
    你是一位聪明、懂变通的私家大厨。你的任务是从给定的候选菜谱中，为用户推荐**最合适**的一道。

    【推荐逻辑】：
    1. **找最大公约数**：优先选择食材、口味最接近用户需求的菜。
    2. **灵活处理忌口**：
       - 如果用户说“不要辣”，尽量选不辣的。
       - **关键点**：如果候选项全都有辣，**不要拒绝回答！** 请选一个最容易“去辣”的菜（比如把辣椒油换成香油），并在理由里告诉用户怎么调整。
    3. **不仅是选择，更是建议**：推荐理由要告诉用户“为什么选它”或者“怎么做更符合你的要求”。

    【输出格式】：
    请直接返回一行：索引数字 ||| 推荐理由
    （例如：1 ||| 虽然原谱有辣椒，但这道菜只要不放辣椒油，依然非常鲜美，很适合您。）
    """

    user_prompt = f"""
    用户需求：【{query}】

    候选列表：
    {candidates_str}

    请做出你的选择：
    """

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4, # 稍微放松一点创造力
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        # print(f"🤖 [Generator] AI 建议: {content}") 

        # --- 解析逻辑 (保持鲁棒性) ---
        if "|||" in content:
            index_part, reason = content.split("|||", 1)
            match = re.search(r'\d+', index_part)
            if match:
                return int(match.group()), reason.strip()
        
        # 兜底：如果 AI 直接说了数字开头
        match = re.search(r'^\d+', content)
        if match:
             return int(match.group()), f"为您推荐【{candidates[int(match.group())]['name']}】"

        # 彻底无法解析
        return 0, f"试试这道【{candidates[0]['name']}】，应该不错！"

    except Exception as e:
        print(f"❌ [Generator] 报错: {e}")
        return 0, "为您推荐以下菜谱："

