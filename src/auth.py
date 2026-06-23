from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta

import streamlit as st

from src.app_config import AppConfig


SESSION_KEY = "auth_state"


def ensure_auth_state() -> None:
    st.session_state.setdefault(
        SESSION_KEY,
        {
            "authenticated": False,
            "username": "",
            "expires_at": None,
        },
    )


def is_authenticated(config: AppConfig) -> bool:
    ensure_auth_state()
    state = st.session_state[SESSION_KEY]
    if not state["authenticated"]:
        return False

    expires_at = state.get("expires_at")
    if not expires_at:
        return False

    if datetime.utcnow() > datetime.fromisoformat(expires_at):
        logout()
        return False

    refresh_session(config)
    return True


def try_login(username: str, password: str, config: AppConfig) -> bool:
    username_ok = hmac.compare_digest(username.strip(), config.app_username)
    password_ok = verify_password(password, config)
    if not (username_ok and password_ok):
        return False

    st.session_state[SESSION_KEY] = {
        "authenticated": True,
        "username": config.app_username,
        "expires_at": _expiry_timestamp(config),
    }
    return True


def logout() -> None:
    st.session_state[SESSION_KEY] = {
        "authenticated": False,
        "username": "",
        "expires_at": None,
    }


def refresh_session(config: AppConfig) -> None:
    if SESSION_KEY in st.session_state:
        st.session_state[SESSION_KEY]["expires_at"] = _expiry_timestamp(config)


def verify_password(password: str, config: AppConfig) -> bool:
    if config.app_password_hash:
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest().lower()
        return hmac.compare_digest(digest, config.app_password_hash)
    return hmac.compare_digest(password, config.app_password)


def _expiry_timestamp(config: AppConfig) -> str:
    return (datetime.utcnow() + timedelta(minutes=config.session_timeout_minutes)).isoformat()
