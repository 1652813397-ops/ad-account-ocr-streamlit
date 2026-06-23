from __future__ import annotations

import streamlit as st

from src.app_config import AppConfig
from src.auth import is_authenticated, logout, try_login


def render_access_gate(config: AppConfig) -> bool:
    if not config.auth_enabled:
        return True

    if is_authenticated(config):
        with st.sidebar:
            st.success("已通过访问验证")
            st.caption(f"账号：`{config.app_username}`")
            if st.button("退出登录", use_container_width=True):
                logout()
                st.rerun()
        return True

    st.markdown("<div class='login-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>共享登录入口</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-caption'>请输入账号和访问密码后进入共享网页。建议在公网部署时改为你自己的账号密码或哈希密码。</div>",
        unsafe_allow_html=True,
    )

    with st.form("access_gate_form"):
        username = st.text_input("账号", value=config.app_username)
        password = st.text_input("访问密码", type="password")
        submitted = st.form_submit_button("进入系统", use_container_width=True)

    if submitted:
        if try_login(username, password, config):
            st.rerun()
        else:
            st.error("账号或访问密码不正确。")

    st.markdown("</div>", unsafe_allow_html=True)
    return False
