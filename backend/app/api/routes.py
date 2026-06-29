import base64
import hashlib
import io
import re
import zipfile
from datetime import datetime, timedelta
from typing import Annotated
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service, get_current_user, get_llm_service, get_wecom_client
from app.core.config import get_settings
from app.core.database import get_db
from app.core.responses import success
from app.models import (
    ChatMessage,
    CompanyMaterial,
    Customer,
    FollowRecord,
    IpContentRecord,
    PersonaSource,
    ReplyFeedback,
    Tenant,
    User,
)
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.llm_service import LLMService
from app.services.sales_knowledge import SalesKnowledgeService
from app.services.transcript_parser import parse_transcript
from app.services.wecom_client import WeComClient, now_timestamp

router = APIRouter()


class LoginRequest(BaseModel):
    code: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "sales"
    tenant_name: str | None = None
    tenant_id: int | None = None


class LoginPasswordRequest(BaseModel):
    username: str
    password: str


class GuideRequest(BaseModel):
    industry: str
    customer_group: str


class CustomerCreateRequest(BaseModel):
    nickname: str


class CustomerStatusRequest(BaseModel):
    lifecycle_status: str = "active"


class ChatImportRequest(BaseModel):
    sales_userid: str
    external_userid: str
    transcript: str
    customer_name: str | None = None


class FollowAddRequest(BaseModel):
    sales_userid: str
    external_userid: str
    content: str
    next_follow_time: datetime | None = None


class FeedbackRequest(BaseModel):
    sales_userid: str
    external_userid: str
    ai_reply: str
    customer_reply: str = ""
    sales_review: str = ""
    customer_feedback: str = ""
    outcome: str = "neutral"
    original_customer_question: str | None = None


class PersonaSourceRequest(BaseModel):
    sales_userid: str
    external_userid: str
    content: str
    source_type: str = "manual"
    title: str | None = None
    source_url: str | None = None


class IpContentRequest(BaseModel):
    theme: str
    channel: str = "moments"


class CompanyMaterialRequest(BaseModel):
    title: str
    content: str
    source_type: str = "manual"
    scope: str = "sales"


class IntentReplyRequest(BaseModel):
    sales_userid: str
    external_userid: str
    intent: str


class TenantCreateRequest(BaseModel):
    name: str
    contact_name: str | None = None
    contact_phone: str | None = None


class UserCreateRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "sales"
    tenant_id: int | None = None


class ApprovalRequest(BaseModel):
    status: str = "approved"


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_FILE_BYTES = 12 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
SUPPORTED_TEXT_TYPES = {"text/plain", "text/markdown", "text/csv", "application/json"}
SUPPORTED_DOCUMENT_SUFFIXES = {".pdf", ".docx", ".doc"}
PERSONA_SOURCE_TYPES = {"douyin_profile", "douyin_content", "qichacha", "website", "manual"}
URL_PATTERN = re.compile(r"https?://[^\s，。；;）)]+")
DOUYIN_URL_PATTERN = re.compile(r"https?://(?:v\.douyin\.com|www\.douyin\.com|www\.iesdouyin\.com|iesdouyin\.com)/[^\s，。；;）)]+")


def _optional_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    if not authorization:
        return None
    try:
        auth = AuthService(get_settings().app_secret_key)
        token = authorization.removeprefix("Bearer ").strip()
        payload = auth.parse_token(token)
        if payload is None:
            return None
        return db.get(User, payload.user_id)
    except Exception:
        return None


def _normalize_role(role: str) -> str:
    return role if role in {"platform_admin", "tenant_admin", "sales"} else "sales"


def _approval_status(default: str = "approved") -> str:
    return "pending" if get_settings().approval_enforcement else default


def _require_role(user: User, roles: set[str]) -> None:
    if user.role not in roles:
        raise HTTPException(status_code=403, detail="无权限访问该功能")


def _default_tenant(db: Session) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.name == "默认企业"))
    if tenant is None:
        tenant = Tenant(name="默认企业", contact_name="系统默认", status="approved")
        db.add(tenant)
        db.flush()
    return tenant


def _tenant_payload(tenant: Tenant, db: Session | None = None) -> dict:
    payload = {
        "id": tenant.id,
        "name": tenant.name,
        "contact_name": tenant.contact_name or "",
        "contact_phone": tenant.contact_phone or "",
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat(),
    }
    if db is not None:
        payload["sales_count"] = db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id, User.role == "sales"))
    return payload


@router.post("/auth/login")
async def login(body: LoginRequest, wecom: Annotated[WeComClient, Depends(get_wecom_client)]):
    settings = get_settings()
    token = await wecom.get_access_token("app", settings.wechat_app_secret)
    user = await wecom.get_user_info_by_code(token, body.code)
    return success(user)


