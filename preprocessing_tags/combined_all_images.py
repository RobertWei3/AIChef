import json
import os

# --- 配置文件路径 ---
# RAG 准备好的数据路径
rag_file_path = 'data/recipe_rag_ready.json'
# 原始包含详细步骤的数据路径
raw_file_path = 'data/raw/recipeData_with_tags.json'
# 输出文件路径
output_file_path = 'data/rag_ready_final.json'

print(f"正在读取文件...\n1. {rag_file_path}\n2. {raw_file_path}")

# 1. 读取两个文件
try:
    with open(rag_file_path, 'r', encoding='utf-8') as f:
        rag_data = json.load(f)

    with open(raw_file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except FileNotFoundError as e:
    print(f"\n❌ 错误：找不到文件 - {e.filename}")
    print("请检查文件路径是否正确，或者脚本是否在根目录下运行。")
    exit()

print(f"读取成功，开始合并 {len(rag_data)} 条数据...")

# 2. 循环合并
count = 0
for item in rag_data:
    # 获取 RAG 数据里的 id (确保转换为字符串以防万一)
    rec_id = str(item['metadata']['id'])
    
    # 构造原始数据里的 key (例如 "recipe_10001")
    raw_key = f"recipe_{rec_id}"
    
    # 如果在原始数据里找到了这个菜谱
    if raw_key in raw_data:
        # 提取 instructions
        steps = raw_data[raw_key].get('instructions', [])
        
        # 【关键】新增一个字段存步骤，不要覆盖 image
        item['metadata']['instructions'] = steps
        count += 1

# 3. 保存为新文件
# 确保存放输出文件的目录存在
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(rag_data, f, ensure_ascii=False, indent=4)

print("-" * 30)
print(f"✅ 合并完成！成功更新了 {count} 条数据。")
print(f"📁 新文件已保存为: {output_file_path}")