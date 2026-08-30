# Skill evidence

This page maps each portfolio claim to inspectable code, tests, and a command a
reviewer can run. The repository deliberately proves three related skills only.

## Document AI & Extraction

Evidence:

- `src/document_intelligence/adapters.py` validates plain text and provider-neutral OCR blocks, including pages and bounding boxes.
- `src/document_intelligence/normalization.py` repairs common OCR artifacts without losing evidence boundaries.
- `src/document_intelligence/extractor.py` classifies documents, normalizes dates and amounts, extracts fields and line items, and attaches confidence.
- `src/document_intelligence/pipeline.py` adds SHA-256 provenance, required-field warnings, and total reconciliation.
- `samples/northstar-invoice.ocr.json` is a layout-aware synthetic OCR fixture.
- `samples/expected/northstar-invoice.json` is checked-in golden data.
- `tests/test_pipeline.py` verifies normalized values, source evidence, line items, totals, warnings, and provenance.

Verify:

```bash
docintel extract samples/northstar-invoice.ocr.json
docintel benchmark samples/benchmark.json
```

Expected benchmark result: field F1 `1.0`, matching line-item count, and a passed
case. The pipeline also intentionally reports incomplete or inconsistent input
instead of silently treating it as valid.

## Python

Evidence:

- Typed `src/` package with dataclasses, standard-library HTTP service, adapters, CLI, metrics, and dependency injection through provider-neutral models.
- Explicit validation and structured exceptions at input boundaries.
- Unit and integration tests under `tests/`, including an actual ephemeral HTTP server.
- `pyproject.toml` packaging, console entry point, optional extras, Ruff rules, and pytest configuration.
- `.github/workflows/ci.yml` matrix for Python 3.11 and 3.12.

Verify:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest --cov=document_intelligence --cov-report=term-missing -q
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

Start with `tests/test_pipeline.py`, then compare the OCR fixture with the JSON
emitted by the CLI. For TypeScript, start with `sdk/test/client.test.ts`. The
tests demonstrate behavior more directly than a list of claimed technologies.
