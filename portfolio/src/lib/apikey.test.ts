import assert from "node:assert/strict";
import test from "node:test";

import {
  clearStoredApiKey,
  clearStoredApiKeys,
  getStoredApiKeys,
  getStoredLLMSelection,
  setStoredApiKey,
  setStoredLLMSelection,
  type LLMProviderId,
} from "./apikey";

function resetAll() {
  clearStoredApiKeys();
}

test("API keys start empty and are not persisted across module reload", () => {
  resetAll();
  const keys = getStoredApiKeys();
  for (const provider of Object.keys(keys) as LLMProviderId[]) {
    assert.equal(keys[provider], "");
  }
});

test("getStoredApiKeys returns a defensive copy so callers cannot mutate the store", () => {
  resetAll();
  setStoredApiKey("openai", "sk-live-secret");

  const snapshot = getStoredApiKeys();
  snapshot.openai = "tampered";

  assert.equal(getStoredApiKeys().openai, "sk-live-secret");
  resetAll();
});

test("clearStoredApiKeys wipes every provider key AND the active selection", () => {
  resetAll();
  setStoredApiKey("openai", "sk-live-secret");
  setStoredApiKey("anthropic", "claude-secret");
  setStoredApiKey("gemini", "gemini-secret");
  setStoredApiKey("ollama", "ollama-secret");
  setStoredLLMSelection({ provider: "openai", model: "gpt-5" });

  clearStoredApiKeys();

  const keys = getStoredApiKeys();
  for (const provider of Object.keys(keys) as LLMProviderId[]) {
    assert.equal(keys[provider], "", `provider ${provider} was not cleared`);
  }
  assert.equal(getStoredLLMSelection(), null);
});

test("clearStoredApiKey only wipes the single provider it is called with", () => {
  resetAll();
  setStoredApiKey("openai", "keep-me");
  setStoredApiKey("anthropic", "wipe-me");

  clearStoredApiKey("anthropic");

  assert.equal(getStoredApiKeys().openai, "keep-me");
  assert.equal(getStoredApiKeys().anthropic, "");
  resetAll();
});

test("clearAuthSession triggers clearStoredApiKeys so logout wipes BYOK keys", async () => {
  resetAll();
  setStoredApiKey("openai", "sk-live-secret");
  setStoredApiKey("anthropic", "claude-secret");
  setStoredLLMSelection({ provider: "openai", model: "gpt-5" });

  // Minimal window shim so ``clearAuthSession`` does not short-circuit on the
  // ``typeof window === "undefined"`` guard.  The ``sessionStorage`` surface
  // only needs ``removeItem`` for this path.
  const storage = new Map<string, string>();
  (globalThis as unknown as { window: unknown }).window = {
    sessionStorage: {
      getItem: (k: string) => storage.get(k) ?? null,
      setItem: (k: string, v: string) => {
        storage.set(k, v);
      },
      removeItem: (k: string) => {
        storage.delete(k);
      },
    },
  };

  try {
    const { clearAuthSession } = await import("./auth");
    clearAuthSession();

    const keys = getStoredApiKeys();
    for (const provider of Object.keys(keys) as LLMProviderId[]) {
      assert.equal(keys[provider], "", `provider ${provider} survived logout`);
    }
    assert.equal(getStoredLLMSelection(), null);
  } finally {
    delete (globalThis as unknown as { window?: unknown }).window;
  }
});

test("API key store must not leak into window, localStorage, or sessionStorage", () => {
  // Keys live in a module-scope closure; there must be no ``window.apiKeys``
  // or similar global exposure.  Checking a few common leak points.
  resetAll();
  setStoredApiKey("openai", "sk-live-secret");

  const w = (globalThis as Record<string, unknown>).window as
    | Record<string, unknown>
    | undefined;
  if (w !== undefined) {
    for (const suspect of ["apiKeys", "activeApiKeys", "llmApiKey"]) {
      assert.equal(w[suspect], undefined, `window.${suspect} must not exist`);
    }
  }
  resetAll();
});