@router.post("/account/register")
def register_account(
    body: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
):
    username = body.username.strip()
    if len(username) < 3 or len(body.password) < 6:
        return {"code": 1, "message": "账号至少 3 位，密码至少 6 位", "data": {}}
    if db.scalar(select(User).where(User.username == username)):
        return {"code": 1, "message": "账号已存在", "data": {}}
    role = _normalize_role(body.role)
    if role == "platform_admin":
        role = "sales"
    tenant: Tenant | None = None
    if role == "tenant_admin":
        tenant_name = (body.tenant_name or f"{username}的企业").strip()[:128]
        tenant = db.scalar(select(Tenant).where(Tenant.name == tenant_name))
        if tenant is None:
            tenant = Tenant(name=tenant_name, contact_name=(body.display_name or username)[:64], status=_approval_status())
            db.add(tenant)
            db.flush()
    else:
        if body.tenant_id:
            tenant = db.get(Tenant, body.tenant_id)
        if tenant is None and body.tenant_name:
            tenant = db.scalar(select(Tenant).where(Tenant.name == body.tenant_name.strip()))
        if tenant is None:
            tenant = _default_tenant(db)
    user = User(
        username=username,
        password_hash=auth.hash_password(body.password),
        display_name=(body.display_name or username)[:64],
        role=role,
        tenant_id=tenant.id if tenant else None,
        approval_status=_approval_status(),
        memory_summary="",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success({"token": auth.create_token(user.id), "user": _user_payload(user)})


@router.post("/account/login")
def login_account(
    body: LoginPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
):
    user = db.scalar(select(User).where(User.username == body.username.strip()))
    if user is None or not auth.verify_password(body.password, user.password_hash):
        return {"code": 1, "message": "账号或密码错误", "data": {}}
    if get_settings().approval_enforcement and user.approval_status != "approved":
        return {"code": 1, "message": "账号待审核，请联系上级管理员", "data": {}}
    user.last_active_at = datetime.utcnow()
    db.commit()
    return success({"token": auth.create_token(user.id), "user": _user_payload(user)})


@router.get("/account/me")
def account_me(current_user: Annotated[User, Depends(get_current_user)]):
    return success(_user_payload(current_user))


@router.get("/platform/tenants")
def platform_tenants(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    _require_role(current_user, {"platform_admin"})
    tenants = list(db.scalars(select(Tenant).order_by(desc(Tenant.created_at)).limit(200)))
    return success([_tenant_payload(tenant, db) for tenant in tenants])


@router.post("/platform/tenants")
def platform_create_tenant(
    body: TenantCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"platform_admin"})
    name = body.name.strip()[:128]
    if not name:
        return {"code": 1, "message": "请填写企业名称", "data": {}}
    if db.scalar(select(Tenant).where(Tenant.name == name)):
        return {"code": 1, "message": "企业已存在", "data": {}}
    tenant = Tenant(
        name=name,
        contact_name=(body.contact_name or "")[:64],
        contact_phone=(body.contact_phone or "")[:64],
        status=_approval_status(),
        created_by_user_id=current_user.id,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return success(_tenant_payload(tenant, db))


@router.post("/platform/tenants/{tenant_id}/status")
def platform_update_tenant_status(
    tenant_id: int,
    body: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"platform_admin"})
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        return {"code": 1, "message": "企业不存在", "data": {}}
    tenant.status = body.status if body.status in {"pending", "approved", "rejected", "disabled"} else "approved"
    db.commit()
    db.refresh(tenant)
    return success(_tenant_payload(tenant, db))


@router.post("/platform/tenant-admins")
def platform_create_tenant_admin(
    body: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"platform_admin"})
    tenant = db.get(Tenant, body.tenant_id) if body.tenant_id else None
    if tenant is None:
        return {"code": 1, "message": "请选择企业", "data": {}}
    username = body.username.strip()
    if len(username) < 3 or len(body.password) < 6:
        return {"code": 1, "message": "账号至少 3 位，密码至少 6 位", "data": {}}
    if db.scalar(select(User).where(User.username == username)):
        return {"code": 1, "message": "账号已存在", "data": {}}
    user = User(
        username=username,
        password_hash=auth.hash_password(body.password),
        display_name=(body.display_name or username)[:64],
        role="tenant_admin",
        tenant_id=tenant.id,
        approval_status="approved",
        created_by_user_id=current_user.id,
        memory_summary="",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_user_payload(user))


@router.get("/tenant/overview")
def tenant_overview(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    _require_role(current_user, {"tenant_admin", "platform_admin"})
    tenant_id = current_user.tenant_id
    if current_user.role == "platform_admin":
        tenant_id = _default_tenant(db).id
    tenant = db.get(Tenant, tenant_id) if tenant_id else None
    if tenant is None:
        return {"code": 1, "message": "企业不存在", "data": {}}
    sales_count = db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id, User.role == "sales"))
    material_count = db.scalar(select(func.count()).select_from(CompanyMaterial).where(CompanyMaterial.tenant_id == tenant.id))
    pending_sales = db.scalar(
        select(func.count()).select_from(User).where(User.tenant_id == tenant.id, User.role == "sales", User.approval_status == "pending")
    )
    pending_materials = db.scalar(
        select(func.count()).select_from(CompanyMaterial).where(CompanyMaterial.tenant_id == tenant.id, CompanyMaterial.approval_status == "pending")
    )
    return success(
        {
            "tenant": _tenant_payload(tenant, db),
            "sales_count": sales_count or 0,
            "material_count": material_count or 0,
            "pending_sales": pending_sales or 0,
            "pending_materials": pending_materials or 0,
            "approval_enforcement": get_settings().approval_enforcement,
        }
    )


@router.get("/tenant/sales")
def tenant_sales(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    _require_role(current_user, {"tenant_admin"})
    users = list(
        db.scalars(
            select(User)
            .where(User.tenant_id == current_user.tenant_id, User.role == "sales")
            .order_by(desc(User.created_at))
            .limit(300)
        )
    )
    return success([_user_payload(user) for user in users])


@router.post("/tenant/sales")
def tenant_create_sales(
    body: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"tenant_admin"})
    username = body.username.strip()
    if len(username) < 3 or len(body.password) < 6:
        return {"code": 1, "message": "账号至少 3 位，密码至少 6 位", "data": {}}
    if db.scalar(select(User).where(User.username == username)):
        return {"code": 1, "message": "账号已存在", "data": {}}
    user = User(
        username=username,
        password_hash=auth.hash_password(body.password),
        display_name=(body.display_name or username)[:64],
        role="sales",
        tenant_id=current_user.tenant_id,
        approval_status="approved",
        created_by_user_id=current_user.id,
        memory_summary="",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_user_payload(user))


@router.post("/tenant/sales/{user_id}/status")
def tenant_update_sales_status(
    user_id: int,
    body: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"tenant_admin"})
    user = db.get(User, user_id)
    if user is None or user.tenant_id != current_user.tenant_id or user.role != "sales":
        return {"code": 1, "message": "销售不存在", "data": {}}
    user.approval_status = body.status if body.status in {"pending", "approved", "rejected", "disabled"} else "approved"
    db.commit()
    return success(_user_payload(user))


@router.post("/account/guide")
async def save_guide(
    body: GuideRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
):
    current_user.industry = body.industry.strip()[:128]
    current_user.customer_group = body.customer_group.strip()[:255]
    current_user.sales_guide = await llm.generate_sales_guide(
        current_user.industry,
        current_user.customer_group,
        _product_knowledge_for_user(db, current_user),
    )
    db.commit()
    db.refresh(current_user)
    return success(_user_payload(current_user))


@router.get("/wecom/js-config")
async def js_config(url: str, wecom: Annotated[WeComClient, Depends(get_wecom_client)]):
    settings = get_settings()
    access_token = await wecom.get_access_token("app", settings.wechat_app_secret)
    ticket = await wecom.get_jsapi_ticket(access_token)
    signature = wecom.build_js_sdk_signature(ticket=ticket, nonce_str="sales-ai", timestamp=now_timestamp(), url=url)
    return success(signature)


@router.get("/customer/info")
def customer_info(
    sales_userid: str,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, external_userid)
    return success(_customer_payload(customer, db))


