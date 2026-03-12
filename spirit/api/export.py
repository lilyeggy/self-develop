import json
import io
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from spirit.db.database import get_db
from spirit.db.models import User, Thought, ReviewSummary
from spirit.dependencies import get_current_user
from spirit.services.export import ExportService

router = APIRouter(prefix="/api/v1/export", tags=["export"])

export_service = ExportService()


@router.get("/thoughts")
async def export_thoughts(
    format: str = Query("markdown", regex="^(markdown|json|pdf)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    include_expansions: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Thought).where(Thought.user_id == current_user.id)
    
    if start_date:
        query = query.where(Thought.created_at >= start_date)
    if end_date:
        query = query.where(Thought.created_at <= end_date)
    if category:
        query = query.where(Thought.category == category)
    
    query = query.order_by(Thought.created_at.desc())
    
    result = await db.execute(query)
    thoughts = result.scalars().all()
    
    try:
        if format == "markdown":
            content = await export_service.export_to_markdown(thoughts, include_expansions)
            media_type = "text/markdown"
            filename = f"thoughts_{datetime.now().strftime('%Y%m%d')}.md"
        
        elif format == "json":
            content = await export_service.export_to_json(thoughts, include_expansions)
            media_type = "application/json"
            filename = f"thoughts_{datetime.now().strftime('%Y%m%d')}.json"
        
        elif format == "pdf":
            content = await export_service.export_to_pdf(thoughts, include_expansions)
            media_type = "application/pdf"
            filename = f"thoughts_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.get("/summaries")
async def export_summaries(
    format: str = Query("markdown", regex="^(markdown|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ReviewSummary)
        .where(ReviewSummary.user_id == current_user.id)
        .order_by(ReviewSummary.period_end.desc())
    )
    summaries = result.scalars().all()
    
    try:
        if format == "markdown":
            content = export_service.export_summaries_to_markdown(summaries)
            media_type = "text/markdown"
            filename = f"review_summaries_{datetime.now().strftime('%Y%m%d')}.md"
        
        elif format == "json":
            content = export_service.export_summaries_to_json(summaries)
            media_type = "application/json"
            filename = f"review_summaries_{datetime.now().strftime('%Y%m%d')}.json"
        
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )
