export type JsonScalar = string | number | boolean | null;

export interface BoundingBox {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface Evidence {
  readonly block_id: string;
  readonly page: number;
  readonly text: string;
  readonly bbox?: BoundingBox;
}

export interface ExtractedField<T extends JsonScalar = JsonScalar> {
  readonly value: T;
  readonly confidence: number;
  readonly evidence: readonly Evidence[];
}

export interface LineItem {
  readonly description: string;
  readonly quantity: number;
  readonly unit_price: string;
  readonly amount: string;
  readonly confidence: number;
  readonly evidence: readonly Evidence[];
}

export interface ValidationSummary {
  readonly balanced: boolean | null;
  readonly calculated_subtotal: string | null;
  readonly calculated_total: string | null;
  readonly reported_total: string | null;
  readonly difference: string | null;
}

export interface ProcessingSummary {
  readonly normalization_version: string;
  readonly block_count: number;
  readonly page_count: number;
  readonly source_name: string;
}

export interface ExtractionResult {
  readonly schema_version: "1.0";
  readonly document_id: `sha256:${string}`;
  readonly document_type: "invoice" | "purchase_order" | "unknown";
  readonly fields: Readonly<Record<string, ExtractedField>>;
  readonly line_items: readonly LineItem[];
  readonly validation: ValidationSummary;
  readonly processing: ProcessingSummary;
  readonly warnings: readonly string[];
}

export interface OcrBlockInput {
  readonly id?: string;
  readonly page?: number;
  readonly text: string;
  readonly bbox?: readonly [number, number, number, number] | BoundingBox;
}

export type ExtractionRequest =
  | { readonly text: string }
  | { readonly blocks: readonly OcrBlockInput[] };
