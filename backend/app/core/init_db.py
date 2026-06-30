from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.models import (
    AnalysisLog,
    ChatMessage,
    CompanyMaterial,
    Customer,
    CustomerTag,
    FollowRecord,
    GlobalSalesInsight,
    IpContentRecord,
    PersonaSource,
    ReplyFeedback,
    SyncState,
    Tenant,
    User,
)
from app.core.config import get_settings
from app.services.auth_service import AuthService


def init_db() -> None:
    _ = (
        AnalysisLog,
        ChatMessage,
        CompanyMaterial,
        Customer,
        CustomerTag,
        FollowRecord,
        GlobalSalesInsight,
        IpContentRecord,
        PersonaSource,
        ReplyFeedback,
        SyncState,
        Tenant,
        User,
    )
    Base.metadata.create_all(bind=engine)
    _ensure_tenant_columns()
    _ensure_company_material_columns()
    _ensure_customer_persona_columns()
    _ensure_persona_source_columns()
    _ensure_customer_lifecycle_columns()
    _seed_default_tenant_and_admin()


def _ensure_customer_persona_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("customers")}
    statements: list[str] = []
    if "persona_profile" not in columns:
        statements.append("ALTER TABLE customers ADD COLUMN persona_profile TEXT")
    if "persona_updated_at" not in columns:
        statements.append("ALTER TABLE customers ADD COLUMN persona_updated_at DATETIME")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_customer_lifecycle_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("customers")}
    statements: list[str] = []
    if "lifecycle_status" not in columns:
        statements.append("ALTER TABLE customers ADD COLUMN lifecycle_status VARCHAR(16) NOT NULL DEFAULT 'active'")
    if "closed_at" not in columns:
        statements.append("ALTER TABLE customers ADD COLUMN closed_at DATETIME NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_persona_source_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("persona_sources")}
    statements: list[str] = []
    if "source_url" not in columns:
        statements.append("ALTER TABLE persona_sources ADD COLUMN source_url VARCHAR(500) NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_tenant_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    statements: list[str] = []
    if "role" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'sales'")
    if "tenant_id" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN tenant_id BIGINT NULL")
    if "approval_status" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN approval_status VARCHAR(16) NOT NULL DEFAULT 'approved'")
    if "created_by_user_id" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN created_by_user_id BIGINT NULL")
    if "last_active_at" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN last_active_at DATETIME NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_company_material_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("company_materials")}
    statements: list[str] = []
    if "tenant_id" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN tenant_id BIGINT NULL")
    if "owner_user_id" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN owner_user_id BIGINT NULL")
    if "scope" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN scope VARCHAR(16) NOT NULL DEFAULT 'sales'")
    if "approval_status" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN approval_status VARCHAR(16) NOT NULL DEFAULT 'approved'")
    if "effective" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN effective BOOLEAN NOT NULL DEFAULT TRUE")
    if "reviewed_by_user_id" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN reviewed_by_user_id BIGINT NULL")
    if "reviewed_at" not in columns:
        statements.append("ALTER TABLE company_materials ADD COLUMN reviewed_at DATETIME NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _seed_default_tenant_and_admin() -> None:
    settings = get_settings()
    auth = AuthService(settings.app_secret_key)
    with Session(engine) as db:
        tenant = db.query(Tenant).filter(Tenant.name == "默认企业").one_or_none()
        if tenant is None:
            tenant = Tenant(name="默认企业", contact_name="系统默认", status="approved")
            db.add(tenant)
            db.flush()
        admin = db.query(User).filter(User.username == settings.platform_admin_username).one_or_none()
        if admin is None:
            admin = User(
                username=settings.platform_admin_username,
                password_hash=auth.hash_password(settings.platform_admin_password),
                display_name="平台管理员",
                role="platform_admin",
                tenant_id=None,
                approval_status="approved",
                memory_summary="",
            )
            db.add(admin)
            db.flush()
        elif settings.platform_admin_password != "change-platform-admin-password":
            admin.password_hash = auth.hash_password(settings.platform_admin_password)
        db.query(User).filter(User.role.is_(None)).update({User.role: "sales"}, synchronize_session=False)
        db.query(User).filter(User.approval_status.is_(None)).update(
            {User.approval_status: "approved"}, synchronize_session=False
        )
        db.query(User).filter(User.role == "sales", User.tenant_id.is_(None)).update(
            {User.tenant_id: tenant.id}, synchronize_session=False
        )
        db.query(CompanyMaterial).filter(CompanyMaterial.tenant_id.is_(None)).update(
            {
                CompanyMaterial.tenant_id: tenant.id,
                CompanyMaterial.scope: "sales",
                CompanyMaterial.approval_status: "approved",
                CompanyMaterial.effective: True,
            },
            synchronize_session=False,
        )
        db.commit()


if __name__ == "__main__":
    init_db()
