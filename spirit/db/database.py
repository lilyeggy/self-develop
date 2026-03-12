import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from spirit.db.models import Base


def get_sync_database_url() -> str:
    """获取同步数据库URL"""
    url = os.getenv("DATABASE_URL", "sqlite:///./spirit.db")
    
    if url.startswith("sqlite"):
        return url
    
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "")
    
    return url


def get_async_database_url() -> str:
    """获取异步数据库URL"""
    url = os.getenv("DATABASE_URL", "sqlite:///./spirit.db")
    
    if url.startswith("sqlite"):
        if url.startswith("sqlite:///"):
            path = url.replace("sqlite:///", "", 1)
            return f"sqlite+aiosqlite:///{path}"
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    
    if "+asyncpg" not in url:
        return url + "+asyncpg"
    
    return url


if os.getenv("DATABASE_URL", "").startswith("sqlite"):
    async_url = get_async_database_url()
    sync_url = get_sync_database_url()
    
    engine = create_async_engine(
        async_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    sync_engine = create_engine(
        sync_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    async_url = get_async_database_url()
    sync_url = get_sync_database_url()
    
    engine = create_async_engine(
        async_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    sync_engine = create_engine(
        sync_url,
        echo=False,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
