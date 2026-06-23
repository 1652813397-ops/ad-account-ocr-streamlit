from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OCRToken:
    text: str
    confidence: float
    box: list[list[float]]
    normalized_text: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    center_x: float
    center_y: float
    width: float
    height: float


@dataclass(slots=True)
class FieldRule:
    name: str
    display_name: str
    output_order: int
    data_type: str
    strategies: list[str]
    aliases: list[str]
    source_aliases: dict[str, list[str]] = field(default_factory=dict)
    regex_patterns: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceRule:
    name: str
    display_name: str
    keywords: list[str]


@dataclass(slots=True)
class OCRRules:
    settings: dict
    sources: dict[str, SourceRule]
    fields: dict[str, FieldRule]

    @property
    def field_order(self) -> list[str]:
        return [
            field.name
            for field in sorted(
                self.fields.values(),
                key=lambda item: item.output_order,
            )
        ]
