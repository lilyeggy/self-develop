from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from spirit.db.database import get_db
from spirit.db.models import User, ReviewConfig, ReviewSummary, ReviewPeriod
from spirit.schemas import (
    UserCreate, UserResponse, UserUpdate, Token,
    ReviewConfigCreate, ReviewConfigResponse, ReviewConfigUpdate,
    ReviewSummaryResponse, ReviewSummaryRequest
)
from spirit.dependencies import get_current_user
from spirit.utils import get_password_hash, create_access_token
from spirit.services.agents import ReminderAgent, AnalyzerAgent

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(or_(
            User.username == user_data.username,
            User.email == user_data.email
        ))
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被注册"
        )
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    default_category = UserCategory(
        user_id=db_user.id,
        name="默认",
        color="#6366f1"
    )
    db.add(default_category)
    await db.commit()
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=60*24*7)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_update.username:
        result = await db.execute(
            select(User).where(
                and_(
                    User.username == user_update.username,
                    User.id != current_user.id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已被使用")
        current_user.username = user_update.username
    
    if user_update.email:
        result = await db.execute(
            select(User).where(
                and_(
                    User.email == user_update.email,
                    User.id != current_user.id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        current_user.email = user_update.email
    
    if user_update.preferences:
        current_user.preferences = user_update.preferences
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/review/configs", response_model=ReviewConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_review_config(
    config: ReviewConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = ReviewConfig(
        user_id=current_user.id,
        period=ReviewPeriod(config.period),
        day_of_week=config.day_of_week,
        day_of_month=config.day_of_month,
        hour=config.hour,
        minute=config.minute
    )
    
    reminder_agent = ReminderAgent()
    db_config.next_review_at = reminder_agent.calculate_next_review(db_config)
    
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    
    return db_config


@router.get("/review/configs", response_model=list[ReviewConfigResponse])
async def list_review_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ReviewConfig).where(ReviewConfig.user_id == current_user.id)
    )
    return result.scalars().all()


@router.put("/review/configs/{config_id}", response_model=ReviewConfigResponse)
async def update_review_config(
    config_id: int,
    config_update: ReviewConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ReviewConfig).where(and_(
            ReviewConfig.id == config_id,
            ReviewConfig.user_id == current_user.id
        ))
    )
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="回顾配置不存在")
    
    update_data = config_update.model_dump(exclude_unset=True)
    
    if "period" in update_data:
        update_data["period"] = ReviewPeriod(update_data["period"])
    
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    if any(k in update_data for k in ["period", "day_of_week", "day_of_month", "hour", "minute"]):
        reminder_agent = ReminderAgent()
        db_config.next_review_at = reminder_agent.calculate_next_review(db_config)
    
    await db.commit()
    await db.refresh(db_config)
    
    return db_config


@router.delete("/review/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ReviewConfig).where(and_(
            ReviewConfig.id == config_id,
            ReviewConfig.user_id == current_user.id
        ))
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="回顾配置不存在")
    
    await db.delete(config)
    await db.commit()
    
    return None


@router.get("/review/summaries", response_model=list[ReviewSummaryResponse])
async def list_review_summaries(
    period: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(ReviewSummary).where(ReviewSummary.user_id == current_user.id)
    
    if period:
        query = query.where(ReviewSummary.period == ReviewPeriod(period))
    
    query = query.order_by(ReviewSummary.period_end.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/review/generate", response_model=ReviewSummaryResponse)
async def generate_review_summary(
    request: ReviewSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analyzer_agent = AnalyzerAgent(db)
    summary = await analyzer_agent.generate_review_summary(
        current_user.id,
        request.period,
        request.force_regenerate
    )
    
    return summary


@router.get("/analytics", response_model=dict)
async def get_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from spirit.schemas import AnalyticsResponse
    
    analyzer_agent = AnalyzerAgent(db)
    analytics = await analyzer_agent.get_analytics(
        current_user.id,
        start_date,
        end_date
    )
    
    return analytics


from sqlalchemy import or_
from spirit.db.models import UserCategory
from spirit.utils import verify_password
