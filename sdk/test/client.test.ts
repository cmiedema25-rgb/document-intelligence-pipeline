import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { DocumentApiError, DocumentIntelligenceClient } from "../src/client.js";
import { validResult } from "./fixtures.js";

describe("DocumentIntelligenceClient", () => {
  it("sends text and validates the successful response", async () => {
    let capturedBody = "";
    const mockFetch: typeof fetch = async (_input, init) => {
      capturedBody = String(init?.body ?? "");
      return new Response(JSON.stringify(validResult), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    };
    const client = new DocumentIntelligenceClient("http://service.test/", {
      fetch: mockFetch,
    });
    const result = await client.extractText("Invoice Number: INV-1");
    assert.deepEqual(JSON.parse(capturedBody), { text: "Invoice Number: INV-1" });
    assert.equal(result.fields.invoice_number?.value, "INV-1");
  });

  it("surfaces structured API errors", async () => {
    const mockFetch: typeof fetch = async () =>
      new Response(JSON.stringify({ error: "invalid_document", message: "bad document" }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    const client = new DocumentIntelligenceClient("http://service.test", {
      fetch: mockFetch,
    });
    await assert.rejects(
      () => client.extractText("broken"),
      (error: unknown) =>
        error instanceof DocumentApiError && error.status === 400 && error.message === "bad document",
    );
  });

  it("rejects empty input before making a request", () => {
    const client = new DocumentIntelligenceClient("http://service.test", {
      fetch: async () => {
        throw new Error("should not run");
      },
    });
    assert.throws(() => client.extractText("   "), /cannot be empty/);
  });
});
