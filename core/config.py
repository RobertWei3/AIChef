import os
from dotenv import load_dotenv

# 1. 自动加载 .env 文件
# 获取项目根目录 (AIChef/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# 2. 数据库配置
# ⚠️ 注意：请去 data 文件夹确认你的数据库文件夹叫什么名字
# 如果是 chroma_db_baai 就写这个，如果是 chroma_db_v3 就改一下
DB_PATH = os.path.join(ROOT_DIR, "data", "chroma_db_baai")
DB_PATH_V3 = os.path.join(ROOT_DIR, "data", "chroma_db_v3")
COLLECTION_NAME = "recipe_collection_v3"

# 数据source file 位置
SOURCE_FILE = "data/rag_ready_final.json"

# Embedding 模型 (用于检索)
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
# 强制使用国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 3. 大模型配置 (支持 SiliconFlow 或 Google Gemini)
# 优先读取 SiliconFlow，如果没有则尝试读取 Gemini
LLM_API_KEY = os.getenv("SILICONFLOW_API_KEY")
LLM_BASE_URL = os.getenv("SILICONFLOW_BASE_URL")
LLM_MODEL_NAME = (os.getenv("SILICONFLOW_MODEL_NAME") or "").split("#")[0].strip()
LLM_MODEL_IMG_NAME = (os.getenv("SILICONFLOW_PIC_MODEL_NAME") or "").split("#")[0].strip()

# Rerank 配置
RERANK_API_KEY = os.getenv("RERANK_API_KEY")
RERANK_BASE_URL = os.getenv("RERANK_BASE_URL")
RERANK_MODEL_NAME = (os.getenv("RERANK_MODEL_NAME") or "").split("#")[0].strip()

# 简单检查
if not LLM_API_KEY:
    print("⚠️ 警告: 未检测到 SiliconFlow API 配置，生成功能将无法使用。")


# ===========================
# ⚡️ Redis Cache Configuration(test)
# ===========================
# 1. 地址: 如果是在你本机运行代码，Docker 也是本机，这里就是 localhost
REDIS_HOST = "localhost"
# 2. 端口: 默认都是 6379
REDIS_PORT = 6379
# 3. 密码: 必须和你 Docker 启动命令里设置的一模一样！
# 如果你用的方案 A (无密码)，这里这就填 None
REDIS_PASSWORD = None