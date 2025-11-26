import json
import argparse
import sys
import re

# ============================================================
# Constants & Configuration
# ============================================================

STOPWORDS = {
    "水", "开水", "温水", "凉开水", "油", "食用油", "盐", "白糖", "糖", "淀粉",
    "味精", "鸡精", "生抽", "老抽", "酱油", "醋", "料酒"
}

# Units and descriptors to remove for keyword extraction
UNITS_AND_DESCRIPTORS = [
    "g", "克", "kg", "千克", "斤", "两", "ml", "毫升", "l", "升",
    "小勺", "大勺", "勺", "适量", "少许", "若干", "适可而止",
    "丝", "片", "丁", "末", "蓉", "段", "块", "条", "粒", "个", "只", "把", "本", "张", "袋", "盒",
    "半", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"
]

NORMALIZE_MAP = {
    "花肉": "五花肉",
    "色拉油小匙": "色拉油",
    "青葱根": "青葱"
}

# Tagging Whitelists
PORK_WORDS = ["猪肉", "五花肉", "瘦肉", "排骨", "仔排", "猪颈肉"]
BEEF_WORDS = ["牛肉", "牛腩", "肥牛", "牛里脊", "牛排"]
CHICKEN_WORDS = ["鸡肉", "鸡腿", "鸡翅", "鸡爪", "鸡胸肉", "鸡块"]
SEAFOOD_WORDS = ["虾", "虾仁", "鱼", "鱼片", "海鲜", "蟹", "蛤", "贝", "花甲"]

# ============================================================
# Helper Functions
# ============================================================

def normalize_keyword(text):
    """
    Clean ingredient text to extract the core keyword.
    Removes numbers, units, descriptors, and stopwords.
    """
    if not text:
        return None
    
    # 1. Remove numbers (digits)
    text = re.sub(r'\d+|[0-9]+', '', text)
    
    # 2. Remove units and descriptors
    # Sort by length descending to match longest first
    sorted_units = sorted(UNITS_AND_DESCRIPTORS, key=len, reverse=True)
    for unit in sorted_units:
        text = text.replace(unit, "")
        
    # 3. Strip whitespace
    text = text.strip()
    
    # 4. Check stopwords
    if not text or text in STOPWORDS:
        return None
        
    # 5. Apply Normalization Map
    text = NORMALIZE_MAP.get(text, text)
        
    return text

def generate_tags(name, ingredients_display_list, instructions_text, brief_des=""):
    """
    Generate tags based on strict whitelist matching and simple category rules.
    """
    tags = {"中餐", "家常菜"}
    
    # Combine text for searching
    combined_text = name + " " + " ".join(ingredients_display_list)
    content_text = name + " " + brief_des + " " + instructions_text
    
    # Check categories
    for word in PORK_WORDS:
        if word in combined_text:
            tags.add("猪肉")
            break
            
    for word in BEEF_WORDS:
        if word in combined_text:
            tags.add("牛肉")
            break
            
    for word in CHICKEN_WORDS:
        if word in combined_text:
            tags.add("鸡肉")
            break
            
    for word in SEAFOOD_WORDS:
        if word in combined_text:
            tags.add("海鲜")
            break
            
    # Spicy check
    if any(w in combined_text for w in ["辣椒", "剁椒", "辣椒粉"]):
        tags.add("辣")
        
    # Steamed check
    if "蒸" in instructions_text:
        tags.add("蒸")
        
    # Extra Category Tags
    # "饼", "糕", "包", "点心" -> "点心"
    if any(k in content_text for k in ["饼", "糕", "包", "点心"]):
        tags.add("点心")

    # "冰", "刨冰", "冰淇淋" -> "甜品"
    if any(k in content_text for k in ["冰", "刨冰", "冰淇淋"]):
        tags.add("甜品")

    # "茶", "糖水" -> "饮品"
    if any(k in name for k in ["茶", "糖水"]):
        tags.add("饮品")

    # "汤" -> "汤菜"
    if "汤" in name:
        tags.add("汤菜")
        
    return list(tags)

