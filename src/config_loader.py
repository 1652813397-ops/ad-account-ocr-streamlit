from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from src.models import FieldRule, OCRRules, SourceRule


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "ocr_rules.yaml"


@lru_cache(maxsize=1)
def load_rules() -> OCRRules:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    sources = {
        name: SourceRule(
            name=name,
            display_name=value["display_name"],
            keywords=value.get("keywords", []),
        )
        for name, value in data.get("sources", {}).items()
    }

    fields = {
        name: FieldRule(
            name=name,
            display_name=value["display_name"],
            output_order=value["output_order"],
            data_type=value["data_type"],
            strategies=value.get("strategies", []),
            aliases=value.get("aliases", []),
            source_aliases=value.get("source_aliases", {}),
            regex_patterns=value.get("regex_patterns", []),
        )
        for name, value in data.get("fields", {}).items()
    }

    return OCRRules(
        settings=data.get("settings", {}),
        sources=sources,
        fields=fields,
    )
