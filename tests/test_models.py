import pytest

from document_intelligence.models import BoundingBox, ExtractedField, OcrBlock, SourceDocument


def test_bounding_box_rejects_negative_dimensions() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        BoundingBox(0, 0, -1, 2)


def test_ocr_block_requires_positive_page() -> None:
    with pytest.raises(ValueError, match="start at 1"):
        OcrBlock(id="block", page=0, text="hello")


def test_source_document_exposes_page_count_and_text() -> None:
    document = SourceDocument(
        blocks=(
            OcrBlock(id="a", page=1, text="first"),
            OcrBlock(id="b", page=3, text="last"),
        )
    )
    assert document.page_count == 3
    assert document.text == "first\nlast"


def test_extracted_field_requires_evidence() -> None:
    with pytest.raises(ValueError, match="evidence"):
        ExtractedField(value="x", confidence=0.9, evidence=())
