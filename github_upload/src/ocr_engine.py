from __future__ import annotations

import os
from io import BytesIO

import numpy as np
import streamlit as st

# Avoid oneDNN fused_conv2d crashes seen on some Windows CPU environments.
os.environ.setdefault("FLAGS_use_mkldnn", "0")

from paddleocr import PaddleOCR
from PIL import Image

from src.models import OCRToken
from src.text_utils import normalize_text


class OCRProcessingError(RuntimeError):
    """OCR processing failed."""


class OCRProcessor:
    def __init__(self) -> None:
        self.engine = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=False,
            use_gpu=False,
        )

    def extract_tokens(self, image_bytes: bytes, image_name: str = "") -> tuple[list[OCRToken], list[str]]:
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:  # pragma: no cover - PIL specifics depend on input
            raise OCRProcessingError(f"图片无法打开: {exc}") from exc

        try:
            result = self.engine.ocr(np.array(image), cls=True)
        except Exception as exc:  # pragma: no cover - Paddle internals vary by environment
            raise OCRProcessingError(f"PaddleOCR 识别异常: {exc}") from exc

        lines = result[0] if result else []
        if not lines:
            raise OCRProcessingError("未识别到任何文本")

        tokens: list[OCRToken] = []
        raw_lines: list[str] = []

        for line in lines:
            if not line or len(line) < 2:
                continue

            box = line[0]
            text, confidence = line[1]
            normalized = normalize_text(text)
            raw_lines.append(normalized)

            x_values = [point[0] for point in box]
            y_values = [point[1] for point in box]
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)

            tokens.append(
                OCRToken(
                    text=text,
                    confidence=float(confidence),
                    box=box,
                    normalized_text=normalized,
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                    center_x=(x_min + x_max) / 2,
                    center_y=(y_min + y_max) / 2,
                    width=max(x_max - x_min, 1.0),
                    height=max(y_max - y_min, 1.0),
                )
            )

        if not tokens:
            raise OCRProcessingError(f"{image_name or '图片'} 未生成有效 OCR token")

        return tokens, raw_lines


@st.cache_resource(show_spinner=False)
def get_ocr_processor() -> OCRProcessor:
    return OCRProcessor()
