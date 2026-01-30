import sys
import os

# 1. 确保能导入 core 模块
# 将项目根目录添加到 python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.image_generator import ImageGenerator

def test_single():
    print("🚀 正在初始化 ImageGenerator...")
    generator = ImageGenerator()
    
    # 2. 准备一个测试用例
    # 你可以随意修改这里的菜名和食材
    test_title = "宫保鸡丁"
    test_ingredients = ["鸡胸肉", "花生", "干辣椒", "葱"]
    
    print(f"\n🧪 开始测试生成: {test_title}")
    print(f"   食材: {test_ingredients}")

    # 3. 调用生成接口
    # 这一步会消耗额度，但只是一次
    img_url = generator.generate(test_title, test_ingredients)
    
    if img_url:
        print("\n🎉 [生成成功!]")
        print(f"🔗 图片链接 (点击查看): {img_url}")
        
        # 4. 测试下载保存 (可选)
        # 如果你想验证能否存到本地，可以取消下面代码的注释
        save_dir = "frontend/public/recipe_images"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        save_path = os.path.join(save_dir, "test_kung_pao.jpg")
        print(f"\n💾 正在尝试保存到: {save_path} ...")
        
        success = generator.download_to_local(img_url, save_path)
        if success:
            print("✅ 保存成功！请去文件夹查看图片质量。")
        else:
            print("❌ 保存失败。")
            
    else:
        print("\n❌ 生成失败，请检查 API Key 或网络。")

if __name__ == "__main__":
    test_single()