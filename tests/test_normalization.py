from document_intelligence.models import OcrBlock, SourceDocument
from document_intelligence.normalization import normalize_document, normalize_text


def test_normalize_text_handles_ocr_artifacts() -> None:
    raw = "Invo\u200bice\u00a0\u00a0Number:\u00a0ABC\u2014123\r\nTotal:  $10.00"
    assert normalize_text(raw) == "Invoice Number: ABC-123\nTotal: $10.00"


def test_normalize_text_repairs_soft_hyphenated_line_break() -> None:
    assert normalize_text("ware-\nhouse") == "warehouse"


def test_normalize_document_splits_multiline_blocks() -> None:
    source = SourceDocument(blocks=(OcrBlock(id="b1", page=1, text="one\ntwo"),))
    result = normalize_document(source)
    assert [block.id for block in result.blocks] == ["b1.1", "b1.2"]
    assert [block.text for block in result.blocks] == ["one", "two"]
