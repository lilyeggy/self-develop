from datetime import datetime, timedelta
from typing import Optional, List
import hashlib
import secrets

from passlib.context import CryptContext
from jose import JWTError, jwt

from spirit.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    key = f"sp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12] + "..."
    return key, key_prefix, key_hash


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def parse_thought_category(content: str) -> str:
    content_lower = content.lower()
    
    if any(marker in content_lower for marker in ["？", "?", "问题", "怎么", "如何", "为什么", "求解"]):
        return "question"
    elif any(marker in content_lower for marker in ["计划", "要", "准备", "打算", "目标"]):
        return "plan"
    elif any(marker in content_lower for marker in ["感悟", "明白", "发现", "想到", "觉得"]):
        return "insight"
    elif any(marker in content_lower for marker in ["反思", "复盘", "回顾", "总结"]):
        return "reflection"
    elif any(marker in content_lower for marker in ["日记", "今天", "今日"]):
        return "diary"
    elif len(content) < 50 and not any(marker in content_lower for marker in ["因为", "所以", "但是", "而且"]):
        return "idea"
    else:
        return "note"


def extract_tags(content: str) -> List[str]:
    import re
    tag_pattern = r"#(\w+)"
    tags = re.findall(tag_pattern, content)
    return list(set(tags))


def sanitize_content(content: str) -> str:
    content = content.strip()
    content = content.replace("\r\n", "\n")
    content = content.replace("\r", "\n")
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")
    return content