def build_markdown_recipe(name, brief_des, ingredients_display, seasonings, instructions, tips):
    """
    Construct a Chinese Markdown string for the full recipe.
    """
    md_lines = []
    md_lines.append(f"# {name}")
    md_lines.append("")
    
    if brief_des:
        md_lines.append(f"{brief_des.strip()}")
        md_lines.append("")
    
    md_lines.append("## 用料")
    
    # Add main ingredients
    if ingredients_display:
        for item in ingredients_display:
            md_lines.append(f"- {item}")
            
    # Add seasonings with a separator or subsection
    if seasonings:
        md_lines.append("")
        md_lines.append("## 调味料")
        for item in seasonings:
            md_lines.append(f"- {item}")
            
    md_lines.append("")
    
    md_lines.append("## 做法")
    if instructions:
        for idx, step in enumerate(instructions, 1):
            desc = step.get('description', '').strip()
            if desc:
                md_lines.append(f"{idx}. {desc}")
    md_lines.append("")
    
    if tips and any(tips):
        md_lines.append("## 小贴士")
        for tip in tips:
            if tip:
                md_lines.append(f"- {tip}")
        md_lines.append("")
        
    return "\n".join(md_lines)

def process_recipes(input_path, output_path, limit=50):
    print(f"Reading from {input_path}...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    valid_recipes = []
    sorted_keys = sorted(data.keys())
    
    count = 0
    for key in sorted_keys:
        if count >= limit:
            break
            
        recipe = data[key]
        name = recipe.get("recipeName")
        instructions = recipe.get("instructions")
        
        # Basic validation
        if not name or not instructions or not isinstance(instructions, list):
            continue
            
        # 1. Process Ingredients & Seasonings
        raw_ingredients = recipe.get("ingredients", [])
        raw_seasonings = recipe.get("seasonings", [])
        
        ingredients_display = []
        keywords_set = set()
        
        # Process main ingredients
        for item in raw_ingredients:
            if isinstance(item, dict):
                iname = item.get("name", "").strip()
                iweight = item.get("weight", "").strip()
                if iname:
                    # Display: "Name Weight"
                    display_str = f"{iname} {iweight}".strip()
                    ingredients_display.append(display_str)
                    
                    # Keyword extraction
                    kw = normalize_keyword(iname)
                    if kw:
                        keywords_set.add(kw)
                        
        # Process seasonings
        has_seasonings = False
        clean_seasonings = []
        for item in raw_seasonings:
            if isinstance(item, str) and item.strip():
                has_seasonings = True
                clean_seasonings.append(item.strip())
                kw = normalize_keyword(item)
                if kw:
                    keywords_set.add(kw)
                    
        # 2. Filter Invalid Recipes
        if not ingredients_display and not has_seasonings:
            continue
            
        # 3. Generate Tags
        instructions_text = ""
        for step in instructions:
            instructions_text += step.get("description", "")
        
        brief_des = recipe.get("briefDes", "")
        
        tags = generate_tags(name, ingredients_display + clean_seasonings, instructions_text, brief_des)
        
        # 4. Build Markdown
        tips = recipe.get("tips", [])
        
        full_recipe_md = build_markdown_recipe(
            name,
            brief_des,
            ingredients_display,
            clean_seasonings,
            instructions,
            tips
        )
        
        # 5. Construct Final Object
        normalized_recipe = {
            "name": name,
            "ingredients": list(keywords_set),
            "ingredients_display": ingredients_display,
            "full_recipe": full_recipe_md,
            "tags": tags
        }
        
        valid_recipes.append(normalized_recipe)
        count += 1

    print(f"Collected {len(valid_recipes)} valid recipes.")
    
    print(f"Writing to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_recipes, f, ensure_ascii=False, indent=2)
        print("Done.")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/recipeData-new1.json")
    parser.add_argument("--output", default="data/master_recipes_test.json")
    args = parser.parse_args()
    
    process_recipes(args.input, args.output)
