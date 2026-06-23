from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st


@dataclass(slots=True)
class AppConfig:
    app_title: str
    app_subtitle: str
    app_badge: str
    app_brand: str
    app_username: str
    app_password: str
    app_password_hash: str
    auth_enabled: bool
    session_timeout_minutes: int
    public_base_url: str
    support_message: str


def load_app_config() -> AppConfig:
    password = _get_config_value("APP_ACCESS_CODE", "")
    password_hash = _get_config_value("APP_ACCESS_CODE_HASH", "").lower()
    auth_enabled = _parse_bool(_get_config_value("APP_AUTH_ENABLED", "true"))
    if not password and not password_hash:
        auth_enabled = False

    return AppConfig(
        app_title=_get_config_value("APP_TITLE", "广告账户数据汇总工具") or "广告账户数据汇总工具",
        app_subtitle=_get_config_value(
            "APP_SUBTITLE",
            "面向 Meta 中文广告后台截图的 OCR 汇总平台，支持批量上传、自动识别、汇总导出与团队共享。",
        ),
        app_badge=_get_config_value("APP_BADGE", "Meta OCR Workspace") or "Meta OCR Workspace",
        app_brand=_get_config_value("APP_BRAND", "Team Edition") or "Team Edition",
        app_username=_get_config_value("APP_USERNAME", "admin") or "admin",
        app_password=password,
        app_password_hash=password_hash,
        auth_enabled=auth_enabled,
        session_timeout_minutes=max(int(_get_config_value("APP_SESSION_TIMEOUT_MINUTES", "720")), 10),
        public_base_url=_get_config_value("PUBLIC_BASE_URL", ""),
        support_message=_get_config_value(
            "APP_SUPPORT_MESSAGE",
            "如遇识别误差，请把截图样本补给管理员继续扩展规则。",
        ),
    )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_config_value(key: str, default: str) -> str:
    secret_value = _get_secret_value(key)
    if secret_value is not None:
        return str(secret_value).strip()
    return os.getenv(key, default).strip()


def _get_secret_value(key: str) -> str | None:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        return None
    return None
