"""Shared data models for document ingestion and extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Normalized or pixel bounding box emitted by an OCR provider."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("Bounding-box width and height must be non-negative")

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class OcrBlock:
    """A single OCR text block with optional layout coordinates."""

    id: str
    page: int
    text: str
    bbox: BoundingBox | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("OCR block id cannot be empty")
        if self.page < 1:
            raise ValueError("OCR page numbers start at 1")
        if not isinstance(self.text, str):
            raise TypeError("OCR block text must be a string")

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"id": self.id, "page": self.page, "text": self.text}
        if self.bbox is not None:
            result["bbox"] = self.bbox.to_dict()
        return result


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Provider-neutral document representation used by the pipeline."""

    blocks: tuple[OcrBlock, ...]
    source_name: str = "inline"

    def __post_init__(self) -> None:
        if not self.blocks:
            raise ValueError("A document must contain at least one text block")

    @property
    def page_count(self) -> int:
        return max(block.page for block in self.blocks)

    @property
    def text(self) -> str:
        return "\n".join(block.text for block in self.blocks)

    @property
    def suffix(self) -> str:
        return Path(self.source_name).suffix.lower()


@dataclass(frozen=True, slots=True)
class Evidence:
    """Source evidence supporting an extracted value."""

    block_id: str
    page: int
    text: str
    bbox: BoundingBox | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "block_id": self.block_id,
            "page": self.page,
            "text": self.text,
        }
        if self.bbox is not None:
            result["bbox"] = self.bbox.to_dict()
        return result


@dataclass(frozen=True, slots=True)
class ExtractedField:
    """A normalized value with confidence and traceable source evidence."""

    value: JsonScalar
    confidence: float
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.evidence:
            raise ValueError("Extracted fields require at least one evidence block")

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class LineItem:
    description: str
    quantity: float
    unit_price: str
    amount: str
    confidence: float
    evidence: tuple[Evidence, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount": self.amount,
            "confidence": round(self.confidence, 3),
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    balanced: bool | None
    calculated_subtotal: str | None
    calculated_total: str | None
    reported_total: str | None
    difference: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "balanced": self.balanced,
            "calculated_subtotal": self.calculated_subtotal,
            "calculated_total": self.calculated_total,
            "reported_total": self.reported_total,
            "difference": self.difference,
        }


@dataclass(frozen=True, slots=True)
class ProcessingSummary:
    normalization_version: str
    block_count: int
    page_count: int
    source_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalization_version": self.normalization_version,
            "block_count": self.block_count,
            "page_count": self.page_count,
            "source_name": self.source_name,
        }


@dataclass(slots=True)
class ExtractionResult:
    schema_version: str
    document_id: str
    document_type: str
    fields: dict[str, ExtractedField]
    line_items: list[LineItem]
    validation: ValidationSummary
    processing: ProcessingSummary
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "fields": {name: item.to_dict() for name, item in sorted(self.fields.items())},
            "line_items": [item.to_dict() for item in self.line_items],
            "validation": self.validation.to_dict(),
            "processing": self.processing.to_dict(),
            "warnings": list(self.warnings),
        }
