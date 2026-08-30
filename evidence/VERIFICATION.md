# Verification Record

Date: 2026-08-30 UTC

Environment: CPython 3.12 and Node.js 22 on Linux.

## Commands

~~~bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest --cov=document_intelligence --cov-report=term-missing --cov-fail-under=70 -q
docintel benchmark samples/benchmark.json --report evidence/benchmark-report.json
cd sdk && npm ci && npm test
~~~

## Observed results

| Check | Result |
| --- | ---: |
| Python tests | 24 passed |
| TypeScript tests | 6 passed |
| Total automated tests | 30 passed |
| Python statement coverage | 84.76% (70% floor) |
| Benchmark documents | 3/3 passed |
| Normalized business fields | 23/23 matched |
| Macro precision / recall / F1 | 1.0000 / 1.0000 / 1.0000 |
| Line-item counts | 3/3 matched |

The benchmark contains synthetic invoice and purchase-order fixtures in text
and OCR JSON formats. It does not claim production accuracy across unknown
layouts, scans, languages, or providers.
