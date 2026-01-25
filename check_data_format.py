import json
import os

def check_file(file_path):
    print(f"\n🔍 正在检查: {file_path}")
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("❌ 格式错误：根节点必须是一个列表 (List)")
        return

    print(f"📄 数据条数: {len(data)}")
    
    errors = []
    
    # 抽查前 5 条 + 最后 5 条
    samples = data[:5] + data[-5:] if len(data) > 10 else data
    
    for idx, item in enumerate(samples):
        # 1. 检查 metadata 嵌套
        if 'metadata' not in item:
            errors.append(f"第 {idx} 条: 缺少 'metadata' 键 (这是 Ingest.py 必须的)")
            continue
            
        meta = item['metadata']
        
        # 2. 检查关键字段
        required_fields = ['id', 'name', 'image', 'instructions']
        for field in required_fields:
            if field not in meta:
                errors.append(f"ID {meta.get('id', '未知')}: metadata 中缺少 '{field}'")

        # 3. 检查图片路径 (可选)
        img = meta.get('image', '')
        if img and not img.startswith('/recipe_images/'):
            # 这是一个警告，不是错误
            # errors.append(f"ID {meta.get('id')}: 图片路径似乎不是本地的 -> {img}")
            pass

    if errors:
        print(f"❌ 发现 {len(errors)} 个格式问题 (仅显示前3个):")
        for e in errors[:3]:
            print(f"  - {e}")
        print("结论：格式不兼容，Ingest 会报错。")
    else:
        print("✅ 格式检查通过！完美适配 Ingest.py。")

if __name__ == "__main__":
    # 在这里填入您的文件名
    check_file('data/recipe_rag_ready.json')              # 检查中文
    check_file('data/recipe_rag_ready_english.json')      # 检查英文