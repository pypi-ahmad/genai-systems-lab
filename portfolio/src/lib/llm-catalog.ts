import type { LLMCatalogResponse, LLMModelOption, LLMProviderInfo } from "@/lib/api";
import type { LLMProviderId } from "@/lib/apikey";


export function findProviderForModel(catalog: LLMCatalogResponse | null, model: string): LLMProviderId {
  for (const provider of catalog?.providers ?? []) {
    if (provider.models.some((candidate) => candidate.id === model)) {
      return provider.id;
    }
  }

  return "gemini";
}


export function findProviderInfo(
  catalog: LLMCatalogResponse | null,
  providerId: LLMProviderId,
): LLMProviderInfo | null {
  return catalog?.providers.find((provider) => provider.id === providerId) ?? null;
}


export function findModelInfo(
  catalog: LLMCatalogResponse | null,
  modelId: string,
): LLMModelOption | null {
  for (const provider of catalog?.providers ?? []) {
    const model = provider.models.find((candidate) => candidate.id === modelId);
    if (model) return model;
  }
  return null;
}


export function normalizeModelEffort(model: LLMModelOption | null, effort?: string): string {
  return effort && model?.effort_options.includes(effort) ? effort : "";
}
