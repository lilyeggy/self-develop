import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Spirit - Personal Growth Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://spirit:spirit123@localhost:5432/spirit"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 加密配置
    ENCRYPTION_KEY: Optional[str] = None  # 32字节密钥，base64编码
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # 回顾提醒配置
    DEFAULT_REVIEW_PERIOD: str = "weekly"  # daily/weekly/monthly
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
