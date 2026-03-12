from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from spirit.db.database import get_db
from spirit.db.models import (
    User, Thought, ThoughtExpansion, UserCategory, ThoughtCategory, 
    ReviewConfig, ReviewSummary, Insight, Feedback, ThoughtRelation
)
from spirit.schemas import (
    ThoughtCreate, ThoughtResponse, ThoughtUpdate, ThoughtDetailResponse,
    ThoughtExpansionResponse, CategoryCreate, CategoryResponse, CategoryUpdate,
    ReviewConfigCreate, ReviewConfigResponse, ReviewConfigUpdate,
    ReviewSummaryResponse, InsightResponse, FeedbackCreate, FeedbackResponse,
    ExpandThoughtRequest, ExpandThoughtResponse, AnalyticsResponse,
    ReviewSummaryRequest, UserResponse, UserUpdate
)
from spirit.dependencies import get_current_user
from spirit.utils import parse_thought_category, extract_tags, sanitize_content
from spirit.services.agents import InputHandlerAgent, ContentOrganizerAgent

router = APIRouter(prefix="/api/v1", tags=["thoughts"])


@router.post("/thoughts", response_model=ThoughtResponse, status_code=status.HTTP_201_CREATED)
async def create_thought(
    thought: ThoughtCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = sanitize_content(thought.content)
    
    if not thought.category:
        category = parse_thought_category(content)
    else:
        category = thought.category
    
    tags = thought.tags or []
    if not tags:
        tags = extract_tags(content)
    
    db_thought = Thought(
        user_id=current_user.id,
        content=content,
        raw_content=content,
        category=ThoughtCategory(category),
        title=thought.title,
        tags=tags,
        source=thought.source,
        category_id=thought.category_id,
        thinking_started_at=datetime.utcnow()
    )
    
    db.add(db_thought)
    await db.flush()
    
    input_agent = InputHandlerAgent(db)
    await input_agent.process_thought(db_thought)
    
    await db.commit()
    await db.refresh(db_thought)
    
    return db_thought


@router.get("/thoughts", response_model=List[ThoughtResponse])
async def list_thoughts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Thought).where(Thought.user_id == current_user.id)
    
    if category:
        query = query.where(Thought.category == ThoughtCategory(category))
    if is_favorite is not None:
        query = query.where(Thought.is_favorite == is_favorite)
    if is_archived is not None:
        query = query.where(Thought.is_archived == is_archived)
    if start_date:
        query = query.where(Thought.created_at >= start_date)
    if end_date:
        query = query.where(Thought.created_at <= end_date)
    if search:
        query = query.where(Thought.content.ilike(f"%{search}%"))
    
    query = query.order_by(Thought.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/thoughts/{thought_id}", response_model=ThoughtDetailResponse)
async def get_thought(
    thought_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought)
        .options(selectinload(Thought.expansions))
        .options(selectinload(Thought.related_thoughts).selectinload(ThoughtRelation.related))
        .where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    thought = result.scalar_one_or_none()
    
    if not thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    return thought


@router.put("/thoughts/{thought_id}", response_model=ThoughtResponse)
async def update_thought(
    thought_id: int,
    thought_update: ThoughtUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought).where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    db_thought = result.scalar_one_or_none()
    
    if not db_thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    update_data = thought_update.model_dump(exclude_unset=True)
    
    if "content" in update_data:
        update_data["content"] = sanitize_content(update_data["content"])
        update_data["raw_content"] = update_data["content"]
    
    if "category" in update_data and update_data["category"]:
        update_data["category"] = ThoughtCategory(update_data["category"])
    
    if "tags" not in update_data or update_data["tags"] is None:
        if "content" in update_data:
            update_data["tags"] = extract_tags(update_data["content"])
    
    for key, value in update_data.items():
        setattr(db_thought, key, value)
    
    db_thought.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_thought)
    
    return db_thought


@router.delete("/thoughts/{thought_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thought(
    thought_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought).where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    thought = result.scalar_one_or_none()
    
    if not thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    await db.delete(thought)
    await db.commit()
    
    return None


@router.post("/thoughts/{thought_id}/expand", response_model=ExpandThoughtResponse)
async def expand_thought(
    thought_id: int,
    request: ExpandThoughtRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought).where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    thought = result.scalar_one_or_none()
    
    if not thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    organizer_agent = ContentOrganizerAgent(db)
    expansions = await organizer_agent.expand_thought(thought, request.expansion_types)
    
    return ExpandThoughtResponse(thought_id=thought_id, expansions=expansions)


@router.post("/thoughts/{thought_id}/favorite", response_model=ThoughtResponse)
async def toggle_favorite(
    thought_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought).where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    thought = result.scalar_one_or_none()
    
    if not thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    thought.is_favorite = not thought.is_favorite
    await db.commit()
    await db.refresh(thought)
    
    return thought


@router.post("/thoughts/{thought_id}/archive", response_model=ThoughtResponse)
async def toggle_archive(
    thought_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Thought).where(and_(
            Thought.id == thought_id,
            Thought.user_id == current_user.id
        ))
    )
    thought = result.scalar_one_or_none()
    
    if not thought:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    
    thought.is_archived = not thought.is_archived
    await db.commit()
    await db.refresh(thought)
    
    return thought
