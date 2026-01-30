from langchain_openai import ChatOpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
import re
import ast

# 初始化客户端 (使用 LangChain 统一接口)
llm = None

# 1. 优先检查 SiliconFlow / DeepSeek (OpenAI 兼容接口)
if LLM_API_KEY:
    print(f"✅ 使用 SiliconFlow (model: {LLM_MODEL_NAME})")
    llm = ChatOpenAI(
        model=LLM_MODEL_NAME,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.7
    )
else:
    print("⚠️ 未配置 SiliconFlow API Key，生成功能将不可用。")

class MockResponse:
    def __init__(self, content):
        self.content = content

def safe_invoke(messages):
    """
    统一的 LLM 调用封装
    """
    if not llm:
        return MockResponse("🤖 (未配置 API Key，请查看下方菜谱)")

    try:
        # 直接调用配置好的 LLM
        return llm.invoke(messages)
    except Exception as e:
        print(f"❌ [SafeInvoke] LLM 调用失败: {e}")
        return MockResponse("🤖 (AI 服务暂时不可用，请检查 API Key 或网络)")

def smart_select_and_comment(query: str, candidates: list):
    """
    智能优选 Rerank (灵活版)
    不再死板过滤，而是侧重于“推荐 + 建议”
    """
    if not llm:
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
    你是一位聪明、幽默且懂变通的私家大厨。你的任务是从给定的候选菜谱中，为用户推荐**最合适**的一道。

    【推荐逻辑】：
    1. **找最大公约数**：优先选择食材、口味最接近用户需求的菜。
    2. **幽默处理离谱搭配**：
       - 如果用户给出了离谱的搭配（例如“西瓜炒牛肉”、“巧克力炖蒜”），请**不要**强行推荐这道菜（如果有的话）。
       - 请用**幽默**的语气吐槽这个搭配，并给出一个**合理的烹饪理由**来排除它。
       - 例如：“虽然我有‘西瓜炒肉’的谱子，但为了您的肠胃安全，我强烈建议我们还是吃‘凉拌西瓜皮’如果是想吃瓜的话，或者‘小炒黄牛肉’如果是想吃肉的话。毕竟强扭的瓜不甜，强炒的肉...可能不仅不甜还很怪。”
    3. **灵活处理忌口**：
       - 如果用户说“不要辣”，尽量选不辣的。
       - **关键点**：如果候选项全都有辣，**不要拒绝回答！** 请选一个最容易“去辣”的菜（比如把辣椒油换成香油），并在理由里告诉用户怎么调整。
    4. **不仅是选择，更是建议**：推荐理由要告诉用户“为什么选它”或者“怎么做更符合你的要求”。

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
        # LangChain 调用
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        
        response_msg = safe_invoke(messages)
        content = response_msg.content
        
        # --- 增强解析逻辑 ---
        # 1. 如果是列表 (Multipart)，拼接
        if isinstance(content, list):
             content = " ".join([str(c) for c in content])
        
        # 2. 如果是字典 (或类似结构)，尝试提取 text
        if isinstance(content, dict):
            content = content.get('text', str(content))
            
        # 3. 如果是字符串但看起来像字典 (Stringified Dict)
        content = str(content).strip()
        if content.startswith("{") and "text" in content:
            try:
                val = ast.literal_eval(content)
                if isinstance(val, dict) and 'text' in val:
                    content = val['text']
            except:
                pass # 解析失败就保留原样

        content = str(content).strip()

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

def generate_rag_answer(query: str, candidates: list) -> str:
    """
    为搜索结果列表生成一段 "厨师顾问" 风格的综述
    """
    if not llm:
        return "🤖 AI 厨师正在休息（未配置 API Key），请直接查看下方菜谱。"
        
    if not candidates:
        return "抱歉，没有找到相关菜谱，我也很难为您提供建议。"

    # 1. 简要构建候选信息
    candidates_summary = ""
    for i, doc in enumerate(candidates[:5]):
        candidates_summary += f"- {doc.get('name')} (标签: {doc.get('tags')})\n"

    system_prompt = """
    你是一位高端家庭餐厅的主厨顾问，性格幽默风趣，擅长用专业的烹饪知识来点评食材。
    用户的需求可能只是几个食材名。你的任务是根据搜索到的菜谱列表，给用户一段**专业、优雅且得体**的开场建议。
    
    【推荐逻辑】：
    1.  **语气专业且幽默**：在保持专业度的同时，加入适度的幽默感。
    2.  **总结亮点**：概括菜品特色，体现烹饪的艺术感。
    3.  **给出建议**：简要提及食材搭配或风味特点。
    4.  **幽默排雷（最高优先级）**：
        - **必须检查**：无论是否搜到了菜谱，先检查用户的输入里有没有**奇怪、离谱或调侃**的词（如“屎”、“毒药”、“混凝土”等）或者**黑暗料理搭配**（如“板蓝根泡面”、“西瓜炒肉”）。
        - **混合输入处理**：如果用户输入了“巧克力和蒜”，虽然可能有巧克力菜谱，但你**必须**先吐槽“蒜”在这个组合里的突兀，然后再推荐正常的菜谱！
        - **合理理由**：给出排除理由时要基于烹饪原理或常识（例如：“大蒜的辛辣与巧克力的醇厚实在难以调和”，“高温会破坏西瓜清爽的口感”）。
        - **例子**：“巧克力我懂，但这大蒜...除非您想尝试‘吸血鬼退散’风味，否则我建议还是让大蒜去陪排骨吧。我也为您准备了几道正常的巧克力甜点...”
        - **拒绝无视**：绝对不能假装没看见离谱词只回答正常的，那样太呆板了！
    5.  **形式要求**：严禁使用 Emoji 表情符号。字数控制在 100 字以内。
    
    """

    
    user_prompt = f"""
    用户想吃/有的食材：【{query}】
    搜索到的菜谱：
    {candidates_summary}

    请给用户一段简短的高级感推荐语：
    """

    try:
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        
        response = safe_invoke(messages)
        content = response.content
        
         # --- 增强解析逻辑 ---
        if isinstance(content, list):
             content = " ".join([str(c) for c in content])
             
        if isinstance(content, dict):
            content = content.get('text', str(content))

        content = str(content).strip()
        
        # 处理 Stringified Dict (例如 SiliconFlow/DeepSeek 偶尔返回的格式)
        if content.startswith("{") and "text" in content:
            try:
                import ast
                val = ast.literal_eval(content)
                if isinstance(val, dict) and 'text' in val:
                    content = val['text']
            except:
                pass

        print(f"✅ AI 响应内容: {content[:50]}...")
        return content
            
    except Exception as e:
        print(f"❌ [Generator] Summary 报错: {e}")
        return f"基于您的食材偏好，我为您甄选了以下几道值得尝试的美味佳肴。"
