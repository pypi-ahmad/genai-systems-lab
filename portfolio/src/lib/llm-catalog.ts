import type { LLMCatalogResponse, LLMProviderInfo } from "@/lib/api";
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
