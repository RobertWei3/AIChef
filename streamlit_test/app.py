import streamlit as st
import time

# === 1. 页面配置 (必须放在第一行) ===
st.set_page_config(page_title="冰箱剩菜大救星", page_icon="🥦", layout="wide")

# === 2. 初始化后端 (带错误处理) ===
try:
    from core.pipeline import rag_chain
except ImportError as e:
    # 如果后端导不进来，我们定义一个假的函数，防止后面报错
    st.error(f"⚠️ 无法导入后端逻辑 (core/pipeline.py)。请检查文件位置。\n错误: {e}")
    def rag_chain(text):
        return {"answer": "后端未连接，无法回答。", "source_docs": []}

# === 3. 初始化记忆 (使用 setdefault) ===
# 这种写法比 if...in... 更原子化，确保 messages 一定存在
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "你好！我是你的剩菜顾问。请告诉我你的冰箱里还剩下什么食材？"}
    ]

# === 4. 页面标题 ===
st.title("🥦 冰箱剩菜大救星")
st.caption("输入你剩下的食材（比如：半个洋葱、两个鸡蛋...），AI 教你变废为宝！")

# === 5. 展示历史聊天记录 (终极防报错写法) ===
# ❌ 不要用 st.session_state.messages
# ✅ 要用 st.session_state.get("messages", [])
# 这样写，就算 messages 丢了，它也只会返回空列表，绝对不会红屏报错！
history = st.session_state.get("messages", [])

for msg in history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# === 6. 处理用户输入 ===
if user_input := st.chat_input("例如：土豆和牛肉，或者只有几个西红柿..."):
    # A. 显示用户的输入
    # 确保 messages 存在再 append
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)

    # B. 调用 AI 后端
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        source_docs = []
        
        with st.spinner("正在构思创意..."):
            try:
                # 调用后端
                result = rag_chain(user_input)
                full_response = result.get('answer', "抱歉，AI 没有返回回答。")
                source_docs = result.get('source_docs', [])
            except Exception as e:
                full_response = f"😓 后厨出了一点小问题：{str(e)}"

        # C. 展示 AI 回答
        response_placeholder.markdown(full_response)

        # D. 展示参考灵感 (防御性检查)
        if source_docs:
            with st.expander("🔍 查看灵感来源"):
                for i, doc in enumerate(source_docs):
                    # 检查 doc 是否有效
                    if not doc or not isinstance(doc, dict):
                        continue
                        
                    name = doc.get('name', f'灵感 {i+1}')
                    score = doc.get('score', 0)
                    content = doc.get('content', '暂无内容')
                    
                    st.markdown(f"**📖 {name}** (匹配度: {score:.2f})")
                    st.caption(content[:100] + "...")
                    st.divider()

    # E. 记住 AI 的回答
    st.session_state["messages"].append({"role": "assistant", "content": full_response})