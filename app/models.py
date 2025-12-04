from pydantic import BaseModel
from typing import List, Optional

# --- 请求模型 ---
class QueryRequest(BaseModel):
    query: str

# --- 响应模型 (完全对应前端 UI) ---

class RecipeStep(BaseModel):
    """单步详情：对应 UI 里的每一个步骤卡片"""
    step_index: int             # 步骤序号 (1, 2...)
    description: str            # 步骤文字
    image_url: Optional[str]    # 步骤图片 (可能为 None)

class RecipeResponse(BaseModel):
    recipe_id: str
    recipe_name: str
    tags: List[str]
    cover_image: Optional[str]
    steps: List[RecipeStep]
    message: str