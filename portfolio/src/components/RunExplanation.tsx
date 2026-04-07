import { DismissibleTip } from "@/components/dismissible-tip";
import type { RunExplanation } from "@/lib/api";

type RunExplanationPanelProps = {
  explanation: RunExplanation | null;
  isLoading?: boolean;
  error?: string | null;
  title?: string;
  description?: string;
  sourceLabel?: string;
  onClose?: () => void;
};

export function RunExplanationPanel({
  explanation,
  isLoading = false,
  error = null,
  title = "How It Worked",
  description = "Structured explanation generated from the saved run, its memory trace, and its replay timeline.",
  sourceLabel,
  onClose,
}: RunExplanationPanelProps) {
  return (
    <section className="surface-card rounded-[1.75rem] p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            {title}
          </p>
          <p className="mt-1 text-sm leading-7 text-[var(--muted)]">
            {description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {sourceLabel ? (
            <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
              {sourceLabel}
            </span>
          ) : null}
          {onClose ? (
            <button type="button" onClick={onClose} className="button-base button-ghost button-sm button-pill">
              Close
            </button>
          ) : null}
        </div>
      </div>
      <DismissibleTip
        storageKey="tip-run-explanation"
        text="AI-generated summary of what the agent did, key decisions it made, and why."
        className="mt-3"
      />

      {isLoading ? (
        <div className="mt-5 rounded-[1.25rem] border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-4 py-5 text-sm leading-7 text-[var(--foreground)]" aria-live="polite">
          <div className="flex items-center gap-3">
            <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
            Generating a concise explanation from the saved run artifacts.
          </div>
          <p className="mt-2 text-[11px] text-[var(--muted)]">This usually takes 15–30 seconds.</p>
        </div>
      ) : error ? (
        <div className="error-panel mt-5 rounded-[1.25rem] px-4 py-4 text-sm leading-7 text-[var(--danger-text-soft)]">
          {error}
        </div>
      ) : !explanation ? (
        <div className="mt-5 rounded-[1.25rem] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] px-4 py-6 text-sm leading-7 text-[var(--muted)]">
          Select a saved run and generate an explanation to inspect how the system worked.
        </div>
      ) : (
        <div className="mt-5 space-y-5">
          <div className="rounded-[1.25rem] border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Final Outcome
            </p>
            <p className="mt-2 text-sm leading-7 text-[var(--foreground)]">
              {explanation.final_outcome}
            </p>
          </div>

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(280px,0.95fr)]">
            <div className="space-y-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Step Breakdown
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  The main execution moves, reduced to the few steps that mattered most.
                </p>
              </div>
              <div className="space-y-3">
                {explanation.steps_taken.map((entry, index) => (
                  <article key={`${entry.step}-${index}`} className="surface-panel rounded-[1.25rem] px-4 py-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="surface-pill rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                        {index + 1}
                      </span>
                      <p className="text-sm font-semibold text-[var(--foreground)]">{entry.step}</p>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-[var(--foreground)]">
                      {entry.what_happened}
                    </p>
                    <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                      {entry.why_it_mattered}
                    </p>
                  </article>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-[1.25rem] border border-[var(--line)] bg-[var(--card)] px-4 py-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Key Decisions
                </p>
                <div className="mt-3 space-y-3">
                  {explanation.key_decisions.length > 0 ? (
                    explanation.key_decisions.map((entry, index) => (
                      <div key={`${entry.decision}-${index}`} className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-3 py-3">
                        <p className="text-sm font-semibold text-[var(--foreground)]">{entry.decision}</p>
                        <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{entry.reason}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-[var(--muted)]">
                      No major decision points were strongly supported by the saved artifacts.
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-[1.25rem] border border-[var(--line)] bg-[var(--card)] px-4 py-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Final Reasoning
                </p>
                <p className="mt-3 text-sm leading-7 text-[var(--foreground)]">
                  {explanation.final_reasoning}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}