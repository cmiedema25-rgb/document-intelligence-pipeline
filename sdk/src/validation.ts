import type {
  BoundingBox,
  Evidence,
  ExtractedField,
  ExtractionResult,
  JsonScalar,
  LineItem,
  ProcessingSummary,
  ValidationSummary,
} from "./types.js";

export class SchemaValidationError extends Error {
  override readonly name = "SchemaValidationError";

  constructor(message: string, readonly path: string) {
    super(`${path}: ${message}`);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function record(value: unknown, path: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new SchemaValidationError("expected an object", path);
  }
  return value;
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string") {
    throw new SchemaValidationError("expected a string", path);
  }
  return value;
}

function number(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new SchemaValidationError("expected a finite number", path);
  }
  return value;
}

function nullableString(value: unknown, path: string): string | null {
  return value === null ? null : string(value, path);
}

function confidence(value: unknown, path: string): number {
  const parsed = number(value, path);
  if (parsed < 0 || parsed > 1) {
    throw new SchemaValidationError("expected a number between 0 and 1", path);
  }
  return parsed;
}

function boundingBox(value: unknown, path: string): BoundingBox {
  const item = record(value, path);
  return {
    x: number(item.x, `${path}.x`),
    y: number(item.y, `${path}.y`),
    width: number(item.width, `${path}.width`),
    height: number(item.height, `${path}.height`),
  };
}

function evidence(value: unknown, path: string): Evidence {
  const item = record(value, path);
  const result: Evidence = {
    block_id: string(item.block_id, `${path}.block_id`),
    page: number(item.page, `${path}.page`),
    text: string(item.text, `${path}.text`),
  };
  if (item.bbox !== undefined) {
    return { ...result, bbox: boundingBox(item.bbox, `${path}.bbox`) };
  }
  return result;
}

function evidenceArray(value: unknown, path: string): readonly Evidence[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new SchemaValidationError("expected a non-empty evidence array", path);
  }
  return value.map((item, index) => evidence(item, `${path}[${index}]`));
}

function jsonScalar(value: unknown, path: string): JsonScalar {
  if (value === null || ["string", "number", "boolean"].includes(typeof value)) {
    return value as JsonScalar;
  }
  throw new SchemaValidationError("expected a JSON scalar", path);
}

function extractedField(value: unknown, path: string): ExtractedField {
  const item = record(value, path);
  return {
    value: jsonScalar(item.value, `${path}.value`),
    confidence: confidence(item.confidence, `${path}.confidence`),
    evidence: evidenceArray(item.evidence, `${path}.evidence`),
  };
}

function lineItem(value: unknown, path: string): LineItem {
  const item = record(value, path);
  return {
    description: string(item.description, `${path}.description`),
    quantity: number(item.quantity, `${path}.quantity`),
    unit_price: string(item.unit_price, `${path}.unit_price`),
    amount: string(item.amount, `${path}.amount`),
    confidence: confidence(item.confidence, `${path}.confidence`),
    evidence: evidenceArray(item.evidence, `${path}.evidence`),
  };
}

function validation(value: unknown, path: string): ValidationSummary {
  const item = record(value, path);
  if (item.balanced !== null && typeof item.balanced !== "boolean") {
    throw new SchemaValidationError("expected boolean or null", `${path}.balanced`);
  }
  return {
    balanced: item.balanced as boolean | null,
    calculated_subtotal: nullableString(item.calculated_subtotal, `${path}.calculated_subtotal`),
    calculated_total: nullableString(item.calculated_total, `${path}.calculated_total`),
    reported_total: nullableString(item.reported_total, `${path}.reported_total`),
    difference: nullableString(item.difference, `${path}.difference`),
  };
}

function processing(value: unknown, path: string): ProcessingSummary {
  const item = record(value, path);
  return {
    normalization_version: string(item.normalization_version, `${path}.normalization_version`),
    block_count: number(item.block_count, `${path}.block_count`),
    page_count: number(item.page_count, `${path}.page_count`),
    source_name: string(item.source_name, `${path}.source_name`),
  };
}

export function parseExtractionResult(value: unknown): ExtractionResult {
  const root = record(value, "$.");
  if (root.schema_version !== "1.0") {
    throw new SchemaValidationError('expected schema version "1.0"', "$.schema_version");
  }
  const documentId = string(root.document_id, "$.document_id");
  if (!documentId.startsWith("sha256:")) {
    throw new SchemaValidationError('expected a "sha256:" document id', "$.document_id");
  }
  const documentType = string(root.document_type, "$.document_type");
  if (!["invoice", "purchase_order", "unknown"].includes(documentType)) {
    throw new SchemaValidationError("unsupported document type", "$.document_type");
  }

  const rawFields = record(root.fields, "$.fields");
  const fields = Object.fromEntries(
    Object.entries(rawFields).map(([name, item]) => [name, extractedField(item, `$.fields.${name}`)]),
  );
  if (!Array.isArray(root.line_items)) {
    throw new SchemaValidationError("expected an array", "$.line_items");
  }
  if (!Array.isArray(root.warnings) || !root.warnings.every((item) => typeof item === "string")) {
    throw new SchemaValidationError("expected an array of strings", "$.warnings");
  }

  return {
    schema_version: "1.0",
    document_id: documentId as `sha256:${string}`,
    document_type: documentType as ExtractionResult["document_type"],
    fields,
    line_items: root.line_items.map((item, index) => lineItem(item, `$.line_items[${index}]`)),
    validation: validation(root.validation, "$.validation"),
    processing: processing(root.processing, "$.processing"),
    warnings: root.warnings as string[],
  };
}
