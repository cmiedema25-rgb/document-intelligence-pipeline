"""High-level document processing, validation, and provenance."""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation

from document_intelligence.extractor import classify_document, extract_fields, extract_line_items
from document_intelligence.models import (
    Evidence,
    ExtractedField,
    ExtractionResult,
    LineItem,
    ProcessingSummary,
    SourceDocument,
    ValidationSummary,
)
from document_intelligence.normalization import NORMALIZATION_VERSION, normalize_document


def _as_decimal(fields: dict[str, ExtractedField], name: str) -> Decimal | None:
    field = fields.get(name)
    if field is None or field.value is None:
        return None
    try:
        return Decimal(str(field.value))
    except (InvalidOperation, ValueError):
        return None


def _money(value: Decimal | None) -> str | None:
    return None if value is None else f"{value.quantize(Decimal('0.01')):.2f}"


def validate_totals(
    fields: dict[str, ExtractedField], line_items: list[LineItem]
) -> tuple[ValidationSummary, list[str]]:
    warnings: list[str] = []
    line_subtotal = sum((Decimal(item.amount) for item in line_items), Decimal("0"))
    reported_subtotal = _as_decimal(fields, "subtotal")
    tax = _as_decimal(fields, "tax") or Decimal("0")
    reported_total = _as_decimal(fields, "total")

    calculated_subtotal: Decimal | None = line_subtotal if line_items else reported_subtotal
    calculated_total = calculated_subtotal + tax if calculated_subtotal is not None else None
    difference = (
        reported_total - calculated_total
        if reported_total is not None and calculated_total is not None
        else None
    )
    balanced = abs(difference) <= Decimal("0.01") if difference is not None else None

    if reported_subtotal is not None and line_items:
        subtotal_difference = abs(reported_subtotal - line_subtotal)
        if subtotal_difference > Decimal("0.01"):
            warnings.append(
                "Reported subtotal differs from the sum of extracted line items by "
                f"{subtotal_difference:.2f}."
            )
    if balanced is False:
        warnings.append(
            f"Reported total differs from the calculated total by {abs(difference):.2f}."
        )

    return (
        ValidationSummary(
            balanced=balanced,
            calculated_subtotal=_money(calculated_subtotal),
            calculated_total=_money(calculated_total),
            reported_total=_money(reported_total),
            difference=_money(difference),
        ),
        warnings,
    )


class DocumentPipeline:
    """Run classification, extraction, evidence capture, and validation."""

    schema_version = "1.0"

    def extract(self, source: SourceDocument) -> ExtractionResult:
        normalized = normalize_document(source)
        document_type, classification_confidence = classify_document(normalized)
        fields = extract_fields(normalized, document_type)
        line_items = extract_line_items(normalized.blocks)
        validation, warnings = validate_totals(fields, line_items)

        required = {
            "invoice": ("invoice_number", "invoice_date", "total"),
            "purchase_order": ("purchase_order_number", "total"),
        }.get(document_type, ())
        missing = [name for name in required if name not in fields]
        if missing:
            warnings.append(f"Missing expected fields: {', '.join(missing)}.")
        if not line_items and document_type in {"invoice", "purchase_order"}:
            warnings.append("No line items were extracted.")
        if document_type == "unknown":
            warnings.append("Document type could not be classified with sufficient evidence.")

        digest = hashlib.sha256(normalized.text.encode("utf-8")).hexdigest()
        fields["document_type_confidence"] = ExtractedField(
            value=round(classification_confidence, 3),
            confidence=classification_confidence,
            evidence=(
                # Classification is document-level; the first block is the compact audit anchor.
                Evidence(
                    block_id=normalized.blocks[0].id,
                    page=normalized.blocks[0].page,
                    text=normalized.blocks[0].text,
                    bbox=normalized.blocks[0].bbox,
                ),
            ),
        )
        return ExtractionResult(
            schema_version=self.schema_version,
            document_id=f"sha256:{digest}",
            document_type=document_type,
            fields=fields,
            line_items=line_items,
            validation=validation,
            processing=ProcessingSummary(
                normalization_version=NORMALIZATION_VERSION,
                block_count=len(normalized.blocks),
                page_count=normalized.page_count,
                source_name=normalized.source_name,
            ),
            warnings=warnings,
        )
