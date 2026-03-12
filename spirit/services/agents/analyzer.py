from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from spirit.db.models import (
    Thought, Insight, ReviewSummary, ReviewPeriod, ThoughtCategory
)
from spirit.core.config import settings
from spirit.services.llm import LLMService


class AnalyzerAgent:
    """
    分析Agent：负责认知模式识别和成长建议生成
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService() if settings.OPENAI_API_KEY else None
    
    async def generate_review_summary(
        self, 
        user_id: int, 
        period: str,
        force_regenerate: bool = False
    ) -> ReviewSummary:
        """生成回顾总结"""
        
        now = datetime.utcnow()
        
        if period == "daily":
            period_start = now - timedelta(days=1)
            period_end = now
        elif period == "weekly":
            period_start = now - timedelta(weeks=1)
            period_end = now
        elif period == "monthly":
            period_start = now - timedelta(days=30)
            period_end = now
        else:
            raise ValueError(f"Invalid period: {period}")
        
        existing = await self.db.execute(
            select(ReviewSummary).where(
                and_(
                    ReviewSummary.user_id == user_id,
                    ReviewSummary.period == ReviewPeriod(period),
                    ReviewSummary.period_start >= period_start,
                    ReviewSummary.period_end <= period_end
                )
            )
        )
        
        if existing.scalar_one_or_none() and not force_regenerate:
            return existing.scalar_one()
        
        thoughts_result = await self.db.execute(
            select(Thought).where(
                and_(
                    Thought.user_id == user_id,
                    Thought.created_at >= period_start,
                    Thought.created_at <= period_end,
                    Thought.is_archived == False
                )
            )
        )
        thoughts = thoughts_result.scalars().all()
        
        if not thoughts:
            summary = ReviewSummary(
                user_id=user_id,
                period=ReviewPeriod(period),
                period_start=period_start,
                period_end=period_end,
                summary="本周没有记录任何思考内容",
                highlights=[],
                insights=[],
                suggestions=["尝试每天记录一些思考，哪怕是很简短的想法"]
            )
            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)
            return summary
        
        category_count = defaultdict(int)
        for thought in thoughts:
            category_count[thought.category.value] += 1
        
        highlights = sorted(
            [{"category": k, "count": v} for k, v in category_count.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        insights = await self._analyze_thoughts(thoughts)
        
        suggestions = await self._generate_suggestions(thoughts, category_count)
        
        summary_text = await self._generate_summary_text(thoughts, category_count, period)
        
        if existing.scalar_one_or_none():
            db_summary = existing.scalar_one()
            db_summary.summary = summary_text
            db_summary.highlights = highlights
            db_summary.insights = insights
            db_summary.suggestions = suggestions
        else:
            db_summary = ReviewSummary(
                user_id=user_id,
                period=ReviewPeriod(period),
                period_start=period_start,
                period_end=period_end,
                summary=summary_text,
                highlights=highlights,
                insights=insights,
                suggestions=suggestions
            )
            self.db.add(db_summary)
        
        await self.db.commit()
        await self.db.refresh(db_summary)
        
        return db_summary
    
    async def _analyze_thoughts(self, thoughts: List[Thought]) -> List[str]:
        """分析思考内容，生成洞察"""
        
        insights = []
        
        if not self.llm_service:
            return insights
        
        content_list = [t.content[:200] for t in thoughts[:20]]
        combined_content = "\n\n".join(content_list)
        
        prompt = f"""分析以下思考记录，识别出2-4个重要的洞察：

{combined_content}

