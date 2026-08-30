"""Deterministic, evidence-linked business-document extraction."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from re import Pattern

from document_intelligence.models import (
    Evidence,
    ExtractedField,
    LineItem,
    OcrBlock,
    SourceDocument,
)

Normalizer = Callable[[str], str]


def _identity(value: str) -> str:
    return value.strip()


def normalize_date(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip().rstrip(".,"))
    for date_format in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(cleaned, date_format).date().isoformat()
        except ValueError:
            continue
    return cleaned


def normalize_amount(value: str) -> str:
    cleaned = re.sub(r"[^0-9.()-]", "", value)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    try:
        return f"{Decimal(cleaned).quantize(Decimal('0.01')):.2f}"
    except InvalidOperation as exc:
        raise ValueError(f"Invalid currency amount: {value}") from exc


def _evidence(block: OcrBlock) -> Evidence:
    return Evidence(block_id=block.id, page=block.page, text=block.text, bbox=block.bbox)


def _first_match(
    blocks: tuple[OcrBlock, ...],
    patterns: tuple[tuple[Pattern[str], float], ...],
    normalizer: Normalizer = _identity,
) -> ExtractedField | None:
    for pattern, confidence in patterns:
        for block in blocks:
            match = pattern.search(block.text)
            if match:
                return ExtractedField(
                    value=normalizer(match.group(1)),
                    confidence=confidence,
                    evidence=(_evidence(block),),
                )
    return None


_INVOICE_NUMBER_PATTERNS = (
    (
        re.compile(
            r"\binvoice\s*(?:number|no\.?|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]{2,})",
            re.IGNORECASE,
        ),
        0.99,
    ),
    (re.compile(r"^\s*invoice\s+([A-Z][A-Z0-9-]{3,})\s*$", re.IGNORECASE), 0.94),
)

_PURCHASE_ORDER_PATTERNS = (
    (
        re.compile(
            r"\b(?:purchase\s+order|P\.?O\.?)\s*(?:number|no\.?|#)?\s*[:#-]?\s*"
            r"([A-Z0-9][A-Z0-9-]{2,})",
            re.IGNORECASE,
        ),
        0.98,
    ),
)

_INVOICE_DATE_PATTERNS = (
    (
        re.compile(
            r"\b(?:invoice\s+date|date)\s*:\s*"
            r"([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            re.IGNORECASE,
        ),
        0.97,
    ),
)

_DUE_DATE_PATTERNS = (
    (
        re.compile(
            r"\bdue\s+date\s*:\s*"
            r"([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            re.IGNORECASE,
        ),
        0.98,
    ),
)

_AMOUNT_PATTERNS: dict[str, Pattern[str]] = {
    "subtotal": re.compile(
        r"^\s*subtotal\s*:?\s*(?:[A-Z]{3}\s*)?([$€£]?\s*[\d,]+\.\d{2})\s*$",
        re.IGNORECASE,
    ),
    "tax": re.compile(
        r"^\s*(?:sales\s+)?tax(?:\s*\([^)]*\))?\s*:?\s*"
        r"(?:[A-Z]{3}\s*)?([$€£]?\s*[\d,]+\.\d{2})\s*$",
        re.IGNORECASE,
    ),
    "total": re.compile(
        r"^\s*(?:invoice\s+)?total(?:\s+due)?\s*:?\s*"
        r"(?:[A-Z]{3}\s*)?([$€£]?\s*[\d,]+\.\d{2})\s*$",
        re.IGNORECASE,
    ),
}

_NON_VENDOR_RE = re.compile(
    r"invoice|purchase\s+order|bill\s+to|ship\s+to|date|due|email|phone|subtotal|total|tax|"
    r"description|quantity|\bqty\b|\|",
    re.IGNORECASE,
)


def classify_document(document: SourceDocument) -> tuple[str, float]:
    text = document.text.lower()
    invoice_score = 2 * len(re.findall(r"\binvoice\b", text))
    purchase_order_score = 2 * len(re.findall(r"\bpurchase\s+order\b", text))
    purchase_order_score += len(re.findall(r"\bp\.?o\.?\s*(?:number|no\.?|#)", text))
    if invoice_score == 0 and purchase_order_score == 0:
        return "unknown", 0.35
    if invoice_score >= purchase_order_score:
        return "invoice", min(0.99, 0.75 + invoice_score * 0.04)
    return "purchase_order", min(0.99, 0.75 + purchase_order_score * 0.04)


def _vendor_name(blocks: tuple[OcrBlock, ...]) -> ExtractedField | None:
    for block in blocks[:8]:
        value = block.text.strip(" :-")
        if len(value) < 3 or _NON_VENDOR_RE.search(value) or re.fullmatch(r"[-=\s]+", value):
            continue
        if re.search(r"@|https?://|www\.|\d{3}[-.) ]\d{3}", value, re.IGNORECASE):
            continue
        normalized = value.title() if value.isupper() else value
        return ExtractedField(value=normalized, confidence=0.86, evidence=(_evidence(block),))
    return None


def _currency(document: SourceDocument) -> ExtractedField | None:
    patterns = (
        (re.compile(r"\b(USD|CAD|EUR|GBP)\b", re.IGNORECASE), 0.98),
        (re.compile(r"(\$)\s*\d"), 0.9),
        (re.compile(r"(€)\s*\d"), 0.9),
        (re.compile(r"(£)\s*\d"), 0.9),
    )
    field = _first_match(document.blocks, patterns, lambda value: value.upper())
    if field is None:
        return None
    symbol_map = {"$": "USD", "€": "EUR", "£": "GBP"}
    if field.value in symbol_map:
        return ExtractedField(
            value=symbol_map[str(field.value)],
            confidence=field.confidence,
            evidence=field.evidence,
        )
    return field


def _amount_field(blocks: tuple[OcrBlock, ...], name: str) -> ExtractedField | None:
    pattern = _AMOUNT_PATTERNS[name]
    for block in blocks:
        match = pattern.match(block.text)
        if match:
            return ExtractedField(
                value=normalize_amount(match.group(1)),
                confidence=0.99,
                evidence=(_evidence(block),),
            )
    return None


def _parse_number(value: str) -> Decimal:
    cleaned = re.sub(r"[^0-9.()-]", "", value)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return Decimal(cleaned)


def extract_line_items(blocks: tuple[OcrBlock, ...]) -> list[LineItem]:
    """Extract pipe-delimited rows while excluding headers and totals."""

    results: list[LineItem] = []
    for block in blocks:
        if "|" not in block.text:
            continue
        parts = [part.strip() for part in block.text.strip(" |").split("|")]
        if len(parts) != 4:
            continue
        description, quantity_text, unit_price_text, amount_text = parts
        lowered = " ".join(parts).lower()
        if "description" in lowered and ("qty" in lowered or "quantity" in lowered):
            continue
        if not description or re.match(r"^(subtotal|tax|total)", description, re.IGNORECASE):
            continue
        try:
            quantity = float(_parse_number(quantity_text))
            unit_price = normalize_amount(unit_price_text)
            amount = normalize_amount(amount_text)
        except (InvalidOperation, ValueError):
            continue
        expected = Decimal(unit_price) * Decimal(str(quantity))
        reported = Decimal(amount)
        confidence = 0.98 if abs(expected - reported) <= Decimal("0.01") else 0.82
        results.append(
            LineItem(
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                confidence=confidence,
                evidence=(_evidence(block),),
            )
        )
    return results


def extract_fields(document: SourceDocument, document_type: str) -> dict[str, ExtractedField]:
    fields: dict[str, ExtractedField | None] = {
        "vendor_name": _vendor_name(document.blocks),
        "currency": _currency(document),
        "invoice_date": _first_match(document.blocks, _INVOICE_DATE_PATTERNS, normalize_date),
        "due_date": _first_match(document.blocks, _DUE_DATE_PATTERNS, normalize_date),
        "subtotal": _amount_field(document.blocks, "subtotal"),
        "tax": _amount_field(document.blocks, "tax"),
        "total": _amount_field(document.blocks, "total"),
    }
    if document_type == "invoice":
        fields["invoice_number"] = _first_match(document.blocks, _INVOICE_NUMBER_PATTERNS)
    if document_type == "purchase_order":
        fields["purchase_order_number"] = _first_match(
            document.blocks, _PURCHASE_ORDER_PATTERNS
        )
    return {name: field for name, field in fields.items() if field is not None}
