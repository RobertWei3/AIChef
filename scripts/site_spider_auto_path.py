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
from tqdm import tqdm

# --- 🎯 核心配置区域 ---
# 你只需要在这里加名字和 Sitemap，路径会自动生成！
TARGET_SITES = [
    {
        "name": "simplyrecipes",  # 文件夹名和文件名会用到这个
        "sitemap_url": "https://www.simplyrecipes.com/sitemap.xml",
        "enabled": False
    },
    {
        "name": "seriouseats",
        "sitemap_url": "https://www.seriouseats.com/sitemap.xml",
        "enabled": True
    },
    {
        "name": "eatingwell",
        "sitemap_url": "https://www.eatingwell.com/sitemap.xml",
        "enabled": True
    },
    {
        "name": "allrecipes", # ⚠️ 这是一个巨型站点，需要跑很久
        "sitemap_url": "https://www.allrecipes.com/sitemap.xml",
        "enabled": False
    }
]

MAX_WORKERS = 8  # 并发数
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

# --- 1. Sitemap 解析器 ---
def fetch_sitemap_urls(url):
    headers = {"User-Agent": USER_AGENT}
    urls = set()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if url.endswith('.gz'):
            content = gzip.decompress(response.content)
        else:
            content = response.content
        
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        if 'sitemapindex' in root.tag:
            for sm in root.findall('ns:sitemap', namespace):
                loc = sm.find('ns:loc', namespace).text
                urls.update(fetch_sitemap_urls(loc))
        elif 'urlset' in root.tag:
            for u in root.findall('ns:url', namespace):
                loc = u.find('ns:loc', namespace).text
                # 通用过滤: 包含 recipe 的链接
                if "/recipes/" in loc or "-recipe-" in loc or "/recipe/" in loc:
                    urls.add(loc)
    except Exception:
        pass
    return urls

# --- 2. 单个页面抓取 ---
def scrape_single_url(url):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        scraper = scrape_me(url)
        if not scraper.ingredients() or not scraper.instructions():
            return None
        
        recipe_id = hashlib.md5(url.encode()).hexdigest()
        return {
            "id": recipe_id,
            "title": scraper.title(),
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions_list(),
            "image_path": f"/recipe_images/{recipe_id}_hero.jpg",
            "source_url": url,
            "language": "en"
        }
    except Exception:
        return None

# --- 3. 核心执行逻辑 (自动路径版) ---
def run_spider_for_site(site_config):
    # 提取名字并转为小写，确保路径整洁
    raw_name = site_config['name']
    safe_name = raw_name.lower().replace(" ", "")
    
    sitemap = site_config['sitemap_url']
    
    # 🔥 自动构建路径逻辑
    # 文件夹: data/raw/simplyrecipes/
    output_dir = os.path.join("data", "raw", safe_name)
    # 文件名: eng_simplyrecipes_full.json
    output_filename = f"eng_{safe_name}_full.json"
    output_path = os.path.join(output_dir, output_filename)

    print(f"\n{'='*60}")
    print(f"🌍 任务: {raw_name}")
    print(f"📂 自动归档至: {output_path}")
    print(f"{'='*60}")

    # Step 1: 解析 Sitemap
    print(f"Step 1: 解析 Sitemap...")
    all_urls = list(fetch_sitemap_urls(sitemap))
    print(f"✅ 捕获到 {len(all_urls)} 个链接")

    if not all_urls:
        return

    # Step 2: 断点续传检查
    existing_ids = set()
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    existing_ids.add(item['id'])
            print(f"💡 发现旧数据，跳过 {len(existing_ids)} 条。")
        except:
            pass

    urls_to_scrape = [url for url in all_urls if hashlib.md5(url.encode()).hexdigest() not in existing_ids]
    
    print(f"📌 实际需抓: {len(urls_to_scrape)} 条")
    if not urls_to_scrape:
        print(f"🎉 数据已最新！")
        return

    # Step 3: 并发抓取
    valid_recipes = []
    # 加载旧数据以追加
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                valid_recipes = json.load(f)
        except:
            pass

    print(f"Step 2: 启动抓取...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(scrape_single_url, url): url for url in urls_to_scrape}
        
        pbar = tqdm(as_completed(future_to_url), total=len(urls_to_scrape), unit="url", desc=f"🕷️ {raw_name}")
        
        batch_count = 0
        for future in pbar:
            result = future.result()
            if result:
                valid_recipes.append(result)
                batch_count += 1
                
                # 每 100 条存一次
                if batch_count % 100 == 0:
                    os.makedirs(output_dir, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(valid_recipes, f, ensure_ascii=False, indent=2)

    # 最终保存
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_recipes, f, ensure_ascii=False, indent=2)
    
    print(f"🎉 {raw_name} 完成！共 {len(valid_recipes)} 条。")

# --- 主程序 ---
def main():
    print(f"🚀 AIChef 自动归档爬虫启动")
    for site in TARGET_SITES:
        if site['enabled']:
            try:
                run_spider_for_site(site)
            except Exception as e:
                print(f"❌ {site['name']} 出错: {e}")
        else:
            print(f"⏭️  跳过 {site['name']}")

if __name__ == "__main__":
    main()