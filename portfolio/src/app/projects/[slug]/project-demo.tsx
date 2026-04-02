"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchCurrentUser, fetchLLMCatalog, getApiUrl, runProject } from "@/lib/api";
import type { LLMCatalogResponse, LLMRequestOptions } from "@/lib/api";
import { getStoredApiKeys, getStoredLLMSelection, setStoredApiKey, setStoredLLMSelection } from "@/lib/apikey";
import type { LLMProviderId } from "@/lib/apikey";
import { getStoredAuthSession, storeAuthSession } from "@/lib/auth";
import { findProviderForModel, findProviderInfo } from "@/lib/llm-catalog";

interface ProjectDemoProps {
  apiEndpoint: string;
  exampleInput: string;
  title?: string;
  description?: string;
  ctaLabel?: string;
}

function projectApiName(apiEndpoint: string) {
  return apiEndpoint.replace(/^\//, "").replace(/\/run$/, "");
}

function formatResult(value: unknown) {
  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export default function ProjectDemo({
  apiEndpoint,
  exampleInput,
  title,
  description,
  ctaLabel,
}: ProjectDemoProps) {
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [result, setResult] = useState<string>("");
  const [input, setInput] = useState(exampleInput);
  const [authToken, setAuthToken] = useState<string | null>(() => getStoredAuthSession());
  const [llmCatalog, setLlMCatalog] = useState<LLMCatalogResponse | null>(null);
  const [llmCatalogError, setLlMCatalogError] = useState<string | null>(null);
  const [apiKeys, setApiKeys] = useState(() => getStoredApiKeys());
  const [selectedModel, setSelectedModel] = useState(() => getStoredLLMSelection()?.model ?? "gemini-3-flash-preview");
  const [selectedProvider, setSelectedProvider] = useState<LLMProviderId>(() => getStoredLLMSelection()?.provider ?? "gemini");
  const projectName = projectApiName(apiEndpoint);

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
      .catch((error) => {
        if (!cancelled) {
          setLlMCatalogError(error instanceof Error ? error.message : "Unable to load the model catalog.");
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
  const apiKeyHelpUrl = selectedProviderInfo?.api_key_help_url ?? null;
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
    setStatus("running");
    setResult("");

    if (!providerAvailable) {
      setStatus("error");
      setResult(providerUnavailableReason ?? "This provider is not currently available.");
      return;
    }

    const normalizedApiKey = selectedApiKey.trim();
    if (apiKeyRequired && !normalizedApiKey) {
      setStatus("error");
      setResult(`Enter your ${apiKeyLabel.toLowerCase()} before running this demo.`);
      return;
    }

    let body: Record<string, unknown>;
    try {
      body = JSON.parse(input);
    } catch {
      setStatus("error");
      setResult("Input is not valid JSON.");
      return;
    }

    try {
      const response = await runProject(projectName, body, authToken ?? undefined, llm);

      if (!response.ok) {
        setStatus("error");
        setResult(response.error);
        return;
      }

      setStatus("success");
      setResult(formatResult(response.data));
    } catch (error) {
      setStatus("error");
      setResult(error instanceof Error ? error.message : "Unable to run demo.");
    }
  }

  return (
    <section className="surface-card rounded-xl p-6 sm:p-8">
      <p className="eyebrow">Run Demo</p>
      <h3 className="mt-3 text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">
        {title ?? "Test the live endpoint"}
      </h3>
      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
        {description ?? "Edit the JSON body and send it to the FastAPI backend for this project."}
      </p>

      <div className="surface-panel mt-4 rounded-[1.25rem] px-4 py-3 font-mono text-xs leading-6 text-[var(--muted)]">
        POST {getApiUrl(`/${projectName}/run`)}
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Model
          </span>
          <select
            value={selectedModel}
            onChange={(event) => handleModelChange(event.target.value)}
            className="input-shell mt-3 w-full rounded-[1rem] px-4 py-3 text-sm leading-6"
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
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            {apiKeyLabel}
          </span>
          {apiKeyRequired ? (
            <input
              type="password"
              value={selectedApiKey}
              onChange={(event) => handleApiKeyChange(event.target.value)}
              autoComplete="off"
              spellCheck={false}
              placeholder={apiKeyPlaceholder}
              className="input-shell mt-3 w-full rounded-[1rem] px-4 py-3 font-mono text-xs leading-6"
            />
          ) : (
            <div className="surface-panel mt-3 rounded-[1rem] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
              No API key required for Ollama.
            </div>
          )}
        </label>
        <div className="surface-panel rounded-[1rem] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
          {authToken ? (
            <span>Signed in. This run can be saved to your history.</span>
          ) : (
            <span>
              Guest mode is available. <Link href="/auth" className="font-semibold text-[var(--foreground)] underline decoration-[var(--accent-border-soft)] underline-offset-2 hover:text-[var(--accent-solid)] hover:decoration-[var(--accent-solid)]">
                Sign in
              </Link>{" "}
              to save history and replay runs.
            </span>
          )}
        </div>
      </div>

      {(apiKeyHelpUrl || providerUnavailableReason || llmCatalogError) && (
        <div className="mt-3 space-y-2 text-[11px] leading-5 text-[var(--muted)]">
          {apiKeyHelpUrl && apiKeyRequired ? (
            <p>
              <a
                href={apiKeyHelpUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-[var(--accent)] hover:underline"
              >
                Get a {apiKeyLabel.toLowerCase()} &rarr;
              </a>
            </p>
          ) : null}
          {providerUnavailableReason ? <p className="text-amber-300">{providerUnavailableReason}</p> : null}
          {llmCatalogError ? <p className="text-red-400">{llmCatalogError}</p> : null}
        </div>
      )}

      <div className="mt-5">
        <label
          htmlFor={`demo-input-${projectName}`}
          className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]"
        >
          Request Body
        </label>
        <textarea
          id={`demo-input-${projectName}`}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          spellCheck={false}
          rows={10}
          className="input-shell mt-3 w-full rounded-[1.25rem] px-4 py-4 font-mono text-[13px] leading-7"
        />
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={status === "running" || !providerAvailable || (apiKeyRequired && !selectedApiKey.trim())}
        className="button-base button-primary button-pill mt-5 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {status === "running" ? "Running..." : (ctaLabel ?? "Run Demo")}
      </button>

      {status === "running" ? (
        <div className="surface-panel mt-5 rounded-[1.25rem] p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Loading
          </p>
          <div className="mt-3 flex items-center gap-3 text-sm leading-7 text-[var(--muted)]">
            <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
            <span>Waiting for the FastAPI response.</span>
          </div>
        </div>
      ) : null}

      {result && status !== "running" ? (
        <div
          className={`mt-5 rounded-[1.25rem] border p-4 ${
            status === "error"
              ? "error-panel"
              : "surface-panel"
          }`}
        >
          <p
            className={`mb-3 text-xs font-semibold uppercase tracking-[0.18em] ${
              status === "error"
                ? "text-[var(--danger-text)]"
                : "text-[var(--muted)]"
            }`}
          >
            {status === "error" ? "Demo Error" : "Demo Output"}
          </p>
          <pre
            className={`overflow-x-auto rounded-[1rem] p-4 font-mono text-[13px] leading-7 ${
              status === "error"
                ? "bg-[var(--danger-surface)] text-[var(--danger-text-soft)]"
                : "input-shell"
            }`}
          >
            {result}
          </pre>
        </div>
      ) : null}
    </section>
  );
}