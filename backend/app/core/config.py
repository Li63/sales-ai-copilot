from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sales AI Copilot"
    environment: str = "local"
    api_prefix: str = "/api"

    wechat_corp_id: str = Field(default="", alias="WECHAT_CORP_ID")
    wechat_agent_id: str = Field(default="", alias="WECHAT_AGENT_ID")
    wechat_app_secret: str = Field(default="", alias="WECHAT_APP_SECRET")
    wechat_archive_secret: str = Field(default="", alias="WECHAT_ARCHIVE_SECRET")
    wechat_public_key_ver: str = Field(default="", alias="WECHAT_PUBLIC_KEY_VER")
    wechat_rsa_private_key: str = Field(default="", alias="WECHAT_RSA_PRIVATE_KEY")
    wechat_trusted_domain: str = Field(default="", alias="WECHAT_TRUSTED_DOMAIN")

    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
    vision_api_key: str = Field(default="", alias="VISION_API_KEY")
    vision_base_url: str = Field(default="", alias="VISION_BASE_URL")
    vision_model: str = Field(default="", alias="VISION_MODEL")
    product_knowledge: str = Field(default="", alias="PRODUCT_KNOWLEDGE")

    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_db: str = Field(default="sales_agent", alias="MYSQL_DB")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    archive_client: str = Field(default="stub", alias="ARCHIVE_CLIENT")
    app_secret_key: str = Field(default="change-this-secret", alias="APP_SECRET_KEY")
    approval_enforcement: bool = Field(default=False, alias="APPROVAL_ENFORCEMENT")
    platform_admin_username: str = Field(default="platform_admin", alias="PLATFORM_ADMIN_USERNAME")
    platform_admin_password: str = Field(default="change-platform-admin-password", alias="PLATFORM_ADMIN_PASSWORD")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
