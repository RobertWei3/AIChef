import json
from typing import Optional
from .models import RecipeStep, RecipeResponse
from core.retriever import retrieve_docs
# ✅ 引入新的优选函数
from core.generator import smart_select_and_comment 

class RecipeService:
    def get_recipe_response(self, query: str) -> Optional[RecipeResponse]:
        print(f"🔍 [Service] 用户搜索: {query}")
        
        # 1. 【扩大召回】从数据库拿 Top 3，而不是 Top 1
        # 这样即使向量检索把最佳结果排在了第 2 或 第 3，AI 也能把它捞回来
        candidates = retrieve_docs(query, top_k=6)
        
        if not candidates:
            return None
        
        # 🔍 调试打印：看看数据库到底捞出了啥，到底有没有不辣的？
        print(f"👀 候选名单: {[c['name'] for c in candidates]}")
        
        # 2. 【AI 优选】让大模型来挑，并生成推荐语
        # 返回值: (选中的索引, 推荐语)
        selected_index, ai_message = smart_select_and_comment(query, candidates)
        
        # 确保索引不越界 (防止 AI 瞎返回 "index: 99")
        if selected_index < 0 or selected_index >= len(candidates):
            selected_index = 0
            
        # 3. 锁定最终的最佳菜谱
        best_match = candidates[selected_index]
        print(f"🎯 [Service] AI 选中了第 {selected_index} 项: {best_match['name']}")

        # --- 以下清洗逻辑不变 ---
        raw_instructions = best_match.get('instructions', [])
        if isinstance(raw_instructions, str):
            try: raw_instructions = json.loads(raw_instructions)
            except: raw_instructions = []

        raw_tags = best_match.get('tags', [])
        if isinstance(raw_tags, str):
            try: raw_tags = json.loads(raw_tags)
            except: raw_tags = []

        formatted_steps = []
        for idx, step in enumerate(raw_instructions):
            img_link = step.get('imgLink')
            if not img_link or img_link == "null": img_link = None
            formatted_steps.append(
                RecipeStep(
                    step_index=idx + 1,
                    description=step.get('description', ''),
                    image_url=img_link
                )
            )

        return RecipeResponse(
            recipe_id=str(best_match.get('id', 'unknown')),
            recipe_name=best_match.get('name', '未命名'),
            tags=raw_tags,
            cover_image=best_match.get('image'),
            steps=formatted_steps,
            message=ai_message # 这里是 AI 针对选中菜谱写的推荐语
        )

recipe_service = RecipeService()


# import json  # <--- 1. 必须补上这个！
# from typing import Optional
# from .models import RecipeStep, RecipeResponse

# # ✅ 直接引入你在 core 里写好的检索函数
# from core.retriever import retrieve_docs
# from core.generator import generate_rag_answer

# class RecipeService:
#     def get_recipe_response(self, query: str) -> Optional[RecipeResponse]:
#         """
#         业务逻辑：
#         1. 检索 (Retrieve) -> 拿到 raw data
#         2. 生成 (Generate) -> 拿到 AI 推荐语
#         3. 清洗 (Parse) -> 拿到结构化步骤
#         4. 组装返回
#         """
#         print(f"🔍 [Service] 正在为用户搜索: {query}")
        
#         # 1. 检索
#         results = retrieve_docs(query, top_k=1)
        
#         if not results:
#             print("⚠️ [Service] 未找到匹配结果")
#             return None
            
#         best_match = results[0]
        
#         # # =======================================================
#         # # ✅ 2. 数据清洗：从 JSON 字符串还原回 List
#         # # =======================================================
        
#         # # --- 处理 Instructions ---
#         # raw_instructions = best_match.get('instructions', [])
#         # # 如果它是字符串 (因为 Chroma 存成了 string)，我们需要把它转回 list
#         # if isinstance(raw_instructions, str):
#         #     try:
#         #         raw_instructions = json.loads(raw_instructions)
#         #     except json.JSONDecodeError:
#         #         print("❌ 解析 instructions JSON 失败，使用空列表")
#         #         raw_instructions = []

#         # # --- 处理 Tags ---
#         # raw_tags = best_match.get('tags', [])
#         # if isinstance(raw_tags, str):
#         #     try:
#         #         raw_tags = json.loads(raw_tags)
#         #     except json.JSONDecodeError:
#         #         raw_tags = []

#         # # 3. 格式化步骤 (组装 Steps)
#         # formatted_steps = []
#         # for idx, step in enumerate(raw_instructions):
#         #     # 处理图片链接
#         #     img_link = step.get('imgLink')
#         #     if not img_link or img_link == "null":
#         #         img_link = None

#         #     formatted_steps.append(
#         #         RecipeStep(
#         #             step_index=idx + 1,
#         #             description=step.get('description', ''),
#         #             image_url=img_link
#         #         )
#         #     )

#         # # 4. 返回标准结构
#         # return RecipeResponse(
#         #     recipe_id=str(best_match.get('id', 'unknown')),
#         #     recipe_name=best_match.get('name', '未命名菜谱'),
            
#         #     # <--- 2. 这里要用解析好的 raw_tags，而不是原始的 best_match['tags']
#         #     tags=raw_tags, 
            
#         #     cover_image=best_match.get('image'),
#         #     steps=formatted_steps,
#         #     message=f"✨ 为您找到【{best_match.get('name')}】的最佳做法："
#         # )
#         # 2. 【核心新增】调用大模型生成推荐语 (Generator) - 稍微花点时间
#         # 把 query (用户想吃啥) 和 results (库里有啥) 传给 AI
#         # 注意：这会增加 API 的延迟（通常 1-2 秒），取决于模型速度
#         ai_message = generate_rag_answer(query, results)
        
#         # 3. 数据清洗 (保持不变)
#         raw_instructions = best_match.get('instructions', [])
#         if isinstance(raw_instructions, str):
#             try:
#                 raw_instructions = json.loads(raw_instructions)
#             except:
#                 raw_instructions = []

#         raw_tags = best_match.get('tags', [])
#         if isinstance(raw_tags, str):
#             try:
#                 raw_tags = json.loads(raw_tags)
#             except:
#                 raw_tags = []

#         formatted_steps = []
#         for idx, step in enumerate(raw_instructions):
#             img_link = step.get('imgLink')
#             if not img_link or img_link == "null":
#                 img_link = None
#             formatted_steps.append(
#                 RecipeStep(
#                     step_index=idx + 1,
#                     description=step.get('description', ''),
#                     image_url=img_link
#                 )
#             )

#         # 4. 组装返回
#         return RecipeResponse(
#             recipe_id=str(best_match.get('id', 'unknown')),
#             recipe_name=best_match.get('name', '未命名'),
#             tags=raw_tags,
#             cover_image=best_match.get('image'),
#             steps=formatted_steps,
            
#             # ✅ 这里填入 AI 生成的话！
#             message=ai_message
#         )
# # 创建单例实例
# recipe_service = RecipeService()