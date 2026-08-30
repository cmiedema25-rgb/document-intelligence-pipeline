import json
import threading
from http.client import HTTPConnection

import pytest

from document_intelligence.server import create_server, extract_payload


def test_extract_payload_accepts_text() -> None:
    result = extract_payload(
        {"text": "DEMO SUPPLY\nInvoice Number: INV-123\nInvoice Date: 2026-08-30\nTotal: $5.00"}
    )
    assert result["fields"]["invoice_number"]["value"] == "INV-123"


def test_extract_payload_requires_supported_input() -> None:
    with pytest.raises(ValueError, match="either"):
        extract_payload({"filename": "missing.pdf"})


def test_http_api_health_and_extract() -> None:
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        connection.request("GET", "/health")
        health = connection.getresponse()
        assert health.status == 200
        assert json.loads(health.read())["status"] == "ok"

        body = json.dumps(
            {"text": "DEMO SUPPLY\nInvoice Number: INV-9\nInvoice Date: 2026-08-30\nTotal: $7.00"}
        )
        connection.request("POST", "/v1/extract", body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["fields"]["invoice_number"]["value"] == "INV-9"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
