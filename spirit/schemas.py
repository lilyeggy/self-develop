from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[dict] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    preferences: dict
    
    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    color: str = "#6366f1"
    icon: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ThoughtBase(BaseModel):
    content: str = Field(..., min_length=1)
    category: Optional[str] = "note"
    title: Optional[str] = None
    tags: List[str] = []


class ThoughtCreate(ThoughtBase):
    category_id: Optional[int] = None
    source: Optional[str] = "web"


class ThoughtUpdate(BaseModel):
    content: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class ThoughtResponse(ThoughtBase):
    id: int
    user_id: int
    category_id: Optional[int]
    source: str
    is_archived: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ThoughtExpansionResponse(BaseModel):
    id: int
    thought_id: int
    expansion_type: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ThoughtDetailResponse(ThoughtResponse):
    expansions: List[ThoughtExpansionResponse] = []
    related_thoughts: List[ThoughtResponse] = []


class ReviewConfigBase(BaseModel):
    period: str = "weekly"
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    hour: int = Field(20, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)


class ReviewConfigCreate(ReviewConfigBase):
    pass


class ReviewConfigUpdate(BaseModel):
    period: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    is_active: Optional[bool] = None


class ReviewConfigResponse(ReviewConfigBase):
    id: int
    user_id: int
    is_active: bool
    last_reviewed_at: Optional[datetime]
    next_review_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewSummaryResponse(BaseModel):
    id: int
    user_id: int
    period: str
    period_start: datetime
    period_end: datetime
    summary: str
    highlights: List[str]
    insights: List[str]
    suggestions: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InsightBase(BaseModel):
    insight_type: str
    title: str
    content: str
    related_thought_ids: List[int] = []
    confidence: str = "medium"


class InsightResponse(InsightBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    feedback_type: str
    target_id: int
    target_type: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    feedback_type: str
    target_id: int
    target_type: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExpandThoughtRequest(BaseModel):
    expansion_types: List[str] = ["question_extension", "related_idea", "supplement_info"]


class ExpandThoughtResponse(BaseModel):
    thought_id: int
    expansions: List[ThoughtExpansionResponse]


class ReviewSummaryRequest(BaseModel):
    period: str = "weekly"
    force_regenerate: bool = False


class AnalyticsResponse(BaseModel):
    total_thoughts: int
    thoughts_by_category: dict
    thoughts_by_source: dict
    daily_thoughts_count: List[dict]
    top_tags: List[dict]
    cognitive_patterns: List[dict]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class ExportRequest(BaseModel):
    format: str = "markdown"  # markdown, pdf, json
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    categories: Optional[List[str]] = None
    include_expansions: bool = True
    include_analytics: bool = False


class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read", "write"]
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    permissions: List[str]
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
