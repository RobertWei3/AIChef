import requests
from openai import OpenAI
# 直接从 config 导入配置，确保统一性
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
        # 指定模型 (从 config 读取)
        self.model = LLM_MODEL_IMG_NAME

    def generate(self, title, ingredients):
        """
        统一接口：根据菜名和食材自动构建 Prompt 并生成图片
        """
        if not self.client:
            print("❌ Error: API Key 未配置")
            return None

        # 1. 自动构建 Prompt (提示词)
        # 提取前3个食材，构建英文 Prompt 以获得最佳效果
        ingredients_text = ", ".join(ingredients[:3])
        prompt = (
            f"Professional food photography of {title}, featuring {ingredients_text}. "
            f"Close-up, high resolution, Michelin star style, appetizing, cinematic lighting, 8k."
        )
        
        print(f"🎨 [SiliconFlow] 正在生成: {title} (Model: {self.model})...")
        
        try:
            # 2. 调用 API
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="1024x1024",
                n=1,
            )
            # 返回图片 URL
            return response.data[0].url
            
        except Exception as e:
            print(f"❌ 生图失败: {e}")
            return None

    def download_to_local(self, url, save_path):
        """
        辅助函数：将 URL 图片下载到本地文件
        """
        try:
            # 设置 30秒超时，防止网络卡死
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                print(f"✅ 已保存: {save_path}")
                return True
        except Exception as e:
            print(f"❌ 下载保存失败: {e}")
        return False