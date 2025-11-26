# 食谱 RAG 助手 (Recipe RAG Assistant)

一个本地优先的食谱检索增强生成 (RAG) 助手。

## 功能
- **数据导入**: 加载您自己的食谱数据集 (JSON 格式)。
- **RAG 流程**: 使用 ChromaDB 和多语言 Sentence Transformers 根据食材检索相关食谱。
- **生成**: 使用 LLM (如 Ollama) 生成新的中文食谱。
- **融合**: 融合多个食谱的烹饪技巧。
- **安全**: 针对非食物查询的基本安全检查。

## 安装设置

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **(可选) 设置本地 LLM**:
   - 安装 [Ollama](https://ollama.com/)。
   - 拉取一个模型: `ollama pull llama3` (或者其他支持中文的模型，如 `qwen2`)。
   - 确保它运行在 `http://localhost:11434`。
   - 如果跳过此步骤，系统将使用模拟的后备响应。

3. **运行服务器**:
   ```bash
   uvicorn main:app --reload
   ```

## 使用方法

### 导入数据
```bash
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{"path": "data/sample_recipes.json"}'
```

### 生成食谱
```bash
curl -X POST "http://127.0.0.1:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"ingredients": ["鸡肉", "面条"], "preferences": "辣味"}'
```

### 融合食谱
```bash
curl -X POST "http://127.0.0.1:8000/fusion" \
     -H "Content-Type: application/json" \
     -d '{"ingredients": ["面包", "芝士"]}'
```
