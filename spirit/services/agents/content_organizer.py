from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from spirit.db.models import (
    Thought, ThoughtExpansion, ThoughtRelation, ThoughtCategory, 
    UserCategory, Insight
)
from spirit.core.config import settings
from spirit.services.llm import LLMService


class ContentOrganizerAgent:
    """
    内容组织Agent：负责内容分类、关联和结构化存储
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService() if settings.OPENAI_API_KEY else None
    
    async def expand_thought(
        self, 
        thought: Thought, 
        expansion_types: List[str]
    ) -> List[ThoughtExpansion]:
        """展开思考内容，提供相关扩展"""
        
        expansions = []
        
        if self.llm_service:
            for expansion_type in expansion_types:
                content = await self._generate_expansion(thought.content, expansion_type)
                
                if content:
                    expansion = ThoughtExpansion(
                        thought_id=thought.id,
                        expansion_type=expansion_type,
                        content=content
                    )
                    self.db.add(expansion)
                    expansions.append(expansion)
        
        await self.db.commit()
        
        return expansions
    
    async def _generate_expansion(self, content: str, expansion_type: str) -> Optional[str]:
        """使用LLM生成扩展内容"""
        
        if not self.llm_service:
            return None
        
        prompts = {
            "question_extension": f"""基于以下思考内容，提出3-5个深入的问题来帮助你进一步思考：

{content}

请列出这些问题：""",
            
            "related_idea": f"""基于以下思考内容，提供3-5个相关的想法或观点：

{content}

请列出这些想法：""",
            
            "supplement_info": f"""基于以下思考内容，提供一些补充信息和背景知识：

{content}

请提供相关信息：""",
            
            "alternative_perspective": f"""从另一个角度思考以下内容：

{content}

请提供不同的视角：""",
            
            "action_suggestion": f"""基于以下思考内容，提供具体的行动建议：

{content}

请列出行动建议："""
        }
        
        prompt = prompts.get(expansion_type)
        if not prompt:
            return None
        
        try:
            result = await self.llm_service.generate(prompt)
            return result
        except Exception as e:
            print(f"生成扩展失败: {e}")
            return None
    
    async def find_related_thoughts(
        self, 
        thought: Thought, 
        limit: int = 5
    ) -> List[Thought]:
        """查找相关的思考内容"""
        
        content_words = set(thought.content.lower().split())
        
        if thought.tags:
            content_words.update([tag.lower() for tag in thought.tags])
        
        result = await self.db.execute(
            select(Thought)
            .where(
                and_(
                    Thought.user_id == thought.user_id,
                    Thought.id != thought.id,
                    Thought.is_archived == False
                )
            )
            .order_by(Thought.created_at.desc())
            .limit(100)
        )
        all_thoughts = result.scalars().all()
        
        related = []
        for t in all_thoughts:
            if t.id == thought.id:
                continue
            
            score = 0
            
            t_words = set(t.content.lower().split())
            score += len(content_words & t_words)
            
            if thought.tags and t.tags:
                score += len(set(thought.tags) & set(t.tags)) * 2
            
            if thought.category == t.category:
                score += 3
            
            days_diff = abs((thought.created_at - t.created_at).days)
            if days_diff < 7:
                score += 2
            elif days_diff < 30:
                score += 1
            
            if score > 3:
                related.append((t, score))
        
        related.sort(key=lambda x: x[1], reverse=True)
        
        return [t for t, score in related[:limit]]
    
    async def create_thought_relations(
        self, 
        thought: Thought
    ) -> List[ThoughtRelation]:
        """为思考内容创建关联关系"""
        
        related_thoughts = await self.find_related_thoughts(thought)
        relations = []
        
        for related in related_thoughts:
            existing = await self.db.execute(
                select(ThoughtRelation).where(
                    or_(
                        and_(
                            ThoughtRelation.thought_id == thought.id,
                            ThoughtRelation.related_thought_id == related.id
                        ),
                        and_(
                            ThoughtRelation.thought_id == related.id,
                            ThoughtRelation.related_thought_id == thought.id
                        )
                    )
                )
            )
            
            if not existing.scalar_one_or_none():
                relation = ThoughtRelation(
                    thought_id=thought.id,
                    related_thought_id=related.id,
                    relation_type="related"
                )
                self.db.add(relation)
                relations.append(relation)
        
        if relations:
            await self.db.commit()
        
        return relations
    
    async def auto_categorize(self, thought: Thought) -> Optional[int]:
        """自动分类思考内容"""
        
        if thought.category_id:
            return thought.category_id
        
        user_categories = await self.db.execute(
            select(UserCategory).where(UserCategory.user_id == thought.user_id)
        )
        categories = user_categories.scalars().all()
        
        if not categories:
            return None
        
        category_keywords = {
            "工作": ["工作", "项目", "任务", "会议", "客户", "同事"],
            "学习": ["学习", "读书", "课程", "知识", "技能", "考试"],
            "生活": ["生活", "家庭", "朋友", "健康", "运动", "饮食"],
            "财务": ["钱", "投资", "理财", "收入", "支出", "预算"],
            "成长": ["成长", "目标", "计划", "习惯", "反思", "总结"]
        }
        
        content_lower = thought.content.lower()
        
        for category in categories:
            keywords = category_keywords.get(category.name, [category.name])
            for keyword in keywords:
                if keyword in content_lower:
                    return category.id
        
        return None
    
    async def extract_entities(self, content: str) -> Dict[str, List[str]]:
        """提取内容中的实体"""
        
        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "topics": []
        }
        
        if not self.llm_service:
            return entities
        
        prompt = f"""从以下文本中提取实体：

{content}

请以JSON格式返回，包含以下键：people（人物）、organizations（组织）、locations（地点）、topics（主题）"""
        
        try:
            import json
            result = await self.llm_service.generate(prompt)
            data = json.loads(result)
            
            for key in entities:
                if key in data:
                    entities[key] = data[key]
        
        except Exception as e:
            print(f"实体提取失败: {e}")
        
        return entities
