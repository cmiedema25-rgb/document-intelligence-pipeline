# Skill evidence

This page maps each portfolio claim to inspectable code, retained results, and
a command a reviewer can run. The repository deliberately proves three related
skills only.

## Document AI & Extraction

Evidence:

- `src/document_intelligence/adapters.py` validates plain text and provider-neutral OCR blocks, including pages and bounding boxes.
- `src/document_intelligence/normalization.py` repairs common OCR artifacts without losing evidence boundaries.
- `src/document_intelligence/extractor.py` classifies documents, normalizes dates and amounts, extracts fields and line items, and attaches confidence.
- `src/document_intelligence/pipeline.py` adds SHA-256 provenance, required-field warnings, and total reconciliation.
- `samples/northstar-invoice.ocr.json` is a layout-aware synthetic OCR fixture.
- `samples/expected/` contains checked-in invoice and purchase-order golden data.
- `tests/test_pipeline.py` verifies normalized values, source evidence, line items, totals, warnings, and provenance.
- `tests/test_cli.py` verifies the aggregate reviewer report rather than only a
  console exit code.
- `evidence/benchmark-report.json` retains the exact per-document and aggregate
  result produced by the public CLI.

Verify:

```bash
docintel extract samples/northstar-invoice.ocr.json
docintel benchmark samples/benchmark.json \
  --report evidence/benchmark-report.json
```

Expected aggregate result: 3/3 cases passed, 23/23 normalized fields matched,
macro precision/recall/F1 of `1.0000`, and 3/3 matching line-item counts. The
pipeline also intentionally reports incomplete or inconsistent input instead
of silently treating it as valid.

## Python

Evidence:

- Typed `src/` package with dataclasses, standard-library HTTP service, adapters, CLI, metrics, and dependency injection through provider-neutral models.
- Explicit validation and structured exceptions at input boundaries.
- Unit and integration tests under `tests/`, including an actual ephemeral HTTP server.
- `pyproject.toml` packaging, console entry point, optional extras, Ruff rules, and pytest configuration.
- `.github/workflows/ci.yml` matrix for Python 3.11, 3.12, and 3.13 with a 70%
  statement-coverage floor.
- `.github/workflows/codeql.yml` performs Python and JavaScript/TypeScript
  security analysis.

Verify:

```bash
python -m pip install -e ".[dev]"
make lint
make test
```

## TypeScript

Evidence:

- `sdk/src/types.ts` defines the versioned extraction contract with readonly nested types and a provenance-aware template literal type.
- `sdk/src/validation.ts` performs runtime validation of untrusted JSON, including nested evidence and confidence limits.
- `sdk/src/client.ts` provides a typed fetch client, timeouts, input checks, and structured API errors.
- `sdk/tsconfig.json` enables strict, `noUncheckedIndexedAccess`, and `exactOptionalPropertyTypes`.
- `sdk/test/` tests successful requests, API failures, malformed schemas, and invalid input.
- CI compiles declarations and runs tests on Node 22.

Verify:

```bash
cd sdk
npm ci
npm test
```

## Review guidance

Start with `evidence/benchmark-report.json`, then compare any entry in
`samples/expected/` with the source document and JSON emitted by the CLI. For
Python behavior, read `tests/test_pipeline.py` and `tests/test_cli.py`; for the
strict client, read `sdk/test/client.test.ts`. The retained report plus tests
demonstrate behavior more directly than a list of claimed technologies.

## Measurement boundary

All included organizations and documents are fictional. The three-case
benchmark is a deterministic regression baseline, not an independently sampled
production-accuracy study. It measures exact normalized fields and line-item
counts; it does not measure OCR quality, throughput, human-review time saved, or
financial ROI in a customer deployment.
