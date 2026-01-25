import json
import os
import requests
import time
from pathlib import Path

# --- 配置路径 ---
# 输入文件：RAG 准备好的数据 (建议使用您刚才生成的 rag_ready_final.json)
INPUT_FILE = 'data/recipe_rag_ready.json' 
# 输出文件：下载图片并更新路径后的最终文件
OUTPUT_FILE = 'data/recipe_rag_ready_with_local_images.json'
# 图片保存目录 (前端静态资源目录)
IMG_SAVE_DIR = 'frontend/public/recipe_images'

# 确保图片目录存在
Path(IMG_SAVE_DIR).mkdir(parents=True, exist_ok=True)

def download_and_update():
    print(f"正在读取文件: {INPUT_FILE} ...")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：找不到 {INPUT_FILE}，请确保您已经运行了之前的合并脚本。")
        return

    print(f"找到 {len(data)} 条食谱，开始处理图片...")
    
    success_count = 0
    skip_count = 0
    
    # 创建一个 Session，复用连接，提高下载速度
    session = requests.Session()
    # 模拟浏览器 Header，防止反爬
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

    for item in data:
        metadata = item.get('metadata', {})
        recipe_id = str(metadata.get('id', ''))
        # 尝试获取图片链接，您的数据里可能叫 'image' 或者 'cover_image'
        # 根据您之前提供的 JSON 结构，这里主要是 'image' 字段
        img_url = metadata.get('image')

        if not recipe_id or not img_url or not img_url.startswith('http'):
            # 如果没有 ID 或 URL 无效，跳过
            skip_count += 1
            continue

        # 定义本地文件名 (例如: 10001.jpg)
        # 去掉 URL 后面的参数 (如 !default)
        clean_url = img_url.split('!')[0]
        ext = os.path.splitext(clean_url)[1]
        if not ext or len(ext) > 5: ext = '.jpg' # 默认后缀
        
        file_name = f"{recipe_id}{ext}"
        local_path = os.path.join(IMG_SAVE_DIR, file_name)
        
        # 前端引用的相对路径 (以 / 开头)
        frontend_path = f"/recipe_images/{file_name}"

        # 1. 下载图片 (如果本地不存在)
        if not os.path.exists(local_path):
            try:
                print(f"⬇️ 正在下载: {recipe_id} - {metadata.get('name')} ...")
                resp = session.get(img_url, timeout=10)
                if resp.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(resp.content)
                    success_count += 1
                    time.sleep(0.2) # 稍微停顿，礼貌爬取
                else:
                    print(f"   ⚠️ 下载失败 (状态码 {resp.status_code}): {img_url}")
            except Exception as e:
                print(f"   ⚠️ 下载出错: {e}")
        else:
            # print(f"   ✅ 已存在，跳过下载: {recipe_id}")
            pass

        # 2. 【关键步骤】修改 JSON 数据中的 image 字段指向本地
        # 只要本地文件存在（或者是刚才下载的），就更新路径
        if os.path.exists(local_path):
            item['metadata']['image'] = frontend_path

    # 保存新的 JSON 文件
    print("-" * 30)
    print(f"正在保存更新后的数据到: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"🎉 处理完成！\n- 新下载图片数: {success_count}\n- 图片文件夹: {IMG_SAVE_DIR}\n- 请使用新生成的 JSON 文件重新运行 ingest 脚本。")

if __name__ == "__main__":
    download_and_update()