@router.get("/customer/list")
def customer_list(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    level: str | None = None,
):
    customers = list(
        db.scalars(
            select(Customer)
            .where(Customer.follow_userid == current_user.sales_userid)
            .order_by(desc(Customer.last_chat_time), desc(Customer.updated_at))
        )
    )
    payload = [_customer_payload(customer, db) for customer in customers]
    if level:
        payload = [item for item in payload if item["category"] == level.upper()]
    return success(payload)


@router.post("/customer/create")
def customer_create(
    body: CustomerCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    nickname = body.nickname.strip()
    if not nickname:
        return {"code": 1, "message": "客户名称必填", "data": {}}
    customer = CustomerService(db).create_manual_customer(current_user.sales_userid, nickname)
    db.commit()
    db.refresh(customer)
    return success(_customer_payload(customer, db))


@router.post("/customer/status")
def customer_status(
    body: CustomerStatusRequest,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    customer = CustomerService(db).get_or_create_customer(current_user.sales_userid, external_userid)
    status = body.lifecycle_status if body.lifecycle_status in {"active", "closed"} else "active"
    customer.lifecycle_status = status
    customer.closed_at = datetime.utcnow() if status == "closed" and customer.closed_at is None else customer.closed_at
    if status == "active":
        customer.closed_at = None
    db.commit()
    SalesKnowledgeService(db).refresh_if_due(force=status == "closed")
    db.refresh(customer)
    return success(_customer_payload(customer, db))


@router.get("/analysis/realtime")
async def realtime_analysis(
    sales_userid: str,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, external_userid)
    messages = _load_conversation(db, active_sales_userid, external_userid, limit=20)
    history = [{"content": item.content, "from_user": item.from_user, "msg_time": item.msg_time.isoformat()} for item in messages]
    product_knowledge = _product_knowledge_for_user(db, current_user) if current_user else get_settings().product_knowledge
    analysis = await llm.analyze_realtime(
        _customer_payload(customer, db),
        history,
        product_knowledge,
        sales_guide=current_user.sales_guide if current_user else "",
        memory_summary=current_user.memory_summary if current_user else "",
        feedback_lessons=_global_feedback_lessons(db),
        persona_sources=_persona_sources(db, active_sales_userid, external_userid),
        sales_playbook=_sales_playbook_context(db),
    )
    customer.core_demand = analysis["core_demand"]
    customer.objection = analysis["objection"]
    db.commit()
    return success({"customer": _customer_payload(customer, db), "analysis": analysis})


@router.post("/analysis/summary")
async def summary():
    return success(
        {
            "key_points": ["已记录核心诉求", "待补充真实会话后生成完整小结"],
            "commitment": "",
            "follow_up_date": "",
            "summary": "MVP 当前提供实时分析，完整小结接口已预留。",
        }
    )


@router.post("/analysis/intent-reply")
async def intent_reply(
    body: IntentReplyRequest,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    intent = body.intent.strip()[:500]
    if not intent:
        return {"code": 1, "message": "请填写你想对客户表达的意思", "data": {}}
    active_sales_userid = current_user.sales_userid if current_user else body.sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, body.external_userid)
    messages = _load_conversation(db, active_sales_userid, body.external_userid, limit=20)
    history = [{"content": item.content, "from_user": item.from_user, "msg_time": item.msg_time.isoformat()} for item in messages]
    result = await llm.generate_intent_reply(
        intent=intent,
        customer_profile=_customer_payload(customer, db),
        chat_history=history,
        product_knowledge=_product_knowledge_for_user(db, current_user) if current_user else get_settings().product_knowledge,
        sales_guide=current_user.sales_guide if current_user else "",
        memory_summary=current_user.memory_summary if current_user else "",
        feedback_lessons=_global_feedback_lessons(db),
        persona_sources=_persona_sources(db, active_sales_userid, body.external_userid),
        sales_playbook=_sales_playbook_context(db),
    )
    return success(result)


@router.post("/chat/import")
def import_chat(
    body: ChatImportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    sales_userid = current_user.sales_userid if current_user else body.sales_userid
    service = CustomerService(db)
    customer = service.get_or_create_customer(sales_userid, body.external_userid)
    if body.customer_name:
        customer.nickname = body.customer_name[:128]
    parsed_messages = parse_transcript(body.transcript, sales_userid, body.external_userid)
    imported = 0
    for item in parsed_messages:
        msg_id = _manual_msg_id(sales_userid, body.external_userid, item.from_user, item.msg_time, item.content)
        if db.scalar(select(ChatMessage).where(ChatMessage.msg_id == msg_id)):
            continue
        db.add(
            ChatMessage(
                msg_id=msg_id,
                seq=0,
                action="send",
                from_user=item.from_user,
                to_user=item.to_user,
                msg_type="text",
                content=item.content,
                msg_time=item.msg_time,
                room_id=None,
            )
        )
        imported += 1
    service.apply_profile(
        customer,
        [{"from_customer": item.from_customer, "content": item.content, "hours_ago": 0} for item in parsed_messages],
    )
    db.commit()
    return success({"imported": imported, "customer": _customer_payload(customer, db)})


@router.post("/vision/extract")
async def vision_extract(
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    purpose: Annotated[str, Form()] = "chat",
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    _ = current_user
    if not files:
        return {"code": 1, "message": "请上传图片", "data": {}}
    images = []
    for file in files[:6]:
        content_type = file.content_type or "application/octet-stream"
        if content_type not in SUPPORTED_IMAGE_TYPES:
            return {"code": 1, "message": f"不支持的图片类型：{content_type}", "data": {}}
        content = await file.read()
        if len(content) > MAX_IMAGE_BYTES:
            return {"code": 1, "message": "单张图片不能超过 5MB", "data": {}}
        images.append(
            {
                "filename": file.filename or "image",
                "content_type": content_type,
                "base64": base64.b64encode(content).decode("ascii"),
            }
        )
    text = await llm.analyze_images(images, purpose=purpose)
    return success({"text": text, "count": len(images), "purpose": purpose})


@router.post("/file/extract")
async def file_extract(
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    purpose: Annotated[str, Form()] = "company",
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    _ = current_user
    if not files:
        return {"code": 1, "message": "请上传 Word、PDF 或图片", "data": {}}
    text_blocks: list[str] = []
    images: list[dict[str, str]] = []
    for file in files[:8]:
        content = await file.read()
        if len(content) > MAX_FILE_BYTES:
            return {"code": 1, "message": f"{file.filename or '文件'} 不能超过 12MB", "data": {}}
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "file"
        suffix = _file_suffix(filename)
        if content_type in SUPPORTED_IMAGE_TYPES:
            if len(content) > MAX_IMAGE_BYTES:
                return {"code": 1, "message": "单张图片不能超过 5MB", "data": {}}
            images.append({"filename": filename, "content_type": content_type, "base64": base64.b64encode(content).decode("ascii")})
            continue
        if suffix == ".pdf":
            text_blocks.append(_extract_pdf_text(content, filename))
            continue
        if suffix == ".docx":
            text_blocks.append(_extract_docx_text(content, filename))
            continue
        if suffix == ".doc":
            return {"code": 1, "message": "暂不支持旧版 .doc，请另存为 .docx 或 PDF 后上传", "data": {}}
        if content_type in SUPPORTED_TEXT_TYPES or suffix in {".txt", ".md", ".csv", ".json"}:
            text_blocks.append(f"# {filename}\n{_decode_text(content)}")
            continue
        return {"code": 1, "message": f"不支持的文件类型：{filename}", "data": {}}
    if images:
        text_blocks.append(await llm.analyze_images(images, purpose=purpose))
    text = "\n\n".join(block.strip() for block in text_blocks if block.strip())
    return success({"text": text, "count": len(files), "purpose": purpose})


@router.get("/follow/list")
def follow_list(
    sales_userid: str,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, external_userid)
    return success(_follow_payloads(db, customer.id, active_sales_userid, limit=100))


@router.post("/follow/add")
def follow_add(
    body: FollowAddRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else body.sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, body.external_userid)
    record = FollowRecord(
        customer_id=customer.id,
        sales_userid=active_sales_userid,
        content=body.content,
        next_follow_time=body.next_follow_time,
    )
    db.add(record)
    db.commit()
    return success({"id": record.id})


@router.get("/follow/overview")
def follow_overview(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    today = datetime.utcnow().date()
    customers = list(db.scalars(select(Customer).where(Customer.follow_userid == current_user.sales_userid)))
    items = []
    for customer in customers:
        records = _follow_payloads(db, customer.id, current_user.sales_userid, limit=5)
        followed_today = any(record["created_at"][:10] == today.isoformat() for record in records)
        items.append(
            {
                "customer": _customer_payload(customer, db),
                "followed_today": followed_today,
                "last_follow": records[0] if records else None,
                "next_suggestion": _next_follow_suggestion(customer, followed_today),
                "hook_suggestion": _hook_suggestion(customer),
            }
        )
    done = [item for item in items if item["followed_today"]]
    pending = [item for item in items if not item["followed_today"]]
    return success({"date": today.isoformat(), "done": done, "pending": pending})


@router.get("/feedback/list")
def feedback_list(
    sales_userid: str,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    return success(_feedback_payloads(db, active_sales_userid, external_userid, limit=50))


@router.post("/feedback/add")
def feedback_add(
    body: FeedbackRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else body.sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, body.external_userid)
    outcome = body.outcome if body.outcome in {"good", "bad", "neutral"} else "neutral"
    customer_reply = body.customer_reply.strip() or body.customer_feedback.strip()
    sales_review = body.sales_review.strip()
    if not customer_reply and not sales_review:
        return {"code": 1, "message": "请填写客户回复或销售看法", "data": {}}
    combined_feedback = f"客户回复：{customer_reply}\n销售看法：{sales_review}".strip()
    record = ReplyFeedback(
        customer_id=customer.id,
        sales_userid=active_sales_userid,
        external_userid=body.external_userid,
        original_customer_question=(body.original_customer_question or "")[:1000],
        ai_reply=body.ai_reply[:2000],
        customer_feedback=combined_feedback[:2000],
        outcome=outcome,
        lesson=_build_feedback_lesson(outcome, body.ai_reply, customer_reply, sales_review),
    )
    db.add(record)
    db.commit()
    SalesKnowledgeService(db).refresh_if_due()
    db.refresh(record)
    return success(_feedback_payload(record))


@router.get("/persona/source/list")
def persona_source_list(
    sales_userid: str,
    external_userid: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    return success(_persona_source_payloads(db, active_sales_userid, external_userid, limit=30))


@router.post("/persona/source/add")
async def persona_source_add(
    body: PersonaSourceRequest,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else body.sales_userid
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, body.external_userid)
    title, content, source_type, source_url = _prepare_persona_source_input(
        body.title,
        body.content,
        body.source_type,
        body.source_url,
    )
    if not content:
        return {"code": 1, "message": "请填写客户资料内容，或至少提供一个可识别的资料链接", "data": {}}
    source = PersonaSource(
        customer_id=customer.id,
        sales_userid=active_sales_userid,
        external_userid=body.external_userid,
        source_type=source_type,
        title=title,
        source_url=source_url or None,
        content=content,
        persona_summary=await llm.analyze_persona_source(content, _customer_payload(customer, db), source_type, source_url),
    )
    db.add(source)
    db.flush()
    _refresh_customer_persona(db, customer)
    db.commit()
    db.refresh(source)
    return success(_persona_source_payload(source))


@router.post("/persona/intelligence/analyze")
async def persona_intelligence_analyze(
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    current_user: Annotated[User | None, Depends(_optional_current_user)] = None,
    sales_userid: Annotated[str, Form()] = "",
    external_userid: Annotated[str, Form()] = "",
    source_type: Annotated[str, Form()] = "manual",
    source_url: Annotated[str, Form()] = "",
    title: Annotated[str | None, Form()] = None,
    content: Annotated[str, Form()] = "",
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    active_sales_userid = current_user.sales_userid if current_user else sales_userid
    if not active_sales_userid or not external_userid:
        return {"code": 1, "message": "客户参数缺失", "data": {}}
    customer = CustomerService(db).get_or_create_customer(active_sales_userid, external_userid)
    images: list[dict[str, str]] = []
    text_blocks: list[str] = [content.strip()] if content.strip() else []
    if files:
        for file in files[:8]:
            uploaded = await file.read()
            if len(uploaded) > MAX_FILE_BYTES:
                return {"code": 1, "message": f"{file.filename or '文件'} 不能超过 12MB", "data": {}}
            content_type = file.content_type or "application/octet-stream"
            filename = file.filename or "file"
            suffix = _file_suffix(filename)
            if content_type in SUPPORTED_IMAGE_TYPES:
                if len(uploaded) > MAX_IMAGE_BYTES:
                    return {"code": 1, "message": "单张图片不能超过 5MB", "data": {}}
                images.append({"filename": filename, "content_type": content_type, "base64": base64.b64encode(uploaded).decode("ascii")})
                continue
            if suffix == ".pdf":
                text_blocks.append(_extract_pdf_text(uploaded, filename))
                continue
            if suffix == ".docx":
                text_blocks.append(_extract_docx_text(uploaded, filename))
                continue
            if suffix == ".doc":
                return {"code": 1, "message": "暂不支持旧版 .doc，请另存为 .docx 或 PDF 后上传", "data": {}}
            if content_type in SUPPORTED_TEXT_TYPES or suffix in {".txt", ".md", ".csv", ".json"}:
                text_blocks.append(f"# {filename}\n{_decode_text(uploaded)}")
                continue
            return {"code": 1, "message": f"不支持的文件类型：{filename}", "data": {}}
    raw_context = "\n\n".join(block.strip() for block in text_blocks if block.strip())
    prepared_title, prepared_content, inferred_type, cleaned_url = _prepare_persona_source_input(title, raw_context, source_type, source_url)
    if images and not prepared_content:
        prepared_content = "用户上传了客户截图，请基于图片直接识别截图类型、平台、账号、内容、评论、企业线索和销售假设。"
    if not images and not prepared_content:
        return {"code": 1, "message": "请上传截图/文件，或填写客户资料内容", "data": {}}
    if images:
        persona_summary = await llm.analyze_persona_images(
            images,
            customer_profile=_customer_payload(customer, db),
            source_type=inferred_type,
            source_url=cleaned_url,
            text_context=prepared_content,
        )
        stored_content = (
            f"{prepared_content}\n\n"
            f"多模态截图分析：本次直接分析 {len(images)} 张截图，未将图片仅降级为 OCR 文本。\n"
            f"{persona_summary}"
        ).strip()
    else:
        persona_summary = await llm.analyze_persona_source(prepared_content, _customer_payload(customer, db), inferred_type, cleaned_url)
        stored_content = prepared_content
    source = PersonaSource(
        customer_id=customer.id,
        sales_userid=active_sales_userid,
        external_userid=external_userid,
        source_type=inferred_type,
        title=prepared_title,
        source_url=cleaned_url or None,
        content=stored_content[:7000],
        persona_summary=persona_summary,
    )
    db.add(source)
    db.flush()
    _refresh_customer_persona(db, customer)
    db.commit()
    db.refresh(source)
    return success(_persona_source_payload(source))


@router.get("/company/material/list")
def company_material_list(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role == "tenant_admin":
        records = list(
            db.scalars(
                select(CompanyMaterial)
                .where(CompanyMaterial.tenant_id == current_user.tenant_id)
                .order_by(desc(CompanyMaterial.created_at))
                .limit(100)
            )
        )
    else:
        records = list(
            db.scalars(
                select(CompanyMaterial)
                .where(
                    CompanyMaterial.tenant_id == current_user.tenant_id,
                    CompanyMaterial.effective == True,  # noqa: E712
                    CompanyMaterial.approval_status == "approved",
                    (CompanyMaterial.scope == "tenant")
                    | ((CompanyMaterial.scope == "sales") & (CompanyMaterial.owner_user_id == current_user.id)),
                )
                .order_by(desc(CompanyMaterial.created_at))
                .limit(80)
            )
        )
    return success([_company_material_payload(item) for item in records])


@router.post("/company/material/add")
def company_material_add(
    body: CompanyMaterialRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    title = body.title.strip()[:128]
    content = body.content.strip()[:12000]
    if not title or not content:
        return {"code": 1, "message": "请填写资料标题和内容", "data": {}}
    scope = "tenant" if current_user.role == "tenant_admin" or body.scope == "tenant" else "sales"
    approval_status = "approved"
    effective = True
    if current_user.role == "sales" and scope == "tenant" and get_settings().approval_enforcement:
        approval_status = "pending"
        effective = False
    record = CompanyMaterial(
        sales_userid=current_user.sales_userid,
        tenant_id=current_user.tenant_id,
        owner_user_id=current_user.id,
        scope=scope,
        approval_status=approval_status,
        effective=effective,
        reviewed_by_user_id=current_user.id if approval_status == "approved" else None,
        reviewed_at=datetime.utcnow() if approval_status == "approved" else None,
        title=title,
        source_type=body.source_type[:32] or "manual",
        content=content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success(_company_material_payload(record))


@router.post("/tenant/materials/{material_id}/status")
def tenant_update_material_status(
    material_id: int,
    body: ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _require_role(current_user, {"tenant_admin"})
    material = db.get(CompanyMaterial, material_id)
    if material is None or material.tenant_id != current_user.tenant_id:
        return {"code": 1, "message": "资料不存在", "data": {}}
    material.approval_status = body.status if body.status in {"pending", "approved", "rejected", "disabled"} else "approved"
    material.effective = material.approval_status == "approved"
    material.reviewed_by_user_id = current_user.id
    material.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(material)
    return success(_company_material_payload(material))


@router.post("/ip/content/generate")
async def ip_content_generate(
    body: IpContentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
):
    theme = body.theme.strip()[:128]
    if not theme:
        return {"code": 1, "message": "请填写内容主题", "data": {}}
    content = await llm.generate_ip_content(
        current_user.industry or "",
        current_user.customer_group or "",
        current_user.sales_guide or "",
        theme,
        body.channel,
    )
    record = IpContentRecord(
        sales_userid=current_user.sales_userid,
        theme=theme,
        channel=body.channel[:32] or "moments",
        content=content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success(_ip_content_payload(record))


@router.get("/ip/content/list")
def ip_content_list(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    records = list(
        db.scalars(
            select(IpContentRecord)
            .where(IpContentRecord.sales_userid == current_user.sales_userid)
            .order_by(desc(IpContentRecord.created_at))
            .limit(30)
        )
    )
    return success([_ip_content_payload(item) for item in records])


@router.get("/ip/daily-advice")
async def ip_daily_advice(
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
):
    content = await llm.generate_daily_ip_advice(
        current_user.industry or "",
        current_user.customer_group or "",
        current_user.sales_guide or "",
    )
    return success({"content": content, "date": datetime.utcnow().date().isoformat()})


@router.get("/guide/software")
def software_guide():
    return success(
        {
            "content": """# 软件使用 SOP

## 每天开始前：先看总结
进入 **总结** 页，看三件事：客户总数与分层、今日跟进完成率、优先客户榜。先处理 S/A 类客户，再处理待跟进客户，最后做低意向客户培育。

## 第一步：完善我的资料
在 **我的** 页填写行业和客户群体，生成销售指南。再上传公司资料，包括产品介绍、报价政策、成功案例、售后规则和常见问题。公司资料越完整，系统给出的回复越贴近业务。

公司资料有两种更新方式：**全量更新** 和 **只写变化**。如果选择全量更新，请把产品、价格、案例、售后等完整资料全部重新上传，系统会以最新完整资料为准；如果只是价格、政策、案例有小变化，直接写“某某产品价格由 100 变成 120”，系统会用这条变化覆盖旧资料里的对应信息。

## 第二步：建立客户
在 **话术** 页新建客户，客户名称必填。客户创建后会出现在 **客户** 页，并按 S/A/B/C/D 自动归类。

## 第三步：导入聊天记录
可以粘贴聊天文本，也可以上传聊天截图、Word 或 PDF。系统会先把资料整理成可分析文本，再生成客户全景、意向判断和话术建议。

## 第四步：看回复建议
在 **话术** 页查看三种回复：专业正式、亲和拉近、引导提问。复制前先看“回复解析”，理解这句话抓住了客户哪个点。

## 第五步：记录跟进
沟通完成后到 **跟进** 页记录结果。每次记录都要写清楚：客户反馈、当前状态、下次时间、下次沟通钩子。钩子可以是“下次发案例”“周五给预算拆分”“明天发对比清单”。

## 第六步：管理客户库
进入 **客户** 页，用搜索快速找到客户。客户多时只看对应等级，下拉展开即可。S/A 客户要高频跟进，B/C 客户要内容培育，D 客户只做低频唤醒。

## 第七步：做反馈复盘
在 **客户全景建设** 页记录客户收到 AI 话术后的真实回复，以及销售自己的判断。效果好的话术会沉淀为经验；效果差的场景，下次系统会换思路，让您的销售助手更加智能好用。

## 第八步：补客户人设资料
客户朋友圈、自媒体截图可以持续上传到 **客户全景建设** 页。客户判断是长期过程，不是只看一次资料；系统会随着新朋友圈、新聊天记录、新公开资料不断更新这个客户的长期判断。

## 第九步：打造个人 IP
每天查看 **个人 IP 打造** 页的今日 IP 建议，生成朋友圈或抖音短视频文案。重点不是硬广，而是持续建立专业、可信、有温度的人设。

""",
        }
    )


@router.get("/guide/sales-techniques")
def sales_techniques_guide(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    _ = current_user
    service = SalesKnowledgeService(db)
    service.refresh_if_due()
    return success({"content": service.build_technique_guide()})


def _product_knowledge_for_user(db: Session, user: User | None) -> str:
    base = get_settings().product_knowledge
    if user is None:
        return base
    materials = list(
        db.scalars(
            select(CompanyMaterial)
            .where(
                CompanyMaterial.tenant_id == user.tenant_id,
                CompanyMaterial.effective == True,  # noqa: E712
                CompanyMaterial.approval_status == "approved",
                (CompanyMaterial.scope == "tenant")
                | ((CompanyMaterial.scope == "sales") & (CompanyMaterial.owner_user_id == user.id)),
            )
            .order_by(desc(CompanyMaterial.created_at))
            .limit(30)
        )
    )
    if not materials:
        return base
    full_material = next((item for item in materials if item.source_type in {"full_replace", "manual"}), None)
    if full_material is None:
        effective_materials = materials[:12]
    else:
        effective_materials = [full_material]
        effective_materials.extend(
            item for item in materials if item.source_type == "delta_update" and item.created_at > full_material.created_at
        )
    blocks = [base, "\n# 公司资料使用规则\n优先参考最新完整资料；如果存在之后录入的变更记录，以变更记录覆盖旧内容。"]
    for item in effective_materials[:12]:
        label = "最新完整资料" if item.source_type in {"full_replace", "manual"} else "后续变更记录"
        blocks.append(f"\n## {label}：{item.title}\n{item.content[:1500]}")
    return "\n".join(blocks)


def _file_suffix(filename: str) -> str:
    name = (filename or "").lower()
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1]


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text(content: bytes, filename: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = []
        for index, page in enumerate(reader.pages[:80], start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(f"## 第 {index} 页\n{text}")
        if pages:
            return f"# {filename}\n" + "\n\n".join(pages)
        return f"# {filename}\nPDF 已上传，但未提取到可用文字。若是扫描件，请转为图片上传或使用清晰截图。"
    except Exception:
        return f"# {filename}\nPDF 已上传，但当前环境未能解析内容。请复制关键文字，或将 PDF 页面截图后上传。"


def _extract_docx_text(content: bytes, filename: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml_content = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml_content)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
            if text:
                paragraphs.append(text)
        return f"# {filename}\n" + "\n".join(paragraphs[:1200])
    except Exception:
        return f"# {filename}\nWord 文件已上传，但未能解析内容。请确认文件未损坏，或另存为 PDF 后重新上传。"


def _load_conversation(db: Session, sales_userid: str, external_userid: str, limit: int) -> list[ChatMessage]:
    return list(
        db.scalars(
            select(ChatMessage)
            .where(
                ((ChatMessage.from_user == sales_userid) & (ChatMessage.to_user == external_userid))
                | ((ChatMessage.from_user == external_userid) & (ChatMessage.to_user == sales_userid))
            )
            .order_by(desc(ChatMessage.msg_time))
            .limit(limit)
        )
    )


def _manual_msg_id(sales_userid: str, external_userid: str, from_user: str, msg_time: datetime, content: str) -> str:
    digest = hashlib.sha256(
        f"{sales_userid}|{external_userid}|{from_user}|{msg_time.isoformat()}|{content}".encode("utf-8")
    ).hexdigest()[:40]
    return f"manual:{digest}"


def _customer_payload(customer: Customer, db: Session | None = None) -> dict:
    payload = {
        "id": customer.id,
        "external_userid": customer.external_userid,
        "nickname": customer.nickname or customer.external_userid,
        "avatar": customer.avatar,
        "gender": customer.gender,
        "region": customer.region,
        "remark": customer.remark,
        "follow_userid": customer.follow_userid,
        "intention_level": customer.intention_level,
        "category": _customer_category(customer),
        "intention_score": customer.intention_score,
        "last_chat_time": customer.last_chat_time.isoformat() if customer.last_chat_time else "",
        "core_demand": customer.core_demand or "",
        "objection": customer.objection or "",
        "persona_profile": customer.persona_profile or "",
        "persona_updated_at": customer.persona_updated_at.isoformat() if customer.persona_updated_at else "",
        "lifecycle_status": customer.lifecycle_status or "active",
        "closed_at": customer.closed_at.isoformat() if customer.closed_at else "",
        "tags": [
            {
                "tag_name": tag.tag_name,
                "tag_type": tag.tag_type,
                "source": tag.source,
                "confidence": float(tag.confidence),
            }
            for tag in customer.tags
        ],
        "recent_follow_records": [],
    }
    if db is not None:
        payload["recent_follow_records"] = _follow_payloads(db, customer.id, customer.follow_userid, limit=3)
    return payload


def _customer_category(customer: Customer) -> str:
    if customer.intention_score < 20:
        return "D"
    if customer.last_chat_time and customer.last_chat_time < datetime.utcnow() - timedelta(days=30):
        return "D"
    return customer.intention_level or "C"


def _follow_payloads(db: Session, customer_id: int, sales_userid: str, limit: int) -> list[dict]:
    records = list(
        db.scalars(
            select(FollowRecord)
            .where(FollowRecord.customer_id == customer_id, FollowRecord.sales_userid == sales_userid)
            .order_by(desc(FollowRecord.created_at))
            .limit(limit)
        )
    )
    return [
        {
            "id": item.id,
            "content": item.content,
            "next_follow_time": item.next_follow_time.isoformat() if item.next_follow_time else "",
            "created_at": item.created_at.isoformat(),
        }
        for item in records
    ]


def _next_follow_suggestion(customer: Customer, followed_today: bool) -> str:
    if followed_today:
        return "今天已跟进。建议在记录里写清下次跟进时间和钩子。"
    if customer.intention_level in {"S", "A"}:
        return "今天建议跟进，优先确认预算、时间和下一步动作。"
    if customer.intention_level == "B":
        return "可轻量跟进，发送案例、资料或行业观察。"
    return "低频培育即可，用朋友圈内容或价值资料轻触达。"


def _hook_suggestion(customer: Customer) -> str:
    if customer.objection:
        return f"围绕“{customer.objection}”留下下次沟通借口，例如下次发案例、报价拆分或对比清单。"
    if customer.core_demand:
        return f"围绕“{customer.core_demand}”留钩子，例如约定下次补充资料或给一份方案建议。"
    return "本次跟进结束前，务必约定一个下次动作：发资料、看案例、确认预算或约时间。"


def _feedback_payloads(db: Session, sales_userid: str, external_userid: str, limit: int) -> list[dict]:
    records = list(
        db.scalars(
            select(ReplyFeedback)
            .where(ReplyFeedback.sales_userid == sales_userid, ReplyFeedback.external_userid == external_userid)
            .order_by(desc(ReplyFeedback.created_at))
            .limit(limit)
        )
    )
    return [_feedback_payload(item) for item in records]


def _global_feedback_lessons(db: Session) -> list[dict]:
    records = list(db.scalars(select(ReplyFeedback).order_by(desc(ReplyFeedback.created_at)).limit(30)))
    return [
        {"outcome": item.outcome, "lesson": item.lesson or "", "feedback_summary": item.customer_feedback[:260]}
        for item in records
    ]


def _sales_playbook_context(db: Session) -> str:
    service = SalesKnowledgeService(db)
    service.refresh_if_due()
    return service.build_context()


def _feedback_payload(item: ReplyFeedback) -> dict:
    customer_reply, sales_review = _split_feedback(item.customer_feedback)
    return {
        "id": item.id,
        "original_customer_question": item.original_customer_question or "",
        "ai_reply": item.ai_reply,
        "customer_feedback": item.customer_feedback,
        "customer_reply": customer_reply,
        "sales_review": sales_review,
        "outcome": item.outcome,
        "lesson": item.lesson or "",
        "created_at": item.created_at.isoformat(),
    }


def _split_feedback(text: str) -> tuple[str, str]:
    customer_reply = text
    sales_review = ""
    if "销售看法：" in text:
        before, after = text.split("销售看法：", 1)
        customer_reply = before.replace("客户回复：", "").strip()
        sales_review = after.strip()
    return customer_reply, sales_review


def _build_feedback_lesson(outcome: str, ai_reply: str, customer_reply: str, sales_review: str) -> str:
    _ = ai_reply
    if outcome == "good":
        return f"有效经验：客户回复“{customer_reply[:80]}”。销售判断：{sales_review[:80]}。类似场景可保留这类表达逻辑。"
    if outcome == "bad":
        return f"失败教训：客户回复“{customer_reply[:80]}”。销售判断：{sales_review[:80]}。下次要换角度，少压迫，多确认真实顾虑。"
    return f"中性反馈：客户回复“{customer_reply[:80]}”。销售判断：{sales_review[:80]}。下次先确认客户是否理解，再推进下一步。"


def _persona_source_payloads(db: Session, sales_userid: str, external_userid: str, limit: int) -> list[dict]:
    records = list(
        db.scalars(
            select(PersonaSource)
            .where(PersonaSource.sales_userid == sales_userid, PersonaSource.external_userid == external_userid)
            .order_by(desc(PersonaSource.created_at))
            .limit(limit)
        )
    )
    return [_persona_source_payload(item) for item in records]


def _persona_sources(db: Session, sales_userid: str, external_userid: str) -> list[dict]:
    return [
        {
            "source_type": item["source_type"],
            "title": item["title"],
            "source_url": item["source_url"],
            "persona_summary": item["persona_summary"],
        }
        for item in _persona_source_payloads(db, sales_userid, external_userid, limit=8)
    ]


def _refresh_customer_persona(db: Session, customer: Customer) -> None:
    records = list(
        db.scalars(
            select(PersonaSource)
            .where(PersonaSource.customer_id == customer.id)
            .order_by(desc(PersonaSource.created_at))
            .limit(20)
        )
    )
    if not records:
        return
    summaries = [item.persona_summary or _summarize_persona_source(item.content) for item in records]
    latest = records[0]
    profile = [
        f"最近更新：{latest.created_at.date().isoformat()}，累计资料 {len(records)} 条。",
        "销售假设：以下判断只来自已上传资料，用于优化开场、跟进角度和风险提醒，不等同于已验证事实。",
        "持续判断：客户人设会随着朋友圈、抖音内容、企查查资料、聊天截图和公开资料持续补充，不以单次资料下结论。",
    ]
    for record, summary in zip(records[:8], summaries[:8], strict=False):
        if not summary:
            continue
        label = _persona_source_type_label(record.source_type)
        title = record.title or "客户公开资料"
        profile.append(f"- {label}｜{title}：{summary[:180]}")
    customer.persona_profile = "\n".join(profile)[:3000]
    customer.persona_updated_at = datetime.utcnow()


def _persona_source_payload(item: PersonaSource) -> dict:
    return {
        "id": item.id,
        "source_type": item.source_type,
        "title": item.title or "",
        "source_url": item.source_url or "",
        "content": item.content,
        "persona_summary": item.persona_summary or "",
        "created_at": item.created_at.isoformat(),
    }


def _normalize_persona_source_type(source_type: str) -> str:
    value = (source_type or "").strip()
    return value if value in PERSONA_SOURCE_TYPES else "manual"


def _prepare_persona_source_input(title: str | None, content: str, source_type: str, source_url: str | None) -> tuple[str, str, str, str]:
    raw_content = (content or "").strip()
    cleaned_url = _clean_source_url(source_url or _extract_first_url(raw_content))
    normalized_type = _normalize_persona_source_type(source_type)
    inferred_type = _infer_persona_source_type(normalized_type, cleaned_url, raw_content)
    prepared_title = (title or _default_persona_title(inferred_type)).strip()[:128] or "客户公开资料"
    prepared_content = raw_content
    if inferred_type in {"douyin_profile", "douyin_content"}:
        prepared_content = _format_douyin_evidence(raw_content, cleaned_url)
    elif not prepared_content and cleaned_url:
        prepared_content = (
            f"来源链接：{cleaned_url}\n"
            "证据状态：用户只提供了链接，系统尚未抓取完整页面；以下只能作为待验证销售假设。\n"
            "补充建议：请继续上传页面截图、评论区截图、官网摘要或企查查摘要，让企业判断更完整。"
        )
    return prepared_title, prepared_content[:7000], inferred_type, cleaned_url


def _extract_first_url(text: str) -> str:
    matched = URL_PATTERN.search(text or "")
    return _clean_source_url(matched.group(0)) if matched else ""


def _clean_source_url(url: str | None) -> str:
    return (url or "").strip().rstrip("，。；;、,.!?！？）)")


def _infer_persona_source_type(source_type: str, source_url: str, content: str) -> str:
    if source_type != "manual":
        return source_type
    haystack = f"{source_url}\n{content}".lower()
    if DOUYIN_URL_PATTERN.search(haystack) or "复制打开抖音" in content or "抖音" in content:
        if "主页" in content and "作品" not in content and "#" not in content:
            return "douyin_profile"
        return "douyin_content"
    if "qcc.com" in haystack or "企查查" in content or "天眼查" in content:
        return "qichacha"
    if source_url:
        return "website"
    return "manual"


def _format_douyin_evidence(content: str, source_url: str) -> str:
    text = (content or "").strip()
    subject = ""
    account = ""
    subject_match = re.search(r"看看【(.+?)】", text)
    if subject_match:
        subject = subject_match.group(1).strip()
        account = re.sub(r"的(作品|主页|视频)$", "", subject).strip()
    text_without_url = text.replace(source_url, "") if source_url else text
    after_subject = text_without_url.split("】", 1)[1] if "】" in text_without_url else text_without_url
    work_clue = re.split(r"#|https?://", after_subject, maxsplit=1)[0].strip(" ，。:：")
    tags = []
    for tag in re.findall(r"#\s*([^#\s，。\.…]+)", text):
        clean_tag = tag.strip(" ，。:：#.")
        if clean_tag and clean_tag not in tags:
            tags.append(clean_tag)
    lines = [
        "平台：抖音",
        "资料类型：抖音分享文案/短链，系统尚未抓取完整视频页面。",
        "证据状态：只能基于用户粘贴的分享文案、链接、标题、标签做销售假设，不能当成已抓取完整页面。",
    ]
    if source_url:
        lines.append(f"来源链接：{source_url}")
    if account:
        lines.append(f"账号：{account}")
    elif subject:
        lines.append(f"账号/主体线索：{subject}")
    if work_clue:
        lines.append(f"作品线索：{work_clue}")
    if tags:
        lines.append(f"标签：{'、'.join(tags)}")
    if text:
        lines.append(f"原始分享文本：{text[:1000]}")
    else:
        lines.append("用户只提供了链接，建议继续上传抖音主页截图、视频截图、评论区截图或口播摘要，才能分析账号定位、客户性格和真实互动痛点。")
    return "\n".join(lines)


def _default_persona_title(source_type: str) -> str:
    titles = {
        "douyin_profile": "抖音主页情报",
        "douyin_content": "抖音内容情报",
        "qichacha": "企查查企业情报",
        "website": "官网公开情报",
        "manual": "销售观察情报",
    }
    return titles.get(source_type, "客户公开资料")


def _persona_source_type_label(source_type: str) -> str:
    labels = {
        "douyin_profile": "抖音主页",
        "douyin_content": "抖音内容",
        "qichacha": "企查查资料",
        "website": "网站资料",
        "manual": "手动观察",
    }
    return labels.get(source_type, "手动观察")


def _summarize_persona_source(content: str) -> str:
    text = content.strip().replace("\n", " ")
    if not text:
        return ""
    return f"客户公开资料显示：{text[:180]}"


def _ip_content_payload(item: IpContentRecord) -> dict:
    return {
        "id": item.id,
        "theme": item.theme,
        "channel": item.channel,
        "content": item.content,
        "created_at": item.created_at.isoformat(),
    }


def _company_material_payload(item: CompanyMaterial) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "source_type": item.source_type,
        "scope": item.scope,
        "approval_status": item.approval_status,
        "effective": item.effective,
        "tenant_id": item.tenant_id,
        "owner_user_id": item.owner_user_id,
        "content": item.content,
        "created_at": item.created_at.isoformat(),
    }


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "sales_userid": user.sales_userid,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "tenant_name": user.tenant.name if user.tenant else "",
        "approval_status": user.approval_status,
        "industry": user.industry or "",
        "customer_group": user.customer_group or "",
        "sales_guide": user.sales_guide or "",
        "memory_summary": user.memory_summary or "",
    }
