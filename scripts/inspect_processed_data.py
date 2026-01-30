import json
import random
from collections import Counter

# 你的 Master 文件路径
FILE_PATH = "data/processed/eng_merge_recipes_master.json"

def inspect_data():
    try:
        print(f"🕵️‍♂️ 正在读取: {FILE_PATH} ...")
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        total_count = len(data)
        print(f"✅ 文件读取成功！总共有 {total_count} 条食谱。\n")
        
        if total_count == 0:
            print("❌ 数据为空，请检查合并脚本！")
            return

        # --- 1. 来源分布检查 ---
        # 看看是不是所有网站的数据都进来了
        print("📊 [来源分布] (Source Breakdown):")
        sources = [item.get('source_site', 'unknown') for item in data]
        source_counts = Counter(sources)
        for site, count in source_counts.items():
            print(f"   - {site}: {count} 条 ({count/total_count*100:.1f}%)")
        
        # --- 2. 字段完整性检查 ---
        # 看看有没有缺胳膊少腿的数据
        print("\n🏥 [健康度检查] (Health Check):")
        missing_title = sum(1 for item in data if not item.get('title'))
        missing_ing = sum(1 for item in data if not item.get('ingredients'))
        missing_steps = sum(1 for item in data if not item.get('instructions'))
        missing_img = sum(1 for item in data if not item.get('image_path'))
        
        print(f"   - 缺少标题: {missing_title}")
        print(f"   - 缺少食材: {missing_ing}")
        print(f"   - 缺少步骤: {missing_steps}")
        print(f"   - 缺少图片路径: {missing_img} (正常，稍后会生成)")

        # --- 3. 随机抽样展示 ---
        # 随机抽一条看看具体长什么样
        print("\n🎲 [随机抽样] (Random Sample):")
        sample = random.choice(data)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {FILE_PATH}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    inspect_data()