import json
import os

# ================= 配置 =================
INPUT_FILE = 'data/recipeData_with_tags.json'  # 上一步生成的文件
OUTPUT_FILE = 'data/recipe_rag_ready.json'     # 处理好准备入库的文件

def serialize_recipe(recipe):
    """
    【核心函数】将单个菜谱字典转换为一段长文本
    """
    # 1. 提取基础信息
    name = recipe.get('recipeName', '未知菜名')
    desc = recipe.get('briefDes')
    desc = str(desc).strip() if desc else ""
    
    # 2. 处理标签 (列表转逗号分隔字符串)
    tags_list = recipe.get('tags', [])
    tags_str = ", ".join(tags_list)
    
    # 3. 处理食材 (提取 name 和 weight 拼接)
    # 原始格式: [{"name": "虾", "weight": "200g"}, ...]
    ingredients_list = recipe.get('ingredients', [])
    ing_text_list = []
    if isinstance(ingredients_list, list):
        for item in ingredients_list:
            if isinstance(item, dict):
                n = item.get('name', '')
                w = item.get('weight', '')
                # 拼成 "虾(200g)" 的形式，如果没有重量就只写名字
                text = f"{n}({w})" if w else n
                ing_text_list.append(text)
    ingredients_str = ", ".join(ing_text_list)

    # 4. 处理调料
    seasonings = recipe.get('seasonings', [])
    # 调料有时候是纯字符串列表，有时候是字典，简单容错一下
    season_str = ""
    if isinstance(seasonings, list):
        # 过滤掉非字符串元素，防止报错
        valid_seasonings = [str(s) for s in seasonings if s]
        season_str = ", ".join(valid_seasonings)

    # 5. 处理做法步骤
    instructions = recipe.get('instructions', [])
    steps_list = []
    if isinstance(instructions, list):
        for idx, step in enumerate(instructions):
            if isinstance(step, dict):
                # 给步骤加上序号，逻辑更清晰: "1. 做法xxx"
                # detail = step.get('description', '').strip()
                raw_desc = step.get('description')
                detail = str(raw_desc).strip() if raw_desc else ""
                if detail:
                    steps_list.append(f"{idx+1}. {detail}")
    steps_str = " ".join(steps_list)

    # 6. 【关键】组合模板
    # 这个模板的设计原则是：把最重要的信息（菜名、标签、食材）放前面
    serialized_text = (
        f"菜名: {name}\n"
        f"标签: {tags_str}\n"
        f"简介: {desc}\n"
        f"主要食材: {ingredients_str}\n"
        f"调料: {season_str}\n"
        f"烹饪步骤: {steps_str}"
    )
    
    return serialized_text

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"找不到 {INPUT_FILE}，请确认文件名。")
        return

    print("正在读取数据...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rag_docs = []
    
    print("正在序列化文本...")
    count = 0
    for key, recipe in data.items():
        # A. 生成用于向量化的文本 (Content)
        text_content = serialize_recipe(recipe)
        
        # B. 提取用于过滤的元数据 (Metadata)
        # 比如：用户搜“不辣的菜”，就可以用 metadata 中的 tags 过滤
        metadata = {
            "id": recipe.get('recipeID'),
            "name": recipe.get('recipeName'),
            "tags": recipe.get('tags', []),
            # 这里提取第一张图作为封面图，前端展示用
            "image": "" 
        }
        
        # 尝试提取图片链接
        insts = recipe.get('instructions', [])
        if insts and isinstance(insts[0], dict):
            metadata['image'] = insts[0].get('imgLink', '')

        # C. 组合成 RAG 标准对象
        entry = {
            "page_content": text_content, # 这是喂给 AI 看的
            "metadata": metadata          # 这是给数据库过滤用的
        }
        rag_docs.append(entry)
        count += 1

    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(rag_docs, f, ensure_ascii=False, indent=4)

    print(f"成功转换 {count} 条数据！")
    print(f"文件已保存为: {OUTPUT_FILE}")
    
    # 打印一个示例给用户看
    print("\n====== [示例] 序列化后的文本内容 ======")
    print(rag_docs[0]['page_content'])
    print("\n====== [示例] 提取的 Metadata ======")
    print(rag_docs[0]['metadata'])

if __name__ == "__main__":
    main()