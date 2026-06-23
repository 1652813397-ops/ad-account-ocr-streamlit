from __future__ import annotations

import json
import uuid

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.models import OCRRules
from src.text_utils import format_output_value


def _should_render_zero_for_empty(field_name: str, rules: OCRRules) -> bool:
    rule = rules.fields[field_name]
    return bool(rules.settings.get("empty_numeric_as_zero", False)) and rule.data_type != "string"


def format_field_output(value: object, field_name: str, rules: OCRRules) -> str:
    if value in (None, "") and _should_render_zero_for_empty(field_name, rules):
        return "0"
    return format_output_value(value)


def build_detail_dataframe(results: list[dict], rules: OCRRules) -> pd.DataFrame:
    rows = []
    for item in results:
        row = {
            "图片": item["image_name"],
            "来源": item["source"],
            "状态": item["status"],
        }
        for field_name in rules.field_order:
            row[rules.fields[field_name].display_name] = format_field_output(
                item["fields"].get(field_name),
                field_name,
                rules,
            )
        row["错误日志"] = " | ".join(item["logs"])
        rows.append(row)

    return pd.DataFrame(rows)


def build_summary_metrics(results: list[dict], rules: OCRRules) -> dict[str, object]:
    metrics: dict[str, object] = {}

    for field_name in rules.field_order:
        rule = rules.fields[field_name]
        if rule.data_type == "string":
            metrics[field_name] = len(
                [item for item in results if item["fields"].get(field_name) not in (None, "")]
            )
        else:
            metrics[field_name] = sum(
                float(item["fields"].get(field_name) or 0)
                for item in results
            )

    return metrics


def build_summary_dataframe(summary_metrics: dict[str, object], rules: OCRRules) -> pd.DataFrame:
    rows = []
    for field_name in rules.field_order:
        if field_name == "account_id":
            continue
        rows.append(
            {
                "字段": rules.fields[field_name].display_name,
                "汇总值": format_output_value(summary_metrics.get(field_name)),
            }
        )
    return pd.DataFrame(rows)


def build_copy_block(results: list[dict], summary_metrics: dict[str, object], rules: OCRRules) -> str:
    lines: list[str] = []

    for field_name in rules.field_order:
        label = rules.fields[field_name].display_name
        lines.append(f"{label}：")
        for item in results:
            value = format_field_output(item["fields"].get(field_name), field_name, rules)
            if value:
                lines.append(value)
        lines.append("")

    lines.append("汇总：")
    for field_name in rules.field_order:
        if field_name == "account_id":
            continue
        label = rules.fields[field_name].display_name
        lines.append(f"{label}：{format_output_value(summary_metrics.get(field_name))}")

    return "\n".join(lines).strip()


def render_copy_button(copy_text: str) -> None:
    button_id = f"copy-btn-{uuid.uuid4().hex}"
    text_payload = json.dumps(copy_text).replace("</", "<\\/")
    components.html(
        f"""
        <div style="margin-top: 8px;">
          <button id="{button_id}" style="
            background: #0f62fe;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            cursor: pointer;
            font-size: 14px;
          ">
            一键复制结果
          </button>
          <span id="{button_id}-status" style="margin-left: 12px; color: #1f2937;"></span>
        </div>
        <script>
          const button = document.getElementById("{button_id}");
          const status = document.getElementById("{button_id}-status");
          const payload = {text_payload};
          button.addEventListener("click", async () => {{
            try {{
              await navigator.clipboard.writeText(payload);
              status.textContent = "已复制到剪贴板";
            }} catch (err) {{
              status.textContent = "复制失败，请手动复制文本框内容";
            }}
          }});
        </script>
        """,
        height=60,
    )


def render_sidebar_notes() -> None:
    st.sidebar.info("字段别名和规则可在 config/ocr_rules.yaml 中扩展。")
