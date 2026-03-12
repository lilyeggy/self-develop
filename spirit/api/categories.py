from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from spirit.db.database import get_db
from spirit.db.models import User, UserCategory, Thought
from spirit.schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from spirit.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if category.parent_id:
        result = await db.execute(
            select(UserCategory).where(and_(
                UserCategory.id == category.parent_id,
                UserCategory.user_id == current_user.id
            ))
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="父分类不存在")
    
    db_category = UserCategory(
        user_id=current_user.id,
        name=category.name,
        color=category.color,
        icon=category.icon,
        parent_id=category.parent_id
    )
    
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    
    return db_category


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(UserCategory).where(UserCategory.user_id == current_user.id)
    
    if parent_id is not None:
        query = query.where(UserCategory.parent_id == parent_id)
    else:
        query = query.where(UserCategory.parent_id == None)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserCategory).where(and_(
            UserCategory.id == category_id,
            UserCategory.user_id == current_user.id
        ))
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserCategory).where(and_(
            UserCategory.id == category_id,
            UserCategory.user_id == current_user.id
        ))
    )
    db_category = result.scalar_one_or_none()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    await db.commit()
    await db.refresh(db_category)
    
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserCategory).where(and_(
            UserCategory.id == category_id,
            UserCategory.user_id == current_user.id
        ))
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    result = await db.execute(
        select(Thought).where(and_(
            Thought.category_id == category_id,
            Thought.user_id == current_user.id
        ))
    )
    thoughts = result.scalars().all()
    
    for thought in thoughts:
        thought.category_id = None
    
    await db.delete(category)
    await db.commit()
    
    return None
