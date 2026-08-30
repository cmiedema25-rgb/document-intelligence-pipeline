"""Input adapters for text, OCR JSON, and optionally text-based PDFs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from document_intelligence.models import BoundingBox, OcrBlock, SourceDocument


def source_from_text(text: str, *, source_name: str = "inline.txt") -> SourceDocument:
    """Create a source document while retaining line-level evidence ids."""

    if not isinstance(text, str):
        raise TypeError("Document text must be a string")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = tuple(
        OcrBlock(id=f"line-{index:04d}", page=1, text=line)
        for index, line in enumerate(lines, start=1)
        if line.strip()
    )
    if not blocks:
        raise ValueError("Document text cannot be empty")
    return SourceDocument(blocks=blocks, source_name=source_name)


def _parse_bbox(value: object) -> BoundingBox | None:
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 4:
        x, y, width, height = value
        return BoundingBox(float(x), float(y), float(width), float(height))
    if isinstance(value, Mapping):
        required = ("x", "y", "width", "height")
        if all(key in value for key in required):
            return BoundingBox(*(float(value[key]) for key in required))
    raise ValueError("bbox must be [x, y, width, height] or a bounding-box object")


def source_from_payload(
    payload: Mapping[str, Any], *, source_name: str = "inline.ocr.json"
) -> SourceDocument:
    """Validate and load provider-neutral OCR JSON."""

    raw_blocks = payload.get("blocks")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        raise ValueError("OCR payload must contain a non-empty 'blocks' array")

    blocks: list[OcrBlock] = []
    ids: set[str] = set()
    for index, item in enumerate(raw_blocks, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"blocks[{index - 1}] must be an object")
        block_id = str(item.get("id") or f"block-{index:04d}")
        if block_id in ids:
            raise ValueError(f"Duplicate OCR block id: {block_id}")
        ids.add(block_id)
        try:
            page = int(item.get("page", 1))
            text = item["text"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid OCR block at index {index - 1}") from exc
        blocks.append(
            OcrBlock(
                id=block_id,
                page=page,
                text=text,
                bbox=_parse_bbox(item.get("bbox")),
            )
        )

    blocks.sort(
        key=lambda block: (
            block.page,
            block.bbox.y if block.bbox else float("inf"),
            block.bbox.x if block.bbox else float("inf"),
            block.id,
        )
    )
    return SourceDocument(blocks=tuple(blocks), source_name=source_name)


def _load_pdf(path: Path) -> SourceDocument:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - exercised only with optional dependency
        raise RuntimeError('PDF support requires: pip install -e ".[pdf]"') from exc

    blocks: list[OcrBlock] = []
    reader = PdfReader(path)
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                blocks.append(
                    OcrBlock(
                        id=f"page-{page_number:03d}-line-{line_number:04d}",
                        page=page_number,
                        text=line,
                    )
                )
    if not blocks:
        raise ValueError("PDF contains no extractable text; run OCR before extraction")
    return SourceDocument(blocks=tuple(blocks), source_name=path.name)


def load_document(path: str | Path) -> SourceDocument:
    """Load a supported document from disk."""

    resolved = Path(path)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    suffix = resolved.suffix.lower()
    if suffix in {".txt", ".md"}:
        return source_from_text(resolved.read_text(encoding="utf-8"), source_name=resolved.name)
    if suffix == ".json":
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("OCR JSON root must be an object")
        return source_from_payload(payload, source_name=resolved.name)
    if suffix == ".pdf":
        return _load_pdf(resolved)
    raise ValueError(f"Unsupported document type: {suffix or '(no extension)'}")
