import assert from "node:assert/strict";
import test from "node:test";

import type { LLMCatalogResponse } from "./api";
import { findModelInfo, findProviderForModel, normalizeModelEffort } from "./llm-catalog";


const catalog: LLMCatalogResponse = {
  default_model: "gemini-3.7-flash",
  providers: [
    {
      id: "gemini",
      label: "Google Gemini",
      requires_api_key: true,
      api_key_label: "Google API key",
      api_key_help_url: null,
      api_key_placeholder: "",
      available: true,
      unavailable_reason: null,
      models: [{
        id: "gemini-3.7-flash",
        label: "Gemini Flash 3.7",
        provider: "gemini",
        effort_options: ["low", "medium", "high"],
        pricing: null,
      }],
    },
    {
      id: "xai",
      label: "xAI",
      requires_api_key: true,
      api_key_label: "xAI API key",
      api_key_help_url: null,
      api_key_placeholder: "",
      available: true,
      unavailable_reason: null,
      models: [{
        id: "grok-4.6",
        label: "Grok 4.6",
        provider: "xai",
        effort_options: [],
        pricing: null,
      }],
    },
  ],
};


test("catalog helpers resolve xAI and model-specific efforts", () => {
  assert.equal(findProviderForModel(catalog, "grok-4.6"), "xai");
  const model = findModelInfo(catalog, "gemini-3.7-flash");
  assert.equal(normalizeModelEffort(model, "high"), "high");
  assert.equal(normalizeModelEffort(model, "minimal"), "");
});
