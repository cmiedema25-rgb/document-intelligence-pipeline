# Extraction method

## 1. Ingestion

Text files are split into stable line blocks. OCR JSON is validated for block
identity, page number, text type, coordinate shape, and duplicate ids. Text-based
PDF extraction is optional; image-only PDFs require OCR first.

## 2. Normalization

Normalization applies Unicode NFKC, converts non-breaking spaces and dash
variants, removes zero-width characters, preserves meaningful line boundaries,
and rejoins lowercase words broken by OCR hyphenation. Normalization has an
explicit version in every result.

## 3. Classification

The classifier scores explicit invoice and purchase-order markers. An unknown
class is retained when the document provides no reliable evidence. Classification
confidence is included as a traceable field rather than hidden.

## 4. Field extraction

Label-aware patterns extract document numbers, dates, currency, and totals.
Dates are normalized to ISO 8601. Currency amounts are parsed with `Decimal` and
serialized as two-decimal strings. The original matching block is returned as
evidence, including page and optional bounding box.

## 5. Line items

The reference format uses pipe-delimited OCR rows. Headers and totals are
excluded. Quantity, unit price, and amount are parsed independently. Confidence
is reduced when `quantity × unit price` does not equal the reported row amount.

## 6. Validation

Extracted line-item amounts are summed and compared with the reported subtotal.
Tax is added and compared with the reported total using a one-cent tolerance.
Differences produce explicit warnings and remain visible in the structured
validation summary.

## 7. Evaluation

Golden fixtures compare normalized field values and line-item counts. Precision,
recall, and F1 are computed transparently. The benchmark fails CI below the
configured F1 threshold.

## Extension points

A production version could add OCR vendor adapters, layout-aware table models,
LLM-assisted fallback extraction, multiple currencies and languages, human
review queues, and dataset-level evaluation. Those extensions should retain the
same evidence-first result contract.
