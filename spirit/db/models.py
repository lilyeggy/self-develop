from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class ThoughtCategory(str, enum.Enum):
    IDEA = "idea"           # 想法
    QUESTION = "question"   # 问题
    INSIGHT = "insight"     # 感悟
    PLAN = "plan"          # 计划
    REFLECTION = "reflection"  # 反思
    NOTE = "note"          # 笔记
    DIARY = "diary"        # 日记


class ReviewPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class InputSource(str, enum.Enum):
    WEB = "web"
    API = "api"
    VOICE = "voice"
    NOTION = "notion"
    OBSIDIAN = "obsidian"
    EVERNOTE = "evernote"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    encryption_key_hash = Column(String(255))  # 加密密钥的哈希
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    preferences = Column(JSON, default=dict)
    
    thoughts = relationship("Thought", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("UserCategory", back_populates="user", cascade="all, delete-orphan")
    review_configs = relationship("ReviewConfig", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")


class UserCategory(Base):
    __tablename__ = "user_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default="#6366f1")
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("user_categories.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="categories")
    parent = relationship("UserCategory", remote_side=[id], backref="children")
    thoughts = relationship("Thought", back_populates="category")


class Thought(Base):
    __tablename__ = "thoughts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("user_categories.id"), nullable=True)
    
    content = Column(Text, nullable=False)
    encrypted_content = Column(Text)
    
    raw_content = Column(Text)  # 原始内容，用于比对
    
    category = Column(SQLEnum(ThoughtCategory), default=ThoughtCategory.NOTE)
    
    source = Column(SQLEnum(InputSource), default=InputSource.WEB)
    
    title = Column(String(500))
    tags = Column(JSON, default=list)
    
    is_archived = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    extra_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    thinking_started_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="thoughts")
    category_obj = relationship("UserCategory", back_populates="thoughts")
    expansions = relationship("ThoughtExpansion", back_populates="thought", cascade="all, delete-orphan")
    related_thoughts = relationship(
        "ThoughtRelation",
        foreign_keys="ThoughtRelation.thought_id",
        back_populates="thought",
        cascade="all, delete-orphan"
    )


class ThoughtRelation(Base):
    __tablename__ = "thought_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    thought_id = Column(Integer, ForeignKey("thoughts.id"), nullable=False)
    related_thought_id = Column(Integer, ForeignKey("thoughts.id"), nullable=False)
    relation_type = Column(String(50), default="related")
    
    thought = relationship("Thought", foreign_keys=[thought_id], back_populates="related_thoughts")
    related = relationship("Thought", foreign_keys=[related_thought_id])


class ThoughtExpansion(Base):
    __tablename__ = "thought_expansions"
    
    id = Column(Integer, primary_key=True, index=True)
    thought_id = Column(Integer, ForeignKey("thoughts.id"), nullable=False)
    
    expansion_type = Column(String(50))  # question_extension, related_idea,补充信息, etc.
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    thought = relationship("Thought", back_populates="expansions")


class ReviewConfig(Base):
    __tablename__ = "review_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    period = Column(SQLEnum(ReviewPeriod), default=ReviewPeriod.WEEKLY)
    day_of_week = Column(Integer, nullable=True)  # 0-6, 周一到周日
    day_of_month = Column(Integer, nullable=True)  # 1-31
    hour = Column(Integer, default=20)  # 提醒时间
    minute = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="review_configs")


class ReviewSummary(Base):
    __tablename__ = "review_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    period = Column(SQLEnum(ReviewPeriod), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    summary = Column(Text)
    highlights = Column(JSON, default=list)
    insights = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    insight_type = Column(String(50))  # cognitive_pattern, growth_area, thinking_limit, etc.
    title = Column(String(500))
    content = Column(Text)
    
    related_thought_ids = Column(JSON, default=list)
    
    confidence = Column(String(20), default="medium")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="insights")


class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    feedback_type = Column(String(50))  # expansion_quality, classification_accuracy, etc.
    target_id = Column(Integer)  # 相关内容的ID
    target_type = Column(String(50))  # thought, expansion, insight, etc.
    
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    permissions = Column(JSON, default=list)
    
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
