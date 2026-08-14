import type { LLMModelOption, RunUsage } from "@/lib/api";


export function formatUsd(value: number, digits = 6): string {
  return `$${value.toFixed(digits)}`;
}


function formatRate(value: number): string {
  return `$${value.toFixed(2)}`;
}


export function ModelPricingSummary({ model }: { model: LLMModelOption | null }) {
  const pricing = model?.pricing;
  if (!pricing) {
    return (
      <div className="surface-panel rounded-[1rem] px-4 py-3 text-[11px] leading-5 text-[var(--muted)]">
        Provider billing is unavailable for this local model.
      </div>
    );
  }

  return (
    <div className="surface-panel rounded-[1rem] px-4 py-3 text-[11px] leading-5 text-[var(--muted)]">
      <p className="font-semibold text-[var(--foreground)]">
        {formatRate(pricing.input_per_million_usd)} input · {formatRate(pricing.output_per_million_usd)} output / 1M tokens
      </p>
      <p className="mt-1">{pricing.details}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.12em]">
        Estimated USD rates · as of {pricing.as_of}
      </p>
    </div>
  );
}


export function UsageCostSummary({ usage, compact = false }: { usage: RunUsage; compact?: boolean }) {
  if (compact) {
    return (
      <span>
        {usage.total_tokens.toLocaleString()} tokens · {usage.estimated_cost_usd === null ? "cost unavailable" : formatUsd(usage.estimated_cost_usd)}
      </span>
    );
  }

  return (
    <div className="surface-panel rounded-[1rem] p-4 text-xs leading-6 text-[var(--muted)]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold text-[var(--foreground)]">Estimated model cost</p>
        <p className="font-semibold text-[var(--foreground)]">
          {usage.estimated_cost_usd === null ? "Unavailable" : formatUsd(usage.estimated_cost_usd)}
        </p>
      </div>
      <p className="mt-1">
        {usage.input_tokens.toLocaleString()} input + {usage.output_tokens.toLocaleString()} output = {usage.total_tokens.toLocaleString()} tokens
      </p>
      {usage.cost_breakdown.map((row, index) => {
        const uncachedInputTokens = row.input_tokens - row.cached_input_tokens;
        return (
          <div key={`${row.model}-${row.pricing_tier}-${index}`} className="mt-3 border-t border-[var(--line)] pt-3">
            <p className="font-medium text-[var(--foreground)]">
              {row.model}{row.pricing_tier === "long_context" ? " · long-context rate" : ""}
            </p>
            <p>
              Input {uncachedInputTokens.toLocaleString()} × ${row.input_rate_per_million_usd}/1M
              {row.cached_input_tokens > 0 && row.cached_input_rate_per_million_usd !== null
                ? ` + ${row.cached_input_tokens.toLocaleString()} cached × $${row.cached_input_rate_per_million_usd}/1M`
                : ""}
              {` = ${formatUsd(row.input_cost_usd)}`}
            </p>
            <p>
              Output {row.output_tokens.toLocaleString()} × ${row.output_rate_per_million_usd}/1M = {formatUsd(row.output_cost_usd)}
            </p>
          </div>
        );
      })}
      <p className="mt-3 text-[10px] uppercase tracking-[0.12em]">
        Estimate excludes taxes and unrelated provider or tool charges.
      </p>
    </div>
  );
}
