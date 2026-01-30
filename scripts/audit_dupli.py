import json
import os
from collections import Counter

# 只检查这个最终文件
MASTER_FILE = "data/processed/eng_merge_recipes_master.json"

def main():
    print(f"🕵️‍♂️ 正在对成品进行最终质检: {MASTER_FILE} ...\n")
    
    if not os.path.exists(MASTER_FILE):
        print(f"❌ 错误: 找不到文件 {MASTER_FILE}")
        print("   请先运行 'scripts/merge_and_deduplicate.py' 生成它。")
        return

    try:
        with open(MASTER_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        total_count = len(data)
        print(f"📦 数据总量: {total_count} 条")

        if total_count == 0:
            print("⚠️ 警告: 文件是空的！")
            return

        # --- 1. 自我重复性检查 (Self-Duplication Check) ---
        # 理论上这里必须是 0，如果有数据，说明去重脚本没跑好
        seen_urls = set()
        seen_titles = set()
        url_dupes = 0
        
        for r in data:
            if r['source_url'] in seen_urls:
                url_dupes += 1
            seen_urls.add(r['source_url'])
            
            # 统计标题分布，方便看有没有太多重名的菜（虽然URL不同）
            seen_titles.add(r['title'])

        print("-" * 40)
        print(f"🔍 [重复性验证]")
        if url_dupes == 0:
            print(f"   ✅ URL 重复数: 0 (完美！数据是唯一的)")
        else:
            print(f"   ❌ URL 重复数: {url_dupes} (警告: 合并脚本可能未正确执行)")

        # --- 2. 字段完整性检查 (Completeness Check) ---
        print("-" * 40)
        print(f"🏥 [健康度验证]")
        missing_content = 0
        missing_image = 0
        
        for r in data:
            # 检查关键字段是否为空
            if not r.get('ingredients') or not r.get('instructions'):
                missing_content += 1
            # 检查图片 (这个阶段缺图是正常的，因为还没跑生图脚本)
            if not r.get('image_path') or "hero.jpg" not in r.get('image_path', ''):
                missing_image += 1

        if missing_content == 0:
            print(f"   ✅ 内容完整性: 100% (所有食谱都有食材和步骤)")
        else:
            print(f"   ⚠️ 内容残缺: {missing_content} 条 (建议从数据库中剔除)")

        print(f"   🖼️ 待补图片数: {missing_image} (请运行 batch_generate.py 修复)")

        # --- 3. 来源分布 (Source Distribution) ---
        print("-" * 40)
        print(f"📊 [来源分布]")
        # 统计 source_site 字段，如果没有该字段则标记为 'unknown'
        sources = [r.get('source_site', 'unknown') for r in data]
        counts = Counter(sources)
        
        for site, count in counts.items():
            print(f"   - {site:<15}: {count} 条")

        print("-" * 40)
        print("🎉 质检完成！")
        if url_dupes == 0 and missing_content == 0:
            print("🚀 结论: 数据非常健康，可以运行 'core/ingest.py' 入库了！")
        else:
            print("🛑 结论: 存在问题，建议重新检查合并逻辑。")

    except Exception as e:
        print(f"❌ 读取失败: {e}")

if __name__ == "__main__":
    main()