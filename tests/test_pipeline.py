from pathlib import Path

from document_intelligence.adapters import load_document, source_from_text
from document_intelligence.pipeline import DocumentPipeline

SAMPLES = Path(__file__).parents[1] / "samples"


def test_sample_invoice_extracts_traceable_balanced_result() -> None:
    result = DocumentPipeline().extract(load_document(SAMPLES / "northstar-invoice.ocr.json"))
    payload = result.to_dict()
    assert payload["document_type"] == "invoice"
    assert payload["fields"]["invoice_number"]["value"] == "INV-2026-1042"
    assert payload["fields"]["invoice_date"]["value"] == "2026-08-15"
    assert payload["fields"]["total"]["value"] == "376.71"
    assert payload["fields"]["total"]["evidence"][0]["block_id"] == "b13"
    assert len(payload["line_items"]) == 2
    assert payload["validation"]["balanced"] is True
    assert payload["warnings"] == []
    assert payload["document_id"].startswith("sha256:")


def test_pipeline_reports_missing_fields_and_unbalanced_total() -> None:
    source = source_from_text(
        "TEST VENDOR\nInvoice Number: INV-500\nWidget | 1 | $10.00 | $10.00\n"
        "Tax: $1.00\nTotal: $15.00"
    )
    result = DocumentPipeline().extract(source)
    assert result.validation.balanced is False
    assert any("Missing expected fields" in warning for warning in result.warnings)
    assert any("calculated total" in warning for warning in result.warnings)


def test_pipeline_handles_unknown_document() -> None:
    result = DocumentPipeline().extract(source_from_text("A short unclassified note"))
    assert result.document_type == "unknown"
    assert any("could not be classified" in warning for warning in result.warnings)
