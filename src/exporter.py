from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.models import OCRRules
from src.presenter import build_detail_dataframe, build_summary_dataframe


def export_to_excel(results: list[dict], summary_metrics: dict[str, object], rules: OCRRules) -> bytes:
    detail_df = build_detail_dataframe(results, rules)
    summary_df = build_summary_dataframe(summary_metrics, rules)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        detail_df.to_excel(writer, index=False, sheet_name="账户明细")
        summary_df.to_excel(writer, index=False, sheet_name="汇总数据")

    output.seek(0)
    return output.read()
