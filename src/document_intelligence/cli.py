"""Command-line interface for extraction, benchmarking, and local serving."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from document_intelligence.adapters import load_document
from document_intelligence.metrics import evaluate
from document_intelligence.pipeline import DocumentPipeline
from document_intelligence.server import serve


def _write_json(payload: object, output: Path | None, *, compact: bool) -> None:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
    )
    if output is None:
        print(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"{text}\n", encoding="utf-8")


def _extract(args: argparse.Namespace) -> int:
    source = load_document(args.input)
    result = DocumentPipeline().extract(source)
    _write_json(result.to_dict(), args.output, compact=args.compact)
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    manifest_path: Path = args.manifest
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark manifest requires a non-empty 'cases' array")

    results: list[dict[str, object]] = []
    all_passed = True
    for case in cases:
        if not isinstance(case, dict) or "input" not in case or "expected" not in case:
            raise ValueError("Each benchmark case requires input and expected paths")
        input_path = manifest_path.parent / str(case["input"])
        expected_path = manifest_path.parent / str(case["expected"])
        predicted = DocumentPipeline().extract(load_document(input_path)).to_dict()
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        metrics = evaluate(predicted, expected)
        passed = metrics.f1 >= args.minimum_f1 and metrics.line_item_count_match
        all_passed = all_passed and passed
        results.append(
            {
                "name": str(case.get("name", input_path.name)),
                **metrics.to_dict(),
                "passed": passed,
            }
        )

    report = {
        "minimum_f1": args.minimum_f1,
        "case_count": len(results),
        "passed": all_passed,
        "results": results,
    }
    _write_json(report, None, compact=False)
    return 0 if all_passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docintel",
        description="Extract structured, evidence-linked data from business documents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract one document")
    extract_parser.add_argument("input", type=Path, help=".txt, .md, .json, or optional .pdf")
    extract_parser.add_argument("-o", "--output", type=Path, help="Write JSON to this path")
    extract_parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    extract_parser.set_defaults(handler=_extract)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run a golden-data benchmark")
    benchmark_parser.add_argument("manifest", type=Path)
    benchmark_parser.add_argument("--minimum-f1", type=float, default=0.95)
    benchmark_parser.set_defaults(handler=_benchmark)

    serve_parser = subparsers.add_parser("serve", help="Run the local extraction API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)
    serve_parser.set_defaults(handler=lambda args: serve(args.host, args.port) or 0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    return 2
