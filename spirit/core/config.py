import os
from typing import Optional
from pydantic_settings import BaseSettings


def get_database_url() -> str:
    """获取数据库URL，支持SQLite和PostgreSQL"""
    url = os.getenv("DATABASE_URL", "sqlite:///./spirit.db")
    
    if url.startswith("sqlite"):
        return url
    
    if "+asyncpg" in url:
        return url
    
    return url


class Settings(BaseSettings):
    APP_NAME: str = "Spirit - Personal Growth Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    DATABASE_URL: str = "sqlite:///./spirit.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    ENCRYPTION_KEY: Optional[str] = None
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    MODELSCOPE_API_KEY: Optional[str] = None
    MODELSCOPE_MODEL: str = "qwen-plus"
    USE_MODELSCOPE: bool = False
    
    DEFAULT_REVIEW_PERIOD: str = "weekly"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URL = get_database_url()


settings = Settings()
