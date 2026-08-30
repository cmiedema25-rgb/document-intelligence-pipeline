"""OCR-oriented text normalization with layout preservation."""

from __future__ import annotations

import re
import unicodedata

from document_intelligence.models import OcrBlock, SourceDocument

NORMALIZATION_VERSION = "2026-08"

_SPACE_RE = re.compile(r"[\t\u00a0 ]+")
_ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200d\ufeff]")
_DASH_RE = re.compile(r"[\u2010-\u2015\u2212]")


def normalize_text(text: str) -> str:
    """Normalize common OCR artifacts without destroying line boundaries."""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _ZERO_WIDTH_RE.sub("", normalized)
    normalized = _DASH_RE.sub("-", normalized)
    normalized = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "", normalized)
    lines = [_SPACE_RE.sub(" ", line).strip() for line in normalized.split("\n")]
    return "\n".join(line for line in lines if line)


def normalize_document(source: SourceDocument) -> SourceDocument:
    """Normalize blocks and split embedded newlines into traceable child blocks."""

    blocks: list[OcrBlock] = []
    for block in source.blocks:
        normalized = normalize_text(block.text)
        for index, line in enumerate(normalized.splitlines(), start=1):
            if not line:
                continue
            suffix = f".{index}" if "\n" in normalized else ""
            blocks.append(
                OcrBlock(
                    id=f"{block.id}{suffix}",
                    page=block.page,
                    text=line,
                    bbox=block.bbox,
                )
            )
    if not blocks:
        raise ValueError("Document contained no text after normalization")
    return SourceDocument(blocks=tuple(blocks), source_name=source.source_name)
