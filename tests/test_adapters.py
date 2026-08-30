import json
from pathlib import Path

import pytest

from document_intelligence.adapters import load_document, source_from_payload, source_from_text


def test_text_adapter_creates_stable_line_ids() -> None:
    source = source_from_text("first\n\nsecond")
    assert [block.id for block in source.blocks] == ["line-0001", "line-0003"]


def test_ocr_adapter_sorts_using_layout() -> None:
    payload = {
        "blocks": [
            {"id": "bottom", "page": 1, "text": "second", "bbox": [0, 0.8, 1, 0.1]},
            {"id": "top", "page": 1, "text": "first", "bbox": [0, 0.1, 1, 0.1]},
        ]
    }
    source = source_from_payload(payload)
    assert [block.id for block in source.blocks] == ["top", "bottom"]


def test_ocr_adapter_rejects_duplicate_ids() -> None:
    payload = {"blocks": [{"id": "same", "text": "a"}, {"id": "same", "text": "b"}]}
    with pytest.raises(ValueError, match="Duplicate"):
        source_from_payload(payload)


def test_load_document_reads_ocr_json(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text(json.dumps({"blocks": [{"text": "Invoice Number: INV-1"}]}))
    assert load_document(path).blocks[0].text == "Invoice Number: INV-1"


def test_load_document_rejects_unknown_extension(tmp_path: Path) -> None:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"hello")
    with pytest.raises(ValueError, match="Unsupported"):
        load_document(path)
