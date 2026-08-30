from document_intelligence.adapters import source_from_text
from document_intelligence.extractor import (
    classify_document,
    extract_fields,
    extract_line_items,
    normalize_amount,
    normalize_date,
)


def test_date_and_amount_normalization() -> None:
    assert normalize_date("August 15, 2026") == "2026-08-15"
    assert normalize_date("08/15/2026") == "2026-08-15"
    assert normalize_amount("$1,234.50") == "1234.50"
    assert normalize_amount("(25.00)") == "-25.00"


def test_invoice_classification_and_core_fields() -> None:
    source = source_from_text(
        "NORTHSTAR SUPPLY\nInvoice Number: INV-2026-9\nInvoice Date: 2026-08-15\n"
        "Subtotal: $10.00\nTax: $0.80\nTotal Due: $10.80"
    )
    document_type, confidence = classify_document(source)
    fields = extract_fields(source, document_type)
    assert document_type == "invoice"
    assert confidence > 0.8
    assert fields["invoice_number"].value == "INV-2026-9"
    assert fields["total"].value == "10.80"


def test_purchase_order_classification() -> None:
    source = source_from_text("ACME PARTS\nPURCHASE ORDER\nP.O. Number: PO-77\nTotal: $5.00")
    document_type, _ = classify_document(source)
    fields = extract_fields(source, document_type)
    assert document_type == "purchase_order"
    assert fields["purchase_order_number"].value == "PO-77"


def test_line_items_include_evidence_and_arithmetic_confidence() -> None:
    source = source_from_text(
        "Description | Qty | Unit Price | Amount\nWidget | 2 | $4.50 | $9.00\n"
        "Odd Item | 2 | $5.00 | $8.00"
    )
    items = extract_line_items(source.blocks)
    assert len(items) == 2
    assert items[0].description == "Widget"
    assert items[0].confidence == 0.98
    assert items[1].confidence == 0.82
    assert items[0].evidence[0].block_id == "line-0002"
