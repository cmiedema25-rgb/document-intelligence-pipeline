"""Evidence-first document extraction pipeline."""

from document_intelligence.adapters import load_document, source_from_payload, source_from_text
from document_intelligence.models import ExtractionResult, OcrBlock, SourceDocument
from document_intelligence.pipeline import DocumentPipeline

__all__ = [
    "DocumentPipeline",
    "ExtractionResult",
    "OcrBlock",
    "SourceDocument",
    "load_document",
    "source_from_payload",
    "source_from_text",
]

__version__ = "1.0.0"
