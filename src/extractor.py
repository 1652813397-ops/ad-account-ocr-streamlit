from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from src.models import FieldRule, OCRRules, OCRToken
from src.text_utils import format_output_value, match_alias, parse_field_value


class AdDataExtractor:
    def __init__(self, rules: OCRRules) -> None:
        self.rules = rules
        self.alias_threshold = int(self.rules.settings.get("alias_match_threshold", 82))
        self.row_tolerance_ratio = float(self.rules.settings.get("row_tolerance_ratio", 0.75))
        self.max_vertical_gap_ratio = float(self.rules.settings.get("max_vertical_gap_ratio", 4.5))
        self.max_horizontal_gap_ratio = float(self.rules.settings.get("max_horizontal_gap_ratio", 8.0))
        self.corrections = self.rules.settings.get("numeric_corrections", {})
        self.summary_keywords = ("总成效", "总花费", "共计", "已显示")

    def build_failed_result(self, image_name: str, error_message: str) -> dict[str, Any]:
        return {
            "image_name": image_name,
            "source": "未知",
            "status": "failed",
            "fields": {name: None for name in self.rules.field_order},
            "field_confidences": {name: 0.0 for name in self.rules.field_order},
            "raw_lines": [],
            "logs": [f"[{image_name}] {error_message}"],
        }

    def extract(self, image_name: str, tokens: list[OCRToken], raw_lines: list[str]) -> dict[str, Any]:
        source_name = self.detect_source(tokens)
        table_fields, table_confidences, table_header_fields = self.extract_table_row_values(tokens, source_name)
        fields: dict[str, Any] = {}
        field_confidences: dict[str, float] = {}
        logs: list[str] = []

        for field_name in self.rules.field_order:
            if table_fields.get(field_name) not in (None, ""):
                value = table_fields[field_name]
                confidence = table_confidences.get(field_name, 0.0)
            elif field_name in table_header_fields:
                value = None
                confidence = 0.0
            else:
                rule = self.rules.fields[field_name]
                value, confidence = self.extract_field_value(rule, tokens, source_name)
            fields[field_name] = value
            field_confidences[field_name] = confidence
            if value is None:
                logs.append(f"[{image_name}] 未识别字段: {self.rules.fields[field_name].display_name}")

        status = "success" if any(value not in (None, "") for value in fields.values()) else "failed"
        if not fields.get("account_id"):
            logs.append(f"[{image_name}] 未识别到账户ID，无法参与去重汇总。")

        return {
            "image_name": image_name,
            "source": source_name,
            "status": status,
            "fields": fields,
            "field_confidences": field_confidences,
            "raw_lines": raw_lines,
            "logs": logs,
        }

    def extract_table_row_values(
        self,
        tokens: list[OCRToken],
        source_display_name: str,
    ) -> tuple[dict[str, Any], dict[str, float], set[str]]:
        header_matches: list[tuple[str, OCRToken]] = []

        for field_name in self.rules.field_order:
            rule = self.rules.fields[field_name]
            aliases = list(rule.aliases)
            source_name = self._find_source_key_by_display(source_display_name)
            if source_name:
                aliases.extend(rule.source_aliases.get(source_name, []))

            for token in tokens:
                if match_alias(token.normalized_text, aliases, self.alias_threshold):
                    header_matches.append((field_name, token))

        if not header_matches:
            return {}, {}, set()

        header_row = self._find_header_row(header_matches)
        if not header_row:
            return {}, {}, set()

        data_row = self._find_first_data_row_below(tokens, header_row)
        if not data_row:
            return {}, {}, set(header_row)

        sorted_headers = sorted(header_row.items(), key=lambda item: item[1].center_x)
        extracted: dict[str, Any] = {}
        confidences: dict[str, float] = {}

        for index, (field_name, header_token) in enumerate(sorted_headers):
            left_bound = float("-inf")
            right_bound = float("inf")

            if index > 0:
                left_bound = (sorted_headers[index - 1][1].center_x + header_token.center_x) / 2
            if index < len(sorted_headers) - 1:
                right_bound = (header_token.center_x + sorted_headers[index + 1][1].center_x) / 2

            column_tokens = [
                token for token in data_row
                if left_bound <= token.center_x < right_bound
            ]
            if not column_tokens:
                continue

            rule = self.rules.fields[field_name]
            parsed_candidates: list[tuple[float, Any]] = []
            for token in column_tokens:
                parsed = parse_field_value(token.normalized_text, rule.data_type, self.corrections)
                if parsed is None:
                    continue

                x_distance = abs(token.center_x - header_token.center_x)
                x_score = 1 / (1 + x_distance)
                score = 0.7 + token.confidence * 0.2 + x_score * 0.1
                parsed_candidates.append((score, parsed))

            if parsed_candidates:
                best_score, best_value = max(parsed_candidates, key=lambda item: item[0])
                extracted[field_name] = best_value
                confidences[field_name] = round(best_score, 4)

        return extracted, confidences, set(header_row)

    def detect_source(self, tokens: list[OCRToken]) -> str:
        matched_scores: dict[str, int] = {}
        texts = [token.normalized_text for token in tokens]
        joined = " ".join(texts)

        for source_name, source_rule in self.rules.sources.items():
            score = 0
            for keyword in source_rule.keywords:
                if keyword.lower() in joined.lower():
                    score += 1
            matched_scores[source_name] = score

        best_source = max(matched_scores, key=matched_scores.get, default="")
        if best_source and matched_scores[best_source] > 0:
            return self.rules.sources[best_source].display_name
        return "未知"

    def extract_field_value(
        self,
        rule: FieldRule,
        tokens: list[OCRToken],
        source_display_name: str,
    ) -> tuple[Any, float]:
        aliases = list(rule.aliases)
        source_name = self._find_source_key_by_display(source_display_name)
        if source_name:
            aliases.extend(rule.source_aliases.get(source_name, []))

        candidates: list[tuple[float, Any]] = []
        label_tokens = [
            token for token in tokens if match_alias(token.normalized_text, aliases, self.alias_threshold)
        ]

        for label_token in label_tokens:
            for strategy in rule.strategies:
                match strategy:
                    case "inline":
                        candidate = self._extract_inline_candidate(label_token, rule, aliases)
                    case "same_line":
                        candidate = self._extract_same_line_candidate(label_token, tokens, rule)
                    case "below":
                        candidate = self._extract_below_candidate(label_token, tokens, rule)
                    case "regex_global":
                        candidate = self._extract_regex_global_candidate(tokens, rule)
                    case _:
                        candidate = None

                if candidate is not None:
                    candidates.append(candidate)

        if not candidates and "regex_global" in rule.strategies:
            global_candidate = self._extract_regex_global_candidate(tokens, rule)
            if global_candidate is not None:
                candidates.append(global_candidate)

        if not candidates:
            return None, 0.0

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_value = candidates[0]
        return best_value, round(best_score, 4)

    def deduplicate_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        anonymous: list[dict[str, Any]] = []

        for item in results:
            account_id = item["fields"].get("account_id")
            if account_id:
                grouped[str(account_id)].append(item)
            else:
                anonymous.append(item)

        deduped: list[dict[str, Any]] = []
        for account_id, items in grouped.items():
            if len(items) == 1:
                deduped.append(items[0])
                continue

            winner = max(items, key=self._record_quality_score)
            merged = self._merge_records(winner, items)
            merged["logs"].append(f"[{winner['image_name']}] 账户 {account_id} 检测到重复截图，已自动去重。")
            deduped.append(merged)

        deduped.extend(anonymous)
        return sorted(deduped, key=lambda item: item["image_name"])

    def _record_quality_score(self, item: dict[str, Any]) -> float:
        populated = sum(1 for value in item["fields"].values() if value not in (None, ""))
        confidence = sum(item["field_confidences"].values())
        return populated * 10 + confidence

    def _merge_records(self, winner: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        merged_fields = dict(winner["fields"])
        merged_confidences = dict(winner["field_confidences"])
        merged_logs = list(winner["logs"])
        merged_raw_lines = list(winner["raw_lines"])

        for item in items:
            merged_logs.extend(item["logs"])
            merged_raw_lines.extend([line for line in item["raw_lines"] if line not in merged_raw_lines])
            for field_name, value in item["fields"].items():
                current_value = merged_fields.get(field_name)
                if current_value in (None, "") and value not in (None, ""):
                    merged_fields[field_name] = value
                    merged_confidences[field_name] = item["field_confidences"].get(field_name, 0.0)

        merged = dict(winner)
        merged["fields"] = merged_fields
        merged["field_confidences"] = merged_confidences
        merged["logs"] = merged_logs
        merged["raw_lines"] = merged_raw_lines
        return merged

    def _find_source_key_by_display(self, display_name: str) -> str | None:
        for key, source in self.rules.sources.items():
            if source.display_name == display_name:
                return key
        return None

    def _find_header_row(
        self,
        header_matches: list[tuple[str, OCRToken]],
    ) -> dict[str, OCRToken]:
        grouped_rows: list[list[tuple[str, OCRToken]]] = []
        for field_name, token in sorted(header_matches, key=lambda item: item[1].center_y):
            placed = False
            for row in grouped_rows:
                row_center_y = sum(item[1].center_y for item in row) / len(row)
                row_height = sum(item[1].height for item in row) / len(row)
                tolerance = max(row_height * self.row_tolerance_ratio, 10.0)
                if abs(token.center_y - row_center_y) <= tolerance:
                    row.append((field_name, token))
                    placed = True
                    break
            if not placed:
                grouped_rows.append([(field_name, token)])

        best_row: dict[str, OCRToken] = {}
        for row in grouped_rows:
            deduped: dict[str, OCRToken] = {}
            for field_name, token in row:
                if field_name not in deduped or token.confidence > deduped[field_name].confidence:
                    deduped[field_name] = token
            if len(deduped) > len(best_row):
                best_row = deduped

        return best_row if len(best_row) >= 3 else {}

    def _find_first_data_row_below(
        self,
        tokens: list[OCRToken],
        header_row: dict[str, OCRToken],
    ) -> list[OCRToken]:
        header_tokens = list(header_row.values())
        header_center_y = sum(token.center_y for token in header_tokens) / len(header_tokens)
        header_height = sum(token.height for token in header_tokens) / len(header_tokens)
        rows = self._group_tokens_by_row(tokens)

        for row in rows:
            row_center_y = sum(token.center_y for token in row) / len(row)
            if row_center_y <= header_center_y + header_height * 0.8:
                continue

            row_text = " ".join(token.normalized_text for token in row)
            if any(keyword in row_text for keyword in self.summary_keywords):
                continue

            numeric_count = sum(
                1
                for token in row
                if any(
                    parse_field_value(token.normalized_text, self.rules.fields[field_name].data_type, self.corrections)
                    is not None
                    for field_name in self.rules.field_order
                )
            )
            if numeric_count >= 2:
                return row

        return []

    def _group_tokens_by_row(self, tokens: list[OCRToken]) -> list[list[OCRToken]]:
        grouped_rows: list[list[OCRToken]] = []
        for token in sorted(tokens, key=lambda item: item.center_y):
            placed = False
            for row in grouped_rows:
                row_center_y = sum(item.center_y for item in row) / len(row)
                row_height = sum(item.height for item in row) / len(row)
                tolerance = max(row_height * self.row_tolerance_ratio, 10.0)
                if abs(token.center_y - row_center_y) <= tolerance:
                    row.append(token)
                    placed = True
                    break
            if not placed:
                grouped_rows.append([token])
        return grouped_rows

    def _extract_inline_candidate(
        self,
        label_token: OCRToken,
        rule: FieldRule,
        aliases: list[str],
    ) -> tuple[float, Any] | None:
        value_text = label_token.normalized_text
        for alias in sorted(aliases, key=len, reverse=True):
            value_text = re.sub(re.escape(alias), " ", value_text, flags=re.IGNORECASE)

        parsed = parse_field_value(value_text, rule.data_type, self.corrections)
        if parsed is None:
            return None
        score = 0.75 + label_token.confidence * 0.25
        return score, parsed

    def _extract_same_line_candidate(
        self,
        label_token: OCRToken,
        tokens: list[OCRToken],
        rule: FieldRule,
    ) -> tuple[float, Any] | None:
        tolerance = max(label_token.height * self.row_tolerance_ratio, 8.0)
        max_horizontal_gap = max(label_token.width * self.max_horizontal_gap_ratio, 80.0)

        candidates: list[tuple[float, Any]] = []
        for token in tokens:
            if token is label_token:
                continue
            if token.center_x <= label_token.center_x:
                continue
            if abs(token.center_y - label_token.center_y) > tolerance:
                continue
            if token.x_min - label_token.x_max > max_horizontal_gap:
                continue

            parsed = parse_field_value(token.normalized_text, rule.data_type, self.corrections)
            if parsed is None:
                continue

            distance_score = 1 / (1 + max(token.x_min - label_token.x_max, 0))
            score = 0.6 + token.confidence * 0.25 + distance_score * 0.15
            candidates.append((score, parsed))

        return max(candidates, key=lambda item: item[0], default=None)

    def _extract_below_candidate(
        self,
        label_token: OCRToken,
        tokens: list[OCRToken],
        rule: FieldRule,
    ) -> tuple[float, Any] | None:
        max_vertical_gap = max(label_token.height * self.max_vertical_gap_ratio, 40.0)
        horizontal_tolerance = max(label_token.width * self.max_horizontal_gap_ratio, 80.0)

        candidates: list[tuple[float, Any]] = []
        for token in tokens:
            if token is label_token:
                continue
            if token.center_y <= label_token.center_y:
                continue
            if token.y_min - label_token.y_max > max_vertical_gap:
                continue
            if abs(token.center_x - label_token.center_x) > horizontal_tolerance:
                continue

            parsed = parse_field_value(token.normalized_text, rule.data_type, self.corrections)
            if parsed is None:
                continue

            distance_score = 1 / (1 + max(token.y_min - label_token.y_max, 0))
            score = 0.58 + token.confidence * 0.25 + distance_score * 0.17
            candidates.append((score, parsed))

        return max(candidates, key=lambda item: item[0], default=None)

    def _extract_regex_global_candidate(
        self,
        tokens: list[OCRToken],
        rule: FieldRule,
    ) -> tuple[float, Any] | None:
        patterns = [re.compile(pattern) for pattern in rule.regex_patterns]
        candidates: list[tuple[float, Any]] = []

        for token in tokens:
            text = token.normalized_text
            for pattern in patterns:
                match = pattern.search(text)
                if not match:
                    continue
                parsed = parse_field_value(match.group(0), rule.data_type, self.corrections)
                if parsed is None:
                    continue
                score = 0.45 + token.confidence * 0.3
                if rule.name == "account_id":
                    digit_count = len(format_output_value(parsed))
                    score += min(digit_count / 50, 0.2)
                candidates.append((score, parsed))

        return max(candidates, key=lambda item: item[0], default=None)
