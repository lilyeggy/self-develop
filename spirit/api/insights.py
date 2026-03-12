from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from spirit.db.database import get_db
from spirit.db.models import User, Insight, Feedback
from spirit.schemas import InsightResponse, FeedbackCreate, FeedbackResponse
from spirit.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["insights"])


@router.get("/", response_model=List[InsightResponse])
async def list_insights(
    insight_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Insight).where(Insight.user_id == current_user.id)
    
    if insight_type:
        query = query.where(Insight.insight_type == insight_type)
    
    query = query.order_by(Insight.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Insight).where(and_(
            Insight.id == insight_id,
            Insight.user_id == current_user.id
        ))
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(status_code=404, detail="洞察不存在")
    
    return insight


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_feedback = Feedback(
        user_id=current_user.id,
        feedback_type=feedback.feedback_type,
        target_id=feedback.target_id,
        target_type=feedback.target_type,
        rating=feedback.rating,
        comment=feedback.comment
    )
    
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    
    return db_feedback
