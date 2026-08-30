import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { parseExtractionResult, SchemaValidationError } from "../src/validation.js";
import { validResult } from "./fixtures.js";

describe("parseExtractionResult", () => {
  it("returns a valid, typed extraction result", () => {
    const result = parseExtractionResult(validResult);
    assert.equal(result.document_type, "invoice");
    assert.equal(result.fields.invoice_number?.value, "INV-1");
  });

  it("rejects confidence outside the allowed range", () => {
    const invalid = structuredClone(validResult) as unknown as {
      fields: { invoice_number: { confidence: number } };
    };
    invalid.fields.invoice_number.confidence = 1.5;
    assert.throws(
      () => parseExtractionResult(invalid),
      (error: unknown) =>
        error instanceof SchemaValidationError && error.path.endsWith(".confidence"),
    );
  });

  it("rejects document ids without provenance hashes", () => {
    const invalid = { ...validResult, document_id: "random-id" };
    assert.throws(() => parseExtractionResult(invalid), /sha256/);
  });
});
