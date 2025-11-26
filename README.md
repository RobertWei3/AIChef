# 🥦 AIChef - 冰箱剩菜大救星 (Fridge Rescue Chef)

> **"不知道怎么处理冰箱里的剩菜？交给 AI 大厨吧！"**

![App Demo](image_21c592.jpg)

## 📖 项目简介 (Introduction)

**AIChef** 是一个基于 **RAG (检索增强生成)** 技术的智能烹饪助手。不同于传统的关键词菜谱搜索，它专注于解决 **“剩菜处理”** 的痛点。

用户只需输入冰箱里现有的食材（例如：“只剩半个洋葱和两个鸡蛋”），系统会：
1.  **🔍 检索 (Retrieve)**：从本地向量数据库（ChromaDB）中检索 10,000+ 道食谱中最相关的灵感。
2.  **🍳 生成 (Generate)**：利用大语言模型（LLM）的推理能力，教用户如何“变废为宝”，灵活调整食谱以适配现有食材。

## ✨ 核心功能 (Features)

* **🥗 剩菜智能匹配**：支持模糊语义搜索，理解食材之间的关联（如：没有猪肉可以用鸡肉替代）。
* **💡 创意烹饪指导**：AI 不会照搬食谱，而是根据你手头的食材，生成定制化的烹饪步骤。
* **⚡️ 极速本地检索**：基于 ChromaDB 和 BAAI Embedding 模型，毫秒级响应。
* **💬 交互式对话**：基于 Streamlit 构建的清爽聊天界面，支持多轮对话。

## 🛠 技术栈 (Tech Stack)

* **前端 UI**：Streamlit
* **后端逻辑**：Python
* **向量数据库**：ChromaDB
* **Embedding 模型**：BAAI/bge-small-zh-v1.5 (HuggingFace)
* **LLM (大模型)**：OpenAI 兼容接口 (支持 SiliconFlow Qwen, DeepSeek, Google Gemini 等)

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

确保你的电脑已安装 Python 3.10+。

```bash
# 克隆项目 (如果你上传到 GitHub)
git clone [https://github.com/your-username/AIChef.git](https://github.com/your-username/AIChef.git)
cd AIChef

# 创建并激活虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt