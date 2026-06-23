from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd
import streamlit as st

from src.app_config import load_app_config
from src.config_loader import load_rules
from src.exporter import export_to_excel
from src.extractor import AdDataExtractor
from src.ocr_engine import OCRProcessingError, get_ocr_processor
from src.presenter import (
    build_copy_block,
    build_detail_dataframe,
    build_summary_dataframe,
    build_summary_metrics,
    render_copy_button,
)
from src.web_access import render_access_gate
from src.ui import (
    inject_global_styles,
    render_hero,
    render_status_banner,
    render_summary_cards,
    wrap_section_end,
    wrap_section_start,
)


APP_CONFIG = load_app_config()

st.set_page_config(page_title=APP_CONFIG.app_title, page_icon="📊", layout="wide")


def reset_state() -> None:
    st.session_state["results"] = []
    st.session_state["logs"] = []
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1


def ensure_state() -> None:
    st.session_state.setdefault("results", [])
    st.session_state.setdefault("logs", [])
    st.session_state.setdefault("uploader_key", 0)


def process_files(uploaded_files: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rules = load_rules()
    extractor = AdDataExtractor(rules)
    ocr_processor = get_ocr_processor()

    results: list[dict[str, Any]] = []
    logs: list[str] = []

    progress = st.progress(0, text="开始 OCR 识别...")
    total = len(uploaded_files)

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        image_bytes = uploaded_file.getvalue()
        image_name = uploaded_file.name

        try:
            tokens, raw_lines = ocr_processor.extract_tokens(image_bytes, image_name=image_name)
            result = extractor.extract(image_name=image_name, tokens=tokens, raw_lines=raw_lines)
            results.append(result)
            if result["logs"]:
                logs.extend(result["logs"])
        except OCRProcessingError as exc:
            logs.append(f"[{image_name}] OCR 失败: {exc}")
            results.append(
                extractor.build_failed_result(
                    image_name=image_name,
                    error_message=str(exc),
                )
            )
        finally:
            progress.progress(index / total, text=f"正在处理: {image_name} ({index}/{total})")

    progress.empty()
    deduplicated = extractor.deduplicate_results(results)
    merged_logs: list[str] = []
    for item in deduplicated:
        merged_logs.extend(item["logs"])
    merged_logs.extend(log for log in logs if log not in merged_logs)
    return deduplicated, merged_logs


def render_header() -> None:
    render_hero(APP_CONFIG, len(st.session_state.get("results", [])))


def render_upload_area() -> list[Any]:
    wrap_section_start()
    st.subheader("1. 图片上传")
    col1, col2 = st.columns([4, 1])
    with col1:
        files = st.file_uploader(
            "拖拽或选择多张广告后台截图",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state['uploader_key']}",
            help="建议上传清晰的 Meta 中文后台截图，支持拖拽、多图批量上传和几十张连续处理。",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("清空", use_container_width=True):
            reset_state()
            st.rerun()
    render_status_banner("共享版支持团队多人访问；如需公网使用，优先部署到 Streamlit Community Cloud，也兼容 Docker / Nginx 方案。")
    wrap_section_end()
    return files


def render_action_bar(files: list[Any]) -> None:
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("开始识别", type="primary", use_container_width=True, disabled=not files):
            results, logs = process_files(files)
            st.session_state["results"] = results
            st.session_state["logs"] = logs
            st.rerun()
    with col2:
        if files:
            st.info(f"当前已上传 {len(files)} 张图片，可一次处理几十张。")


def render_results(results: list[dict[str, Any]], logs: list[str]) -> None:
    if not results:
        st.info("上传图片后点击“开始识别”，这里会显示识别预览和汇总结果。")
        return

    rules = load_rules()
    field_order = rules.field_order

    st.subheader("2. OCR识别结果预览")
    detail_df = build_detail_dataframe(results, rules)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    with st.expander("查看每张图片的原始 OCR 文本"):
        for item in results:
            st.markdown(f"**{item['image_name']}**")
            raw_text = "\n".join(item["raw_lines"]) if item["raw_lines"] else "无"
            st.text(raw_text)

    st.subheader("3. 汇总结果")
    deduped_rows = [item for item in results if item["status"] == "success" and item["fields"].get("account_id")]
    summary_metrics = build_summary_metrics(deduped_rows, rules)
    summary_df = build_summary_dataframe(summary_metrics, rules)
    copy_text = build_copy_block(deduped_rows, summary_metrics, rules)
    render_summary_cards(deduped_rows, summary_metrics, rules)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.text_area("结果文本", value=copy_text, height=360)
        render_copy_button(copy_text)
    with col2:
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        excel_bytes = export_to_excel(results, summary_metrics, rules)
        st.download_button(
            "导出Excel",
            data=excel_bytes,
            file_name="广告账户汇总结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if logs:
        st.subheader("4. 错误日志")
        for message in logs:
            st.error(message)

    failed_count = sum(1 for item in results if item["status"] != "success")
    missing_counts = defaultdict(int)
    for item in results:
        for field_name in field_order:
            if item["fields"].get(field_name) in (None, ""):
                missing_counts[field_name] += 1

    with st.expander("查看识别统计"):
        st.write(f"成功记录数: {len(deduped_rows)}")
        st.write(f"失败图片数: {failed_count}")
        stats_df = pd.DataFrame(
            [
                {
                    "字段": rules.fields[name].display_name,
                    "缺失次数": missing_counts[name],
                }
                for name in field_order
            ]
        )
        st.dataframe(stats_df, use_container_width=True, hide_index=True)


def main() -> None:
    ensure_state()
    inject_global_styles()
    if not render_access_gate(APP_CONFIG):
        return
    render_header()
    st.sidebar.markdown(f"### {APP_CONFIG.app_brand}")
    st.sidebar.info("字段规则可在 `config/ocr_rules.yaml` 中继续扩展。")
    st.sidebar.caption(APP_CONFIG.support_message)
    if APP_CONFIG.public_base_url:
        st.sidebar.code(APP_CONFIG.public_base_url)
    files = render_upload_area()
    render_action_bar(files)
    render_results(st.session_state["results"], st.session_state["logs"])


if __name__ == "__main__":
    main()
