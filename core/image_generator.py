import os
import uuid
import requests
from datetime import datetime
from openai import OpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_IMG_NAME

class ImageGenerator:
    def __init__(self):
        # 初始化客户端
        self.client = None
        if LLM_API_KEY:
            self.client = OpenAI(
                api_key=LLM_API_KEY,
                base_url=LLM_BASE_URL
            )
        self.model = LLM_MODEL_IMG_NAME

        # 1. 定义图片保存位置 (项目根目录/static/images)
        # 获取当前文件 (core/image_generator.py) 的上一级 (core) 的上一级 (根目录)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_dir = os.path.join(project_root, "static", "images")
        
        # 如果目录不存在，自动创建
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"📂 [Image] 已创建图片存储目录: {self.save_dir}")

    def generate(self, title, ingredients):
        """
        生成图片并下载到本地，返回本地文件路径
        """
        if not self.client:
            print("❌ Error: API Key 未配置")
            return None

        # 数据清洗
        if isinstance(ingredients, str): ingredients = [ingredients]
        if not ingredients: ingredients = ["food"]

        # 构建 Prompt
        ingredients_text = ", ".join(ingredients[:3])
        prompt = (
            f"Professional food photography of {title}, featuring {ingredients_text}. "
            f"Close-up, high resolution, Michelin star style, appetizing, cinematic lighting, 1080p."
        )
        
        print(f"🎨 [DALL-E] 正在绘制: {title}...")
        
        try:
            # 2. 调用 API 获取 URL
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1024x1024",
                n=1,
            )
            image_url = response.data[0].url
            
            # 3. 生成唯一文件名 (时间戳 + 随机ID)
            # 例如: 20260202_a1b2c3d4.png
            file_name = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.png"
            local_file_path = os.path.join(self.save_dir, file_name)

            # 4. 执行下载
            if self.download_to_local(image_url, local_file_path):
                # 下载成功！返回相对路径 (方便前端使用)
                # Windows/Mac 路径分隔符处理
                relative_path = f"static/images/{file_name}"
                print(f"💾 [Image] 图片已保存: {relative_path}")
                return relative_path
            else:
                # 下载失败，兜底返回 URL
                return image_url
            
        except Exception as e:
            print(f"❌ 生图/下载失败: {e}")
            return None

    def download_to_local(self, url, save_path):
        """
        下载辅助函数 (增强版：增加重试和更长的超时)
        """
        import time # 记得在文件开头确保引入了 time

        # 尝试下载 3 次
        for attempt in range(1, 4):
            try:
                print(f"⬇️ [Image] 正在下载图片 (第 {attempt} 次尝试)...")
                
                # 伪装一下 User-Agent (有些图片服务器会拒绝纯 Python 脚本请求)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                # 🔥 关键修改：将 timeout 从 30 改为 60 秒
                # stream=True 可以更稳定地下载大文件
                resp = requests.get(url, headers=headers, timeout=60, stream=True)
                
                if resp.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in resp.iter_content(1024):
                            f.write(chunk)
                    return True # 下载成功，直接返回
                else:
                    print(f"⚠️ 下载失败，状态码: {resp.status_code}")
                    
            except Exception as e:
                print(f"⚠️ 第 {attempt} 次下载出现异常: {e}")
                time.sleep(1) # 歇一秒再试
        
        print("❌ [Image] 重试 3 次后依然下载失败，将使用原始链接。")
        return False