请列出这些洞察："""
        
        try:
            result = await self.llm_service.generate(prompt)
            insights = [line.strip() for line in result.split("\n") if line.strip()]
        except Exception as e:
            print(f"洞察生成失败: {e}")
        
        return insights[:4]
    
    async def _generate_suggestions(
        self, 
        thoughts: List[Thought],
        category_count: Dict[str, int]
    ) -> List[str]:
        """生成改进建议"""
        
        suggestions = []
        
        if len(thoughts) < 5:
            suggestions.append("尝试更频繁地记录思考，每天至少一条")
        
        category_weights = defaultdict(lambda: 0)
        total = sum(category_count.values())
        if total > 0:
            for cat, count in category_count.items():
                category_weights[cat] = count / total
        
        if category_weights.get("question", 0) < 0.1:
            suggestions.append("多问一些为什么，尝试从问题中发现新的思考方向")
        
        if category_weights.get("reflection", 0) < 0.05:
            suggestions.append("增加反思性思考，定期回顾自己的行为和决策")
        
        if category_weights.get("plan", 0) < 0.1:
            suggestions.append("将一些想法转化为具体的计划")
        
        if len(thoughts) > 0:
            thought_texts = [t.content for t in thoughts]
            all_text = " ".join(thought_texts)
            avg_length = sum(len(t) for t in thought_texts) / len(thought_texts)
            
            if avg_length < 50:
                suggestions.append("尝试更详细地描述你的思考过程")
        
        return suggestions[:4]
    
    async def _generate_summary_text(
        self, 
        thoughts: List[Thought],
        category_count: Dict[str, int],
        period: str
    ) -> str:
        """生成总结文本"""
        
        period_name = {"daily": "今天", "weekly": "本周", "monthly": "本月"}[period]
        
        summary = f"{period_name}你共记录了 {len(thoughts)} 条思考。"
        
        category_names = {
            "idea": "想法",
            "question": "问题",
            "insight": "感悟",
            "plan": "计划",
            "reflection": "反思",
            "note": "笔记",
            "diary": "日记"
        }
        
        if category_count:
            top_categories = sorted(
                category_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            cat_strs = [
                f"{category_names.get(cat, cat)} {count}条"
                for cat, count in top_categories
            ]
            summary += f" 主要集中在：{', '.join(cat_strs)}。"
        
        return summary
    
    async def get_analytics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """获取用户分析数据"""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        query = select(Thought).where(
            and_(
                Thought.user_id == user_id,
                Thought.created_at >= start_date,
                Thought.created_at <= end_date,
                Thought.is_archived == False
            )
        )
        
        result = await self.db.execute(query)
        thoughts = result.scalars().all()
        
        total_thoughts = len(thoughts)
        
        thoughts_by_category = defaultdict(int)
        thoughts_by_source = defaultdict(int)
        daily_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        
        for thought in thoughts:
            thoughts_by_category[thought.category.value] += 1
            thoughts_by_source[thought.source.value] += 1
            
            date_key = thought.created_at.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1
            
            if thought.tags:
                for tag in thought.tags:
                    tag_counts[tag] += 1
        
        daily_thoughts_count = [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items())
        ]
        
        top_tags = sorted(
            [{"tag": tag, "count": count} for tag, count in tag_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        cognitive_patterns = await self._analyze_cognitive_patterns(thoughts)
        
        return {
            "total_thoughts": total_thoughts,
            "thoughts_by_category": dict(thoughts_by_category),
            "thoughts_by_source": dict(thoughts_by_source),
            "daily_thoughts_count": daily_thoughts_count,
            "top_tags": top_tags,
            "cognitive_patterns": cognitive_patterns
        }
    
    async def _analyze_cognitive_patterns(self, thoughts: List[Thought]) -> List[Dict]:
        """分析认知模式"""
        
        patterns = []
        
        if not thoughts:
            return patterns
        
        thought_texts = [t.content for t in thoughts]
        
        total_words = sum(len(t.split()) for t in thought_texts)
        if total_words > 0:
            avg_words = total_words / len(thought_texts)
            
            if avg_words < 30:
                patterns.append({
                    "type": "brevity",
                    "title": "简洁思考者",
                    "description": "你的思考通常比较简洁，这可能意味着你善于快速捕捉要点"
                })
            elif avg_words > 200:
                patterns.append({
                    "type": "detailed",
                    "title": "深入思考者",
                    "description": "你倾向于深入分析问题，这是很好的思考习惯"
                })
        
        question_count = sum(1 for t in thoughts if "？" in t.content or "?" in t.content)
        if question_count / len(thoughts) > 0.3:
            patterns.append({
                "type": "inquisitive",
                "title": "好奇探索者",
                "description": "你经常提出问题，这种好奇心是成长的动力"
            })
        
        plan_count = sum(1 for t in thoughts if t.category == ThoughtCategory.plan)
        if plan_count / len(thoughts) > 0.2:
            patterns.append({
                "type": "action_oriented",
                "title": "行动导向",
                "description": "你有很多计划，注意确保它们能够执行"
            })
        
        return patterns
