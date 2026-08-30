import type { ExtractionRequest, ExtractionResult, OcrBlockInput } from "./types.js";
import { parseExtractionResult } from "./validation.js";

export interface ClientOptions {
  readonly fetch?: typeof fetch;
  readonly timeoutMs?: number;
}

export class DocumentApiError extends Error {
  override readonly name = "DocumentApiError";

  constructor(
    message: string,
    readonly status: number,
    readonly responseBody: unknown,
  ) {
    super(message);
  }
}

export class DocumentIntelligenceClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(baseUrl = "http://127.0.0.1:8080", options: ClientOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.fetchImpl = options.fetch ?? fetch;
    this.timeoutMs = options.timeoutMs ?? 10_000;
    if (this.timeoutMs <= 0) {
      throw new RangeError("timeoutMs must be positive");
    }
  }

  extractText(text: string): Promise<ExtractionResult> {
    if (text.trim().length === 0) {
      throw new TypeError("Document text cannot be empty");
    }
    return this.request({ text });
  }

  extractBlocks(blocks: readonly OcrBlockInput[]): Promise<ExtractionResult> {
    if (blocks.length === 0) {
      throw new TypeError("OCR blocks cannot be empty");
    }
    return this.request({ blocks });
  }

  private async request(body: ExtractionRequest): Promise<ExtractionResult> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.fetchImpl(`${this.baseUrl}/v1/extract`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      const responseBody: unknown = await response.json();
      if (!response.ok) {
        const message =
          typeof responseBody === "object" &&
          responseBody !== null &&
          "message" in responseBody &&
          typeof responseBody.message === "string"
            ? responseBody.message
            : `Document API request failed with status ${response.status}`;
        throw new DocumentApiError(message, response.status, responseBody);
      }
      return parseExtractionResult(responseBody);
    } finally {
      clearTimeout(timeout);
    }
  }
}
