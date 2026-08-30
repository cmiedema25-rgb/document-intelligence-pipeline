export { DocumentApiError, DocumentIntelligenceClient } from "./client.js";
export type { ClientOptions } from "./client.js";
export type {
  BoundingBox,
  Evidence,
  ExtractedField,
  ExtractionRequest,
  ExtractionResult,
  JsonScalar,
  LineItem,
  OcrBlockInput,
  ProcessingSummary,
  ValidationSummary,
} from "./types.js";
export { parseExtractionResult, SchemaValidationError } from "./validation.js";
