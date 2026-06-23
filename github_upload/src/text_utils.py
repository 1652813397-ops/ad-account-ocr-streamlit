from __future__ import annotations

import math
import re
from typing import Iterable

from rapidfuzz import fuzz


FULLWIDTH_MAP = str.maketrans(
    {
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
        "．": ".",
        "，": ",",
        "：": ":",
        "（": "(",
        "）": ")",
        "－": "-",
        "＋": "+",
        "／": "/",
    }
)

CURRENCY_PATTERN = re.compile(r"[¥￥$€£]")
SPACE_PATTERN = re.compile(r"\s+")
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")


def to_halfwidth(text: str) -> str:
    return text.translate(FULLWIDTH_MAP)


def normalize_text(text: str) -> str:
    text = to_halfwidth(text or "")
    text = text.strip()
    text = SPACE_PATTERN.sub(" ", text)
    return text


def compact_text(text: str) -> str:
    normalized = normalize_text(text)
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", normalized).lower()


def match_alias(text: str, aliases: Iterable[str], threshold: int) -> bool:
    compact = compact_text(text)
    for alias in aliases:
        target = compact_text(alias)
        if not target:
            continue
        if target in compact:
            return True
        if fuzz.partial_ratio(compact, target) >= threshold:
            return True
    return False


def apply_numeric_corrections(text: str, corrections: dict[str, str]) -> str:
    updated = to_halfwidth(text)
    for source, target in corrections.items():
        updated = updated.replace(source, target)
    return updated


def cleanup_numeric_text(text: str, corrections: dict[str, str]) -> str:
    text = apply_numeric_corrections(text, corrections)
    text = normalize_text(text)
    text = CURRENCY_PATTERN.sub("", text)
    text = text.replace(",", "")
    text = text.replace(" ", "")
    return text


def extract_number_fragment(text: str, corrections: dict[str, str]) -> str | None:
    cleaned = cleanup_numeric_text(text, corrections)
    match = NUMBER_PATTERN.search(cleaned)
    return match.group(0) if match else None


def parse_field_value(text: str, data_type: str, corrections: dict[str, str]) -> str | int | float | None:
    if data_type == "string":
        cleaned = cleanup_numeric_text(text, corrections)
        digits = re.findall(r"\d+", cleaned)
        return "".join(digits) if digits else None

    fragment = extract_number_fragment(text, corrections)
    if fragment is None:
        return None

    try:
        if data_type == "int":
            return int(round(float(fragment)))
        if data_type == "float":
            value = float(fragment)
            return int(value) if math.isclose(value, int(value)) else round(value, 2)
    except ValueError:
        return None

    return fragment


def format_output_value(value: object) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)
