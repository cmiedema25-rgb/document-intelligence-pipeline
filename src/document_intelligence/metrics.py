"""Small, transparent evaluation helpers for extraction benchmarks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    matched_fields: int
    expected_fields: int
    predicted_fields: int
    line_item_count_match: bool

    @property
    def precision(self) -> float:
        return self.matched_fields / self.predicted_fields if self.predicted_fields else 0.0

    @property
    def recall(self) -> float:
        return self.matched_fields / self.expected_fields if self.expected_fields else 0.0

    @property
    def f1(self) -> float:
        denominator = self.precision + self.recall
        return 2 * self.precision * self.recall / denominator if denominator else 0.0

    def to_dict(self) -> dict[str, int | float | bool]:
        return {
            "matched_fields": self.matched_fields,
            "expected_fields": self.expected_fields,
            "predicted_fields": self.predicted_fields,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "line_item_count_match": self.line_item_count_match,
        }


def _field_values(payload: Mapping[str, Any]) -> dict[str, object]:
    raw_fields = payload.get("fields", {})
    if not isinstance(raw_fields, Mapping):
        raise ValueError("Evaluation payload fields must be an object")
    values: dict[str, object] = {}
    for name, field in raw_fields.items():
        if isinstance(field, Mapping) and "value" in field:
            values[str(name)] = field["value"]
        else:
            values[str(name)] = field
    return values


def evaluate(predicted: Mapping[str, Any], expected: Mapping[str, Any]) -> EvaluationMetrics:
    """Score normalized field equality and extracted line-item count."""

    predicted_fields = _field_values(predicted)
    expected_fields = _field_values(expected)
    # Metadata confidence is intentionally excluded from business-field scoring.
    predicted_fields.pop("document_type_confidence", None)
    expected_fields.pop("document_type_confidence", None)
    matched = sum(
        1
        for name, expected_value in expected_fields.items()
        if name in predicted_fields and predicted_fields[name] == expected_value
    )
    predicted_items = predicted.get("line_items", [])
    expected_items = expected.get("line_items", [])
    if not isinstance(predicted_items, list) or not isinstance(expected_items, list):
        raise ValueError("line_items must be arrays")
    return EvaluationMetrics(
        matched_fields=matched,
        expected_fields=len(expected_fields),
        predicted_fields=len(predicted_fields),
        line_item_count_match=len(predicted_items) == len(expected_items),
    )
