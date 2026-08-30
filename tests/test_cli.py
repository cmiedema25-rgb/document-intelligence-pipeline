from __future__ import annotations

import json
from pathlib import Path

from document_intelligence.cli import main


def test_benchmark_writes_reviewer_report(tmp_path: Path) -> None:
    report_path = tmp_path / "benchmark-report.json"

    exit_code = main(
        [
            "benchmark",
            "samples/benchmark.json",
            "--report",
            str(report_path),
        ]
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["passed"] is True
    assert report["case_count"] == 3
    assert report["summary"] == {
        "matched_fields": 23,
        "expected_fields": 23,
        "macro_precision": 1.0,
        "macro_recall": 1.0,
        "macro_f1": 1.0,
        "line_item_count_matches": 3,
    }
