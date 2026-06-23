from __future__ import annotations

import streamlit as st

from src.app_config import AppConfig
from src.models import OCRRules
from src.presenter import format_field_output


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 215, 167, 0.55), transparent 34%),
                radial-gradient(circle at top right, rgba(170, 208, 255, 0.45), transparent 28%),
                linear-gradient(180deg, #f7f1ea 0%, #eef4ff 100%);
            color: #1f2937;
            font-family: "Segoe UI Variable", "Microsoft YaHei UI", "PingFang SC", sans-serif;
        }
        [data-testid="stHeader"] {
            background: rgba(247, 241, 234, 0.75);
            backdrop-filter: blur(12px);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(18, 35, 56, 0.96) 0%, rgba(28, 55, 89, 0.96) 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f5f7fb !important;
        }
        .hero-shell {
            padding: 1.6rem 1.8rem;
            border-radius: 28px;
            background: linear-gradient(140deg, rgba(16, 33, 52, 0.95), rgba(32, 76, 114, 0.92));
            box-shadow: 0 24px 70px rgba(24, 39, 75, 0.22);
            color: #f5f7fb;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            display: inline-block;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            text-transform: uppercase;
        }
        .hero-title {
            margin: 0.9rem 0 0.35rem;
            font-size: 2.35rem;
            line-height: 1.1;
            font-weight: 800;
        }
        .hero-subtitle {
            margin: 0;
            max-width: 760px;
            color: rgba(245, 247, 251, 0.88);
            font-size: 1rem;
            line-height: 1.65;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.9rem;
            margin-top: 1.25rem;
        }
        .hero-pill {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .hero-pill-label {
            font-size: 0.8rem;
            color: rgba(245, 247, 251, 0.72);
            margin-bottom: 0.25rem;
        }
        .hero-pill-value {
            font-size: 1.02rem;
            font-weight: 700;
        }
        .section-card {
            background: rgba(255, 255, 255, 0.68);
            border-radius: 22px;
            padding: 1rem 1.1rem 1.15rem;
            border: 1px solid rgba(17, 24, 39, 0.06);
            box-shadow: 0 18px 45px rgba(31, 41, 55, 0.08);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.9rem;
            margin: 0.5rem 0 1rem;
        }
        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(247, 250, 255, 0.92));
            border-radius: 20px;
            padding: 1rem;
            border: 1px solid rgba(20, 42, 74, 0.08);
            min-height: 110px;
        }
        .metric-label {
            font-size: 0.82rem;
            color: #5d6b7d;
            margin-bottom: 0.45rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #13263d;
        }
        .metric-helper {
            margin-top: 0.45rem;
            color: #6b7280;
            font-size: 0.82rem;
        }
        .login-panel {
            max-width: 480px;
            margin: 7vh auto 0;
            padding: 2rem;
            border-radius: 28px;
            background: rgba(255,255,255,0.82);
            box-shadow: 0 30px 80px rgba(15, 23, 42, 0.18);
            border: 1px solid rgba(15, 23, 42, 0.08);
        }
        .login-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.45rem;
            color: #16283f;
        }
        .login-caption {
            color: #5c6879;
            margin-bottom: 1rem;
            line-height: 1.6;
        }
        .status-banner {
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.65);
            border: 1px dashed rgba(20, 42, 74, 0.14);
            margin-top: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(config: AppConfig, results_count: int) -> None:
    public_url = config.public_base_url or "支持局域网 / 公网部署"
    st.markdown(
        f"""
        <div class="hero-shell">
          <div class="hero-kicker">{config.app_badge}</div>
          <div class="hero-title">{config.app_title}</div>
          <p class="hero-subtitle">{config.app_subtitle}</p>
          <div class="hero-grid">
            <div class="hero-pill">
              <div class="hero-pill-label">协作模式</div>
              <div class="hero-pill-value">{config.app_brand}</div>
            </div>
            <div class="hero-pill">
              <div class="hero-pill-label">当前结果数</div>
              <div class="hero-pill-value">{results_count}</div>
            </div>
            <div class="hero-pill">
              <div class="hero-pill-label">部署入口</div>
              <div class="hero-pill-value">{public_url}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards(results: list[dict], summary_metrics: dict[str, object], rules: OCRRules) -> None:
    cards: list[str] = []
    account_count = len([item for item in results if item["fields"].get("account_id") not in (None, "")])
    cards.append(
        _build_metric_card(
            label="有效账户",
            value=str(account_count),
            helper="去重后参与汇总的账户数量",
        )
    )

    for field_name in rules.field_order:
        if field_name == "account_id":
            continue
        cards.append(
            _build_metric_card(
                label=rules.fields[field_name].display_name,
                value=format_field_output(summary_metrics.get(field_name), field_name, rules),
                helper="自动汇总结果",
            )
        )

    st.markdown(f"<div class='metric-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def wrap_section_start() -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)


def wrap_section_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_status_banner(message: str) -> None:
    st.markdown(f"<div class='status-banner'>{message}</div>", unsafe_allow_html=True)


def _build_metric_card(label: str, value: str, helper: str) -> str:
    return (
        "<div class='metric-card'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div>"
        f"<div class='metric-helper'>{helper}</div>"
        "</div>"
    )
