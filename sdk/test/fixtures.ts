import type { ExtractionResult } from "../src/types.js";

export const validResult: ExtractionResult = {
  schema_version: "1.0",
  document_id: `sha256:${"a".repeat(64)}`,
  document_type: "invoice",
  fields: {
    invoice_number: {
      value: "INV-1",
      confidence: 0.99,
      evidence: [{ block_id: "b1", page: 1, text: "Invoice Number: INV-1" }],
    },
  },
  line_items: [],
  validation: {
    balanced: true,
    calculated_subtotal: "10.00",
    calculated_total: "10.00",
    reported_total: "10.00",
    difference: "0.00",
  },
  processing: {
    normalization_version: "2026-08",
    block_count: 2,
    page_count: 1,
    source_name: "api.txt",
  },
  warnings: [],
};
