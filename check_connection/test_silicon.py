from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

print("正在连接硅基流动 API...")

client = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url=os.getenv("SILICONFLOW_BASE_URL")
)

model_name = os.getenv("SILICONFLOW_MODEL_NAME")
print(f"使用模型: {model_name}")

try:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": "你好，请用一句话证明你连通了！"}
        ],
        stream=False
    )
    print("\n✅ 成功！模型回复：")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"\n❌ 失败: {e}")
    print("请检查 .env 文件里的 LLM_API_KEY 和 LLM_MODEL_NAME 是否正确。")