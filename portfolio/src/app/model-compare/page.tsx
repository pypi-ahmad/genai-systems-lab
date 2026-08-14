"use client";

import { useEffect, useState } from "react";
import { ModelPricingSummary, UsageCostSummary } from "@/components/llm-cost";
import { fetchLLMCatalog, runProject, type LLMCatalogResponse, type ProjectRunResponse } from "@/lib/api";
import type { LLMProviderId } from "@/lib/apikey";
import { findProviderInfo } from "@/lib/llm-catalog";


export default function ModelComparePage() {
  const [catalog, setCatalog] = useState<LLMCatalogResponse | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [provider, setProvider] = useState<LLMProviderId>("gemini");
  const [apiKey, setApiKey] = useState("");
  const [prompt, setPrompt] = useState("Compare retrieval-augmented generation with long-context prompting.");
  const [efforts, setEfforts] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Array<{ model: string; data?: ProjectRunResponse; error?: string }>>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchLLMCatalog()
      .then((value) => {
        if (!cancelled) setCatalog(value);
      })
      .catch((error) => {
        if (!cancelled) setCatalogError(error instanceof Error ? error.message : "Unable to load model catalog.");
      });
    return () => { cancelled = true; };
  }, []);

  const providerInfo = findProviderInfo(catalog, provider);
  const models = providerInfo?.models ?? [];
  const apiKeyRequired = providerInfo?.requires_api_key ?? provider !== "ollama";
  const canCompare = !running
    && Boolean(prompt.trim())
    && models.length > 0
    && providerInfo?.available !== false
    && (!apiKeyRequired || Boolean(apiKey.trim()));

  function changeProvider(nextProvider: LLMProviderId) {
    setProvider(nextProvider);
    setApiKey("");
    setEfforts({});
    setResults([]);
  }

  async function compare() {
    setRunning(true);
    try {
      const compared = await Promise.all(models.map(async (model) => {
        const result = await runProject("multi-agent-research", { input: prompt }, undefined, {
          provider,
          model: model.id,
          apiKey: apiKeyRequired ? apiKey : undefined,
          effort: efforts[model.id] || undefined,
        });
        return result.ok ? { model: model.id, data: result.data } : { model: model.id, error: result.error };
      }));
      setResults(compared);
    } finally {
      setRunning(false);
    }
  }

  return <main className="mx-auto max-w-6xl px-5 py-12">
    <p className="eyebrow">Model comparison</p>
    <h1 className="heading-section mt-3 text-4xl">Run one research prompt against the selected provider&apos;s models.</h1>
    <p className="mt-3 text-[var(--muted)]">Results include latency, tokens, estimated cost, and output. Your key stays in this page&apos;s memory.</p>

    <div className="surface-card mt-8 grid gap-4 rounded-2xl p-6 md:grid-cols-2">
      <label>Provider
        <select className="input-shell mt-2 w-full rounded-lg p-3" value={provider} onChange={(event) => changeProvider(event.target.value as LLMProviderId)}>
          {(catalog?.providers ?? []).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
      </label>
      <label>{providerInfo?.api_key_label ?? "API key"}
        {apiKeyRequired ? (
          <input className="input-shell mt-2 w-full rounded-lg p-3" type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={providerInfo?.api_key_placeholder ?? ""} />
        ) : (
          <div className="surface-panel mt-2 rounded-lg p-3 text-sm text-[var(--muted)]">No API key required.</div>
        )}
      </label>
      <label className="md:col-span-2">Prompt
        <textarea className="input-shell mt-2 min-h-28 w-full rounded-lg p-3" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
      </label>

      <div className="grid gap-4 md:col-span-2 md:grid-cols-2">
        {models.map((model) => <div key={model.id} className="space-y-3">
          <label className="block text-sm font-semibold">{model.label} effort
            <select
              className="input-shell mt-2 w-full rounded-lg p-3 font-normal"
              value={efforts[model.id] ?? ""}
              disabled={model.effort_options.length === 0}
              onChange={(event) => setEfforts((current) => ({ ...current, [model.id]: event.target.value }))}
            >
              <option value="">Provider default</option>
              {model.effort_options.map((effort) => <option key={effort} value={effort}>{effort}</option>)}
            </select>
          </label>
          <ModelPricingSummary model={model} />
        </div>)}
      </div>

      {catalogError ? <p className="md:col-span-2 text-sm text-[var(--danger-text)]">{catalogError}</p> : null}
      {providerInfo?.unavailable_reason ? <p className="md:col-span-2 text-sm text-amber-300">{providerInfo.unavailable_reason}</p> : null}
      <button className="button-primary rounded-full px-5 py-3 disabled:opacity-50" disabled={!canCompare} onClick={() => void compare()}>{running ? "Comparing…" : "Compare models"}</button>
    </div>

    <section className="mt-8 grid gap-6 lg:grid-cols-2" aria-live="polite">
      {results.map(({ model, data, error }) => <article className="surface-card rounded-2xl p-6" key={model}>
        <h2 className="text-xl font-semibold">{model}</h2>
        {error ? <p className="mt-4 text-[var(--danger-text)]">{error}</p> : data && <>
          <p className="mt-3 text-sm text-[var(--muted)]">{Math.round(data.latency)} ms</p>
          {data.usage ? <div className="mt-4"><UsageCostSummary usage={data.usage} /></div> : null}
          <pre className="mt-4 max-h-[32rem] overflow-auto whitespace-pre-wrap text-xs">{data.output}</pre>
        </>}
      </article>)}
    </section>
  </main>;
}
