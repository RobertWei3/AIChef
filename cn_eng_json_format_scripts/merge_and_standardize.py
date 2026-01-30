import json
import os
import re

# 根据你上传的文件推测的路径
ENGLISH_FILE = "data/processed/eng_merge_recipes_master.json" 
# 注意：你需要确认你的旧中文数据文件路径，假设是 data/recipe_rag_ready.json
CHINESE_FILE = "data/recipe_rag_ready.json" 
OUTPUT_FILE = "data/rag_ready_final.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    print(f"⚠️ 文件不存在: {path}，将跳过。")
    return []

def process_english_data(recipes):
    processed = []
    for r in recipes:
        # 1. 构造检索文本 (Title + Ingredients + Instructions)
        # 英文数据本来就是列表，直接 join
        ing_str = ", ".join(r.get("ingredients", []))
        # instructions 可能是列表，也可能是字符串，做个容错
        inst_raw = r.get("instructions", [])
        inst_str = " ".join(inst_raw) if isinstance(inst_raw, list) else str(inst_raw)
        
        page_content = f"Title: {r['title']}\nIngredients: {ing_str}\nInstructions: {inst_str}"
        
        # 2. 构造 Metadata (黄金标准结构)
        metadata = {
            "id": r["id"],
            "name": r["title"], # 保留 name 兼容旧代码
            "title": r["title"],
            "language": "en", # 标记语言
            "image": r.get("image_path"), # 统一用 image 字段 (retriever里读的是 image)
            "tags": [], 
            "ingredients": r.get("ingredients", []),
            "instructions": r.get("instructions", []), # 核心：结构化步骤
            "source_url": r.get("source_url", "")
        }
        
        processed.append({
            "page_content": page_content,
            "metadata": metadata
        })
    return processed

def process_chinese_data(recipes):
    processed = []
    for r in recipes:
        # 旧数据的结构是外层有 page_content, metadata
        meta = r.get("metadata", {}).copy()
        content = r.get("page_content", "")
        
        # 尝试从 page_content 提取步骤
        instructions_list = []
        # 简单的启发式提取：假设步骤以数字开头 "1. "
        if "烹饪步骤" in content:
            parts = re.split(r'\d+\.\s', content.split("烹饪步骤")[-1])
            instructions_list = [p.strip() for p in parts if p.strip()]
        else:
            # 如果提取失败，就把整个 content 当作一步
            instructions_list = [content]

        # 补全 Metadata
        meta["language"] = "zh"
        meta["title"] = meta.get("name")
        meta["instructions"] = instructions_list # 补全结构化步骤
        meta["ingredients"] = [] # 中文暂时留空，或者你需要写更复杂的正则从 content 里提取
        
        # 确保 image 字段存在
        if "image" not in meta:
            meta["image"] = None

        processed.append({
            "page_content": content,
            "metadata": meta
        })
    return processed

def main():
    print("🔄 开始合并数据...")
    en_data = load_json(ENGLISH_FILE)
    zh_data = load_json(CHINESE_FILE)
    
    final_data = process_english_data(en_data) + process_chinese_data(zh_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 合并完成！共 {len(final_data)} 条数据。")
    print(f"📂 输出文件: {OUTPUT_FILE}")
    print("🚀 请运行: python core/ingest.py")

if __name__ == "__main__":
    main()