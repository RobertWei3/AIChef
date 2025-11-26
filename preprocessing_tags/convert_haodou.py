import json
import os

# ================= 配置区域 =================
# 输入文件名 (请确保该文件在同一目录下)
INPUT_FILE = 'data/recipeData-new1.json'
# 输出文件名
OUTPUT_FILE = 'data/recipeData_with_tags.json'

# 标签规则字典：关键词 -> 对应的 Tag
# 你可以在这里随意添加自己的规则
TAG_RULES = {
    # --- 食材类 ---
    "虾": "海鲜", "鱼": "海鲜", "蟹": "海鲜", "贝": "海鲜", "鱿": "海鲜", "海鲜": "海鲜",
    "鸡": "肉禽", "鸭": "肉禽", "鹅": "肉禽", "肉": "肉禽", "排骨": "肉禽", "牛": "肉禽", "羊": "肉禽", "猪": "肉禽",
    "蛋": "蛋奶", "豆腐": "豆制品", "腐竹": "豆制品", "豆干": "豆制品",
    "面": "主食", "饭": "主食", "粥": "主食", "粉": "主食", "馒头": "主食", "饼": "主食", "饺": "主食",
    "菜": "蔬菜", "菇": "菌菇", "茄": "蔬菜", "土豆": "蔬菜", "瓜": "蔬菜", "豆": "蔬菜", "笋": "蔬菜",
    
    # --- 烹饪方式 ---
    "炒": "炒菜", "爆": "炒菜", "溜": "炒菜",
    "蒸": "蒸菜", 
    "煮": "汤羹", "汤": "汤羹", "炖": "汤羹", "煲": "汤羹", "烩": "汤羹",
    "凉拌": "凉菜", "拌": "凉菜", "沙拉": "凉菜", "腌": "凉菜",
    "炸": "炸物", "酥": "炸物",
    "烤": "烤箱菜", "焗": "烤箱菜",
    "煎": "煎炸", "红烧": "红烧", "焖": "红烧",
    
    # --- 口味 ---
    "辣": "辣味", "麻": "麻辣", "水煮": "麻辣",
    "酸": "酸甜/酸辣", "醋": "酸甜/酸辣",
    "甜": "甜味", "糖": "甜味", "拔丝": "甜味",
    "咖喱": "咖喱",
    "清淡": "清淡"
}

def generate_tags(recipe_name, ingredients_list):
    """根据菜名和食材列表生成标签"""
    tags = set()
    
    # 1. 准备搜索文本：菜名 + 所有食材名
    name_str = recipe_name if recipe_name else ""
    ing_str = ""
    
    # 处理食材列表结构 (兼容列表中的字典或纯字符串)
    if isinstance(ingredients_list, list):
        for item in ingredients_list:
            if isinstance(item, dict):
                # 提取 {"name": "虾仁", ...} 中的 name
                ing_str += item.get('name', '') + " "
            elif isinstance(item, str):
                ing_str += item + " "
    
    # 拼接成一个大字符串方便检索
    full_search_text = name_str + " " + ing_str
    
    # 2. 遍历规则进行匹配
    for keyword, tag in TAG_RULES.items():
        if keyword in full_search_text:
            tags.add(tag)
            
    # 3. 兜底策略：如果没有匹配到任何标签，标记为"其他"或"家常菜"
    if not tags:
        tags.add("家常菜")
        
    return list(tags)

def main():
    # 检查文件是否存在
    if not os.path.exists(INPUT_FILE):
        print(f"错误：找不到文件 '{INPUT_FILE}'。请确保json文件在当前脚本运行目录下。")
        return

    print(f"正在读取 {INPUT_FILE} ...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 JSON 失败: {e}")
        return

    print(f"开始处理 {len(data)} 条数据...")
    
    count = 0
    # 遍历字典结构
    for key, recipe in data.items():
        r_name = recipe.get('recipeName', '')
        r_ingredients = recipe.get('ingredients', [])
        
        # 生成并写入 tags
        recipe['tags'] = generate_tags(r_name, r_ingredients)
        
        count += 1
        if count % 1000 == 0:
            print(f"已处理 {count} 条...")

    print("处理完成，正在保存...")
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文不乱码
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"成功！文件已保存为: {OUTPUT_FILE}")
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == "__main__":
    main()