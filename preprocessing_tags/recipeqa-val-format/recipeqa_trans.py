import json
import os

# === 🛠️ 配置区域 ===
# 1. 数据根目录 (您存放 JSON 的地方)
BASE_DIR = 'data/raw/recipes-val'

# 2. 主索引文件 (根据您实际下载的文件名修改，通常是 recipes-train.json 或 recipes-val.json)
MAIN_INDEX_FILE = os.path.join(BASE_DIR, 'recipes-val.json') 

# 3. 步骤文件夹名
STEPS_DIR = os.path.join(BASE_DIR, 'steps')

# 4. 输出文件 (生成的“中餐格式”数据)
OUTPUT_FILE = 'data/recipe_rag_ready_english.json'

# 5. 图片前缀 (告诉前端去哪里找图)
IMG_PREFIX = '/recipe_images/en/' 
# =================

def convert_to_aichef_format():
    print(f"🚀 开始转换...\n主索引: {MAIN_INDEX_FILE}")

    # 1. 读取主索引 (菜单)
    try:
        with open(MAIN_INDEX_FILE, 'r', encoding='utf-8') as f:
            # RecipeQA 有时包裹在 'data' 里，有时直接是 list
            raw = json.load(f)
            recipe_list = raw.get('data', raw) if isinstance(raw, dict) else raw
    except FileNotFoundError:
        print(f"❌ 找不到主文件，请检查路径: {MAIN_INDEX_FILE}")
        return

    print(f"📋 找到 {len(recipe_list)} 个食谱，开始拼装详情...")
    
    final_recipes = []
    
    # 2. 遍历每一个食谱
    for item in recipe_list:
        # --- A. 提取基础信息 (来自主文件) ---
        rid = item.get('id')                  # 原始ID
        title = item.get('name', 'Unknown')   # 菜名
        thumb_name = item.get('thumbnail')    # 封面图文件名
        step_filename = item.get('steps')     # 步骤文件的文件名 (的关键！)
        
        if not step_filename: continue

        # --- B. 读取详情 (去 steps 文件夹找) ---
        step_file_path = os.path.join(STEPS_DIR, step_filename)
        
        steps_data = []
        if os.path.exists(step_file_path):
            try:
                with open(step_file_path, 'r', encoding='utf-8') as sf:
                    # 读取子文件里的 'steps' 列表
                    s_json = json.load(sf)
                    steps_data = s_json.get('steps', [])
            except:
                pass # 读取失败就跳过步骤

        # --- C. 格式化步骤 (捏成 AIChef 的形状) ---
        formatted_instructions = []
        for idx, s in enumerate(steps_data):
            # RecipeQA 的 step 里有 body(文字) 和 images(图片列表)
            desc = s.get('body') or s.get('text', '') # 兼容不同字段名
            imgs = s.get('images', [])
            
            # 取第一张图，做成完整路径
            step_img = ""
            if imgs and len(imgs) > 0:
                step_img = f"{IMG_PREFIX}{imgs[0]}"
            
            # 生成标准步骤对象
            formatted_instructions.append({
                "step_index": idx + 1,
                "description": desc,
                "image_url": step_img
            })

        # --- D. 处理封面图 ---
        final_cover = ""
        if thumb_name:
            final_cover = f"{IMG_PREFIX}{thumb_name}"
        elif formatted_instructions and formatted_instructions[0]['image_url']:
            # 如果没有封面，用第一步的图顶替
            final_cover = formatted_instructions[0]['image_url']

        # --- E. 组装最终对象 (和中餐格式一模一样) ---
        final_recipe = {
            "recipe_id": f"en_{rid}",         # 加前缀
            "recipe_name": title,
            "cover_image": final_cover,
            "instructions": formatted_instructions, # 详细步骤
            "language": "en",                 # 标记语言
            "source": "RecipeQA",
            # RAG 专用的全文文本 (用于搜索匹配)
            "full_text": f"{title}\n" + "\n".join([i['description'] for i in formatted_instructions])
        }
        
        final_recipes.append(final_recipe)

    # 3. 保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_recipes, f, ensure_ascii=False, indent=4)

    print(f"🎉 成功转换 {len(final_recipes)} 个食谱！")
    print(f"💾 结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    convert_to_aichef_format()