"""Minimal local HTTP API for the document extraction pipeline."""

from __future__ import annotations

import json
from collections.abc import Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from document_intelligence.adapters import source_from_payload, source_from_text
from document_intelligence.pipeline import DocumentPipeline

MAX_REQUEST_BYTES = 2 * 1024 * 1024


def extract_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract from an API payload containing either text or OCR blocks."""

    if "text" in payload:
        text = payload["text"]
        if not isinstance(text, str):
            raise ValueError("'text' must be a string")
        source = source_from_text(text, source_name="api.txt")
    elif "blocks" in payload:
        source = source_from_payload(payload, source_name="api.ocr.json")
    else:
        raise ValueError("Request must include either 'text' or 'blocks'")
    return DocumentPipeline().extract(source).to_dict()


class DocumentApiHandler(BaseHTTPRequestHandler):
    """JSON request handler with explicit size and content-type checks."""

    server_version = "DocumentIntelligence/1.0"

    def _send_json(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "version": "1.0.0"})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/v1/extract":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._send_json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "unsupported_media_type", "message": "Use application/json"},
            )
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = -1
        if content_length < 1 or content_length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "invalid_request_size", "max_bytes": MAX_REQUEST_BYTES},
            )
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, Mapping):
                raise ValueError("JSON body must be an object")
            result = extract_payload(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_document", "message": str(exc)},
            )
            return
        self._send_json(HTTPStatus.OK, result)

    def log_message(self, format: str, *args: object) -> None:
        # The demo service avoids logging document-derived request data.
        super().log_message(format, *args)


def create_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), DocumentApiHandler)


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = create_server(host, port)
    print(f"Document Intelligence API listening on http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
