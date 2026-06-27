from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.config import get_settings
from app.core.database import get_db
from app.models import User
from app.services.auth_service import AuthService
from app.services.llm_service import LLMService
from app.services.wecom_client import WeComClient


def get_wecom_client() -> WeComClient:
    settings = get_settings()
    return WeComClient(corp_id=settings.wechat_corp_id, cache=get_cache())


def get_llm_service() -> LLMService:
    settings = get_settings()
    return LLMService(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        vision_api_key=settings.vision_api_key,
        vision_base_url=settings.vision_base_url,
        vision_model=settings.vision_model,
    )


def get_auth_service() -> AuthService:
    return AuthService(get_settings().app_secret_key)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    payload = get_auth_service().parse_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="登录已过期")
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="账号不存在")
    return user
