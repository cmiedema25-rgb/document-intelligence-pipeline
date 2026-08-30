from document_intelligence.metrics import evaluate


def test_evaluation_metrics_score_normalized_fields() -> None:
    predicted = {
        "fields": {"invoice_number": {"value": "INV-1"}, "total": {"value": "9.00"}},
        "line_items": [{"description": "Widget"}],
    }
    expected = {
        "fields": {"invoice_number": "INV-1", "total": "10.00"},
        "line_items": [{}],
    }
    metrics = evaluate(predicted, expected)
    assert metrics.matched_fields == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert metrics.line_item_count_match is True
