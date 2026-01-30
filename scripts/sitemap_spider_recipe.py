import requests
import xml.etree.ElementTree as ET
import gzip
import json
import hashlib
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from recipe_scrapers import scrape_me
from tqdm import tqdm  # 进度条库

# --- 配置区域 ---
SITEMAP_URL = "https://www.simplyrecipes.com/sitemap.xml"
OUTPUT_FILE = "data/raw/simplyrecipes/english_recipes_full.json"
MAX_WORKERS = 10  # 并发线程数，建议 5-10，太高容易被封 IP
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# --- 1. Sitemap 解析器 ---
def fetch_sitemap_urls(url):
    """递归获取 Sitemap 中的所有 URL"""
    headers = {"User-Agent": USER_AGENT}
    urls = set()
    
    try:
        # print(f"🔍 正在读取 Sitemap: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        # 处理 .gz 压缩文件
        if url.endswith('.gz'):
            content = gzip.decompress(response.content)
        else:
            content = response.content
            
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # 情况 A: Sitemap Index (包含子 Sitemap)
        if 'sitemapindex' in root.tag:
            sitemaps = root.findall('ns:sitemap', namespace)
            print(f"📦 发现 {len(sitemaps)} 个子 Sitemap，开始递归解析...")
            for sm in sitemaps:
                loc = sm.find('ns:loc', namespace).text
                urls.update(fetch_sitemap_urls(loc))
                
        # 情况 B: Urlset (包含实际链接)
        elif 'urlset' in root.tag:
            for u in root.findall('ns:url', namespace):
                loc = u.find('ns:loc', namespace).text
                # 🔥 核心过滤 1: 只保留看起来像食谱的 URL
                # SimplyRecipes 的食谱通常含 /recipes/ 或 -recipe-
                if "/recipes/" in loc or "-recipe-" in loc:
                    urls.add(loc)
                    
    except Exception as e:
        print(f"❌ 解析 Sitemap 失败 ({url}): {e}")
        
    return urls

# --- 2. 单个页面抓取逻辑 (复用你之前的逻辑) ---
def scrape_single_url(url):
    try:
        # 随机休眠一小会儿，模拟人类行为，减少封禁风险
        time.sleep(random.uniform(0.1, 0.5))
        
        scraper = scrape_me(url)
        
        # 🔥 核心过滤 2: 必须有食材和步骤
        if not scraper.ingredients() or not scraper.instructions():
            return None

        recipe_id = hashlib.md5(url.encode()).hexdigest()
        
        return {
            "id": recipe_id,
            "title": scraper.title(),
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions_list(),
            # 这里先预设图片路径，后续由 batch_generate.py 生成
            "image_path": f"/recipe_images/{recipe_id}_hero.jpg",
            "source_url": url,
            "language": "en" # 标记语言
        }
    except Exception:
        # 忽略所有解析错误（大部分是因为只要不是食谱页面 recipe_scraper 就会报错）
        return None

# --- 3. 主程序 ---
def main():
    print(f"🚀 启动 SimplyRecipes 爬虫 v2.0")
    
    # 1. 获取 URL 列表
    print("Step 1: 正在从 Sitemap 获取链接 (这可能需要几秒钟)...")
    all_urls = list(fetch_sitemap_urls(SITEMAP_URL))
    print(f"✅ 从 Sitemap 中捕获到 {len(all_urls)} 个潜在食谱链接")
    
    # 2. 检查已存在的数据 (断点续传)
    existing_ids = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    existing_ids.add(item['id'])
            print(f"📂 发现本地已有 {len(existing_ids)} 条数据，将自动跳过。")
        except:
            print("⚠️ 本地文件读取失败或为空，将重新开始。")

    # 3. 过滤掉已抓取的 URL
    urls_to_scrape = []
    for url in all_urls:
        uid = hashlib.md5(url.encode()).hexdigest()
        if uid not in existing_ids:
            urls_to_scrape.append(url)
            
    print(f"📌 实际需要抓取: {len(urls_to_scrape)} 个链接")
    
    # 如果没有要抓取的，直接退出
    if not urls_to_scrape:
        print("🎉 所有链接已抓取完毕！")
        return

    # 4. 多线程并发抓取
    valid_recipes = []
    
    # 如果存在旧数据，先载入内存
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                valid_recipes = json.load(f)
            except:
                valid_recipes = []

    print(f"\nStep 2: 启动 {MAX_WORKERS} 个线程开始抓取...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_url = {executor.submit(scrape_single_url, url): url for url in urls_to_scrape}
        
        # 使用 tqdm 显示进度条
        for future in tqdm(as_completed(future_to_url), total=len(urls_to_scrape), unit="url"):
            result = future.result()
            if result:
                valid_recipes.append(result)
                
                # (可选) 每抓取 50 个就保存一次，防止程序崩溃数据全丢
                if len(valid_recipes) % 50 == 0:
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(valid_recipes, f, ensure_ascii=False, indent=2)

    # 5. 最终保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(valid_recipes, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 抓取完成！")
    print(f"总计有效食谱: {len(valid_recipes)}")
    print(f"数据已保存至: {OUTPUT_FILE}")
    print("👉 下一步: 运行 scripts/batch_generate.py 为这些食谱生成图片。")

if __name__ == "__main__":
    main()