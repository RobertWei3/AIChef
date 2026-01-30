import json
import os
import time
import sys

# 将项目根目录添加到 python path，确保能导入 core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.image_generator import ImageGenerator
# 引用全局配置中的数据文件路径
from core.config import SOURCE_FILE 

# 前端图片存放目录 (根据你的项目结构)
IMAGE_DIR = "frontend/public/recipe_images"

def main():
    # 1. 准备环境
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        print(f"📂 创建目录: {IMAGE_DIR}")
        
    generator = ImageGenerator() # 实例化核心模块

    # 2. 读取数据
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ 找不到数据文件: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    print(f"📦 加载了 {len(recipes)} 条食谱，开始检查图片...")

    updated_count = 0
    
    # 3. 循环检查每一道菜
    for index, recipe in enumerate(recipes):
        meta = recipe['metadata']
        
        # 获取基本信息
        recipe_id = meta.get('id')
        title = meta.get('title') or meta.get('name')
        ingredients = meta.get('ingredients', [])
        
        # 构造目标文件名: ID_hero.jpg
        filename = f"{recipe_id}_hero.jpg"
        local_path = os.path.join(IMAGE_DIR, filename)
        
        # 🎯 核心逻辑：只给“没图”的生成 (增量更新)
        # 如果本地没有这个文件，才调用 AI
        if not os.path.exists(local_path):
            print(f"\n[{index+1}/{len(recipes)}] 🔍 发现缺图: {title}")
            
            # 调用 Core 能力生成 URL
            img_url = generator.generate(title, ingredients)
            
            if img_url:
                # 下载并保存
                success = generator.download_to_local(img_url, local_path)
                
                if success:
                    updated_count += 1
                    # 更新 JSON 里的 image 路径 (指向前端可访问的相对路径)
                    meta['image'] = f"/recipe_images/{filename}"
                    
                    # ⚠️ 稍微停顿一下，避免触发 API 速率限制 (Rate Limit)
                    time.sleep(1.0) 
            else:
                print("⚠️ 跳过 (生成失败)")
        else:
            # print(f"⏩ 已存在，跳过: {title}") # 取消注释可查看跳过日志
            pass

    # 4. 如果有更新，回写 JSON 文件
    if updated_count > 0:
        with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 任务完成！共新生成并保存了 {updated_count} 张图片。")
        print(f"💾 数据已更新至: {SOURCE_FILE}")
        print("💡 提示：为了让搜索功能感知到新图片，请记得运行: python core/ingest.py")
    else:
        print("\n✅ 所有食谱图片已就绪，无需更新。")

if __name__ == "__main__":
    main()