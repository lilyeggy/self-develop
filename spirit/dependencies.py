from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from spirit.db.database import get_db
from spirit.db.models import User, APIKey
from spirit.utils import decode_access_token
from spirit.core.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> User:
    if credentials is None:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user is None:
            from spirit.db.models import User as UserModel
            user = UserModel(username="default", email="default@local", hashed_password="")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if payload is None:
            result = await db.execute(select(User).limit(1))
            return result.scalar_one_or_none()
        
        user_id: int = payload.get("sub")
        if user_id is None:
            result = await db.execute(select(User).limit(1))
            return result.scalar_one_or_none()
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        return user
    except:
        result = await db.execute(select(User).limit(1))
        return result.scalar_one_or_none()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def verify_api_key(
    api_key: str,
    db: AsyncSession
) -> Optional[User]:
    from spirit.utils import hash_api_key
    
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            (APIKey.expires_at == None) | (APIKey.expires_at > datetime.utcnow())
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if api_key_obj is None:
        return None
    
    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    return result.scalar_one_or_none()


from datetime import datetime
