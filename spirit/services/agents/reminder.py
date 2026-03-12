from typing import List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from spirit.db.models import User, ReviewConfig, ReviewPeriod, Thought


class ReminderAgent:
    """
    提醒Agent：负责定期回顾和思考引导
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def calculate_next_review(self, config: ReviewConfig) -> datetime:
        """计算下次回顾时间"""
        
        now = datetime.utcnow()
        
        if config.period == ReviewPeriod.DAILY:
            next_review = now.replace(hour=config.hour, minute=config.minute, second=0, microsecond=0)
            if next_review <= now:
                next_review += timedelta(days=1)
        
        elif config.period == ReviewPeriod.WEEKLY:
            days_until = (config.day_of_week - now.weekday()) % 7
            if days_until == 0 and now.hour >= config.hour:
                days_until = 7
            next_review = now + timedelta(days=days_until)
            next_review = next_review.replace(hour=config.hour, minute=config.minute, second=0, microsecond=0)
        
        elif config.period == ReviewPeriod.MONTHLY:
            if config.day_of_month:
                day = config.day_of_month
            else:
                day = now.day
            
            next_review = now.replace(day=day, hour=config.hour, minute=config.minute, second=0, microsecond=0)
            
            if next_review <= now:
                if now.month == 12:
                    next_review = next_review.replace(year=now.year+1, month=1)
                else:
                    next_review = next_review.replace(month=now.month+1)
        else:
            next_review = now + timedelta(days=7)
        
        return next_review
    
    async def get_due_reviews(self, db: AsyncSession) -> List[ReviewConfig]:
        """获取到期的回顾任务"""
        
        now = datetime.utcnow()
        
        result = await db.execute(
            select(ReviewConfig).where(
                and_(
                    ReviewConfig.is_active == True,
                    ReviewConfig.next_review_at <= now
                )
            )
        )
        
        return result.scalars().all()
    
    async def process_review(self, config: ReviewConfig, db: AsyncSession) -> dict:
        """处理回顾任务"""
        
        user_id = config.user_id
        period = config.period.value
        
        period_start, period_end = self._get_period_range(period)
        
        thoughts_result = await db.execute(
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
        
        config.last_reviewed_at = datetime.utcnow()
        config.next_review_at = self.calculate_next_review(config)
        
        await db.commit()
        
        return {
            "user_id": user_id,
            "period": period,
            "thoughts_count": len(thoughts),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }
    
    def _get_period_range(self, period: str) -> tuple[datetime, datetime]:
        """获取周期范围"""
        
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
            period_start = now - timedelta(weeks=1)
            period_end = now
        
        return period_start, period_end
    
    async def generate_review_questions(self, db: AsyncSession, user_id: int) -> List[str]:
        """生成回顾引导问题"""
        
        from spirit.services.agents.analyzer import AnalyzerAgent
        
        analyzer = AnalyzerAgent(db)
        analytics = await analyzer.get_analytics(user_id)
        
        questions = [
            "今天/本周你最想记录的是什么？",
            "有哪些想法想要进一步探索？",
            "有什么问题一直在脑海中萦绕？"
        ]
        
        if analytics.get("thoughts_by_category"):
            categories = analytics["thoughts_by_category"]
            if categories.get("question", 0) > categories.get("insight", 0):
                questions.append("你最近有什么想要解答的问题？")
            if categories.get("plan", 0) > 0:
                questions.append("你的计划执行得如何？")
        
        return questions
    
    async def generate_thinking_prompt(self, db: AsyncSession, user_id: int) -> str:
        """生成思考提示"""
        
        from spirit.services.agents.analyzer import AnalyzerAgent
        from spirit.services.agents.content_organizer import ContentOrganizerAgent
        
        analyzer = AnalyzerAgent(db)
        analytics = await analyzer.get_analytics(user_id)
        
        prompts = [
            "今天你有什么新想法？",
            "有什么事情让你有感而发？",
            "有没有想要记录的问题？"
        ]
        
        patterns = analytics.get("cognitive_patterns", [])
        
        for pattern in patterns:
            if pattern.get("type") == "inquisitive":
                prompts.append("你最近在思考什么问题？")
                break
        
        import random
        return random.choice(prompts)
    
    def start_scheduler(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
    
    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
    
    async def schedule_review(self, config: ReviewConfig):
        """安排回顾任务"""
        
        job_id = f"review_{config.id}"
        
        trigger = self._create_trigger(config)
        
        self.scheduler.add_job(
            self._run_review_job,
            trigger=trigger,
            args=[config.id],
            id=job_id,
            replace_existing=True
        )
    
    def _create_trigger(self, config: ReviewConfig):
        """创建触发器"""
        
        if config.period == ReviewPeriod.DAILY:
            return CronTrigger(
                hour=config.hour,
                minute=config.minute
            )
        elif config.period == ReviewPeriod.WEEKLY:
            return CronTrigger(
                day_of_week=config.day_of_week,
                hour=config.hour,
                minute=config.minute
            )
        elif config.period == ReviewPeriod.MONTHLY:
            return CronTrigger(
                day=config.day_of_month,
                hour=config.hour,
                minute=config.minute
            )
        
        return IntervalTrigger(days=7)
    
    async def _run_review_job(self, config_id: int):
        """执行回顾任务"""
        
        from spirit.db.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ReviewConfig).where(ReviewConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            
            if config and config.is_active:
                await self.process_review(config, db)
