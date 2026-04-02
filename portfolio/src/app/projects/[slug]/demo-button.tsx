"use client";

import { useEffect, useState } from "react";
import { fetchCurrentUser, fetchLLMCatalog, runProject } from "@/lib/api";
import type { LLMCatalogResponse, LLMRequestOptions } from "@/lib/api";
import { getStoredApiKeys, getStoredLLMSelection, setStoredApiKey, setStoredLLMSelection } from "@/lib/apikey";
import type { LLMProviderId } from "@/lib/apikey";
import { getStoredAuthSession, storeAuthSession } from "@/lib/auth";
import { findProviderForModel, findProviderInfo } from "@/lib/llm-catalog";

export default function DemoButton({
  projectName,
  defaultInput,
}: {
  projectName: string;
  defaultInput: string;
}) {
  const [input, setInput] = useState(defaultInput);
  const [output, setOutput] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(() => getStoredAuthSession());
  const [llmCatalog, setLlMCatalog] = useState<LLMCatalogResponse | null>(null);
  const [llmCatalogError, setLlMCatalogError] = useState<string | null>(null);
  const [apiKeys, setApiKeys] = useState(() => getStoredApiKeys());
  const [selectedModel, setSelectedModel] = useState(() => getStoredLLMSelection()?.model ?? "gemini-3-flash-preview");
  const [selectedProvider, setSelectedProvider] = useState<LLMProviderId>(() => getStoredLLMSelection()?.provider ?? "gemini");

  useEffect(() => {
    if (authToken) {
      return;
    }

    let cancelled = false;
    void fetchCurrentUser()
      .then((user) => {
        if (cancelled || !user) {
          return;
        }
        storeAuthSession();
        setAuthToken(getStoredAuthSession());
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, [authToken]);

  useEffect(() => {
    let cancelled = false;

    void fetchLLMCatalog()
      .then((catalog) => {
        if (cancelled) {
          return;
        }

        const knownModels = new Set(
          catalog.providers.flatMap((provider) => provider.models.map((model) => model.id)),
        );
        const storedSelection = getStoredLLMSelection();
        const preferredModel = storedSelection?.model ?? "gemini-3-flash-preview";
        const nextModel = knownModels.has(preferredModel) ? preferredModel : catalog.default_model;
        const nextProvider = findProviderForModel(catalog, nextModel);

        setLlMCatalog(catalog);
        setLlMCatalogError(null);
        setSelectedModel(nextModel);
        setSelectedProvider(nextProvider);
        setStoredLLMSelection({ provider: nextProvider, model: nextModel });
      })
      .catch((reason) => {
        if (!cancelled) {
          setLlMCatalogError(reason instanceof Error ? reason.message : "Unable to load the model catalog.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const selectedProviderInfo = findProviderInfo(llmCatalog, selectedProvider);
  const selectedApiKey = apiKeys[selectedProvider] ?? "";
  const apiKeyRequired = selectedProviderInfo?.requires_api_key ?? (selectedProvider !== "ollama");
  const providerAvailable = selectedProviderInfo?.available ?? true;
  const providerUnavailableReason = selectedProviderInfo?.unavailable_reason ?? null;
  const apiKeyLabel = selectedProviderInfo?.api_key_label ?? "API key";
  const apiKeyPlaceholder = selectedProviderInfo?.api_key_placeholder ?? "";
  const llm: LLMRequestOptions = {
    provider: selectedProvider,
    model: selectedModel,
    apiKey: apiKeyRequired ? selectedApiKey.trim() || undefined : undefined,
  };

  function handleModelChange(model: string) {
    const provider = findProviderForModel(llmCatalog, model);
    setSelectedModel(model);
    setSelectedProvider(provider);
    setStoredLLMSelection({ provider, model });
  }

  function handleApiKeyChange(value: string) {
    setApiKeys((previous) => ({ ...previous, [selectedProvider]: value }));
    setStoredApiKey(selectedProvider, value.trim());
  }

  async function handleRun() {
    setLoading(true);
    setError(null);
    setOutput(null);

    if (!providerAvailable) {
      setError(providerUnavailableReason ?? "This provider is not currently available.");
      setLoading(false);
      return;
    }

    const normalizedApiKey = selectedApiKey.trim();
    if (apiKeyRequired && !normalizedApiKey) {
      setError(`Enter your ${apiKeyLabel.toLowerCase()} before running this demo.`);
      setLoading(false);
      return;
    }

    let body: Record<string, unknown>;
    try {
      body = JSON.parse(input);
    } catch {
      setError("Invalid JSON input");
      setLoading(false);
      return;
    }

    try {
      const result = await runProject(projectName, body, authToken ?? undefined, llm);
      if (result.ok) {
        setOutput(JSON.stringify(result.data, null, 2));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <label
          htmlFor="demo-input"
          className="block text-sm font-medium text-[var(--muted)]"
        >
          Request body
        </label>
        <textarea
          id="demo-input"
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          spellCheck={false}
          className="input-shell w-full rounded-lg p-3 font-mono text-sm leading-relaxed"
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="demo-model"
          className="block text-sm font-medium text-[var(--muted)]"
        >
          Model
        </label>
        <select
          id="demo-model"
          value={selectedModel}
          onChange={(event) => handleModelChange(event.target.value)}
          className="input-shell w-full rounded-lg p-3 text-sm leading-relaxed"
        >
          {llmCatalog
            ? (llmCatalog.providers.map((provider) => (
                provider.models.length > 0 ? (
                  <optgroup key={provider.id} label={provider.available ? provider.label : `${provider.label} (unavailable)`}>
                    {provider.models.map((model) => (
                      <option key={model.id} value={model.id}>{model.label}</option>
                    ))}
                  </optgroup>
                ) : null
              )))
            : <option value={selectedModel}>{llmCatalogError ? "Model catalog unavailable" : "Loading models..."}</option>}
        </select>
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="demo-api-key"
          className="block text-sm font-medium text-[var(--muted)]"
        >
          {apiKeyLabel}
        </label>
        {apiKeyRequired ? (
          <input
            id="demo-api-key"
            type="password"
            value={selectedApiKey}
            onChange={(event) => handleApiKeyChange(event.target.value)}
            autoComplete="off"
            spellCheck={false}
            placeholder={apiKeyPlaceholder}
            className="input-shell w-full rounded-lg p-3 font-mono text-sm leading-relaxed"
          />
        ) : (
          <div className="surface-panel rounded-lg p-3 text-sm leading-relaxed text-[var(--muted)]">
            No API key required for Ollama.
          </div>
        )}
      </div>

      {(providerUnavailableReason || llmCatalogError) && (
        <div className="space-y-1 text-xs leading-6 text-[var(--muted)]">
          {providerUnavailableReason ? <p className="text-amber-300">{providerUnavailableReason}</p> : null}
          {llmCatalogError ? <p className="text-red-400">{llmCatalogError}</p> : null}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={handleRun}
          disabled={loading || !providerAvailable || (apiKeyRequired && !selectedApiKey.trim())}
          className="button-base button-primary disabled:opacity-50"
        >
          {loading && (
            <svg
              className="h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          )}
          {loading ? "Running…" : "Run Demo"}
        </button>
        <span className="text-xs text-[var(--muted)]">
          POST /{projectName}/run
        </span>
      </div>

      <p className="text-xs leading-6 text-[var(--muted)]">
        {authToken ? "Signed in: successful runs are saved to your history." : "Guest mode: you can run demos without signing in, but history and replay stay unavailable."}
      </p>

      {error && (
        <div className="error-panel rounded-lg p-3">
          <p className="text-sm font-medium text-[var(--danger-text)]">
            Error
          </p>
          <p className="mt-1 text-sm text-[var(--danger-text-soft)]">
            {error}
          </p>
        </div>
      )}

      {output && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-[var(--muted)]">Response</p>
          <pre className="input-shell max-h-96 overflow-auto rounded-lg p-4 text-sm leading-relaxed">
            {output}
          </pre>
        </div>
      )}
    </div>
  );
}
