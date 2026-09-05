# Document Intelligence Pipeline

[![CI](https://github.com/cmiedema25-rgb/document-intelligence-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/cmiedema25-rgb/document-intelligence-pipeline/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)

Turns invoices, purchase orders, and OCR JSON into validated structured fields — each value carries confidence and source evidence so results are reviewable.

## Install

```bash
git clone https://github.com/cmiedema25-rgb/document-intelligence-pipeline.git
cd document-intelligence-pipeline
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
make verify
```

## Extract

```bash
docintel extract samples/northstar-invoice.ocr.json
docintel serve --port 8080   # local JSON API
```

TypeScript client lives in `sdk/` (`npm ci && npm test`).

## What you get

- Text / OCR JSON / optional PDF adapters
- Invoice & PO classification
- Vendor, numbers, dates, currency, line items with block-level provenance
- Arithmetic validation (line items vs reported totals)
- CLI + local HTTP API + strict TS SDK

## Benchmark

```bash
docintel benchmark samples/benchmark.json --report evidence/benchmark-report.json
```

Uses checked-in synthetic fixtures — swap in your documents for real runs.


## Who this is for

Ops and finance engineers who need extractable invoice/PO fields they can audit — not a black-box document chat. Swap the sample OCR fixtures for your own documents when you are ready for a real run.

## Layout

```text
src/document_intelligence/   # adapters, extract, pipeline, CLI, server
sdk/                         # TypeScript client
samples/ tests/ docs/
```

## License

MIT
