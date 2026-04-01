"use client";

import Link from "next/link";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { projectDetails } from "@/data/projects";
import type { ProjectDetail } from "@/data/projects";
import type { HistoryRun, RunExplanation } from "@/lib/api";
import { categoryBadgeTone, formatRunTimestamp, maskApiKey } from "./playground-utils";

function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
    </svg>
  );
}

interface PlaygroundSidebarProps {
  activeExplanationRunId: number | null;
  activeReplayRunId: number | null;
  activeSessionId: number | null;
  apiKey: string;
  authToken: string | null;
  clearingSession: boolean;
  errorMsg: string | null;
  explainingRunId: number | null;
  hasSessionContext: boolean;
  historyError: string | null;
  historyLoading: boolean;
  historyRuns: HistoryRun[];
  input: string;
  isActive: boolean;
  keyFocused: boolean;
  onApiKeyChange: (value: string) => void;
  onClearSession: () => void;
  onHistoryExplain: (run: HistoryRun) => void;
  onHistoryReplay: (run: HistoryRun) => void;
  onHistoryRerun: (run: HistoryRun) => void;
  onInputChange: (value: string) => void;
  onKeyFocusedChange: (value: boolean) => void;
  onLogout: () => void;
  onProjectChange: (slug: string) => void;
  onRun: () => void;
  onShare: (run: HistoryRun) => void;
  onStop: () => void;
  onStreamModeChange: (value: boolean) => void;
  onUnshare: (run: HistoryRun) => void;
  runExplanations: Record<number, RunExplanation>;
  selected: ProjectDetail;
  selectedSlug: string;
  sessionEntries: string[];
  sessionLoading: boolean;
  sharingRunId: number | null;
  streamMode: boolean;
}

export function PlaygroundSidebar({
  activeExplanationRunId,
  activeReplayRunId,
  activeSessionId,
  apiKey,
  authToken,
  clearingSession,
  errorMsg,
  explainingRunId,
  hasSessionContext,
  historyError,
  historyLoading,
  historyRuns,
  input,
  isActive,
  keyFocused,
  onApiKeyChange,
  onClearSession,
  onHistoryExplain,
  onHistoryReplay,
  onHistoryRerun,
  onInputChange,
  onKeyFocusedChange,
  onLogout,
  onProjectChange,
  onRun,
  onShare,
  onStop,
  onStreamModeChange,
  onUnshare,
  runExplanations,
  selected,
  selectedSlug,
  sessionEntries,
  sessionLoading,
  sharingRunId,
  streamMode,
}: PlaygroundSidebarProps) {
  const recentRuns = historyRuns.slice(0, 6);

  return (
    <aside className="flex flex-col gap-7 xl:sticky xl:top-24">
      <section className="surface-card rounded-[1.75rem] p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Input</p>
            <p className="mt-1 text-base font-semibold text-[var(--foreground)]">Compose request</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${categoryBadgeTone[selected.category]}`}>
            {selected.category}
          </span>
        </div>

        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          rows={8}
          disabled={isActive}
          className="input-shell mt-4 w-full resize-y rounded-[1.25rem] px-4 py-3.5 font-mono text-[13px] leading-7 disabled:cursor-not-allowed disabled:opacity-60"
          spellCheck={false}
        />

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--muted)]">
            <input
              type="checkbox"
              checked={streamMode}
              onChange={(event) => onStreamModeChange(event.target.checked)}
              disabled={isActive}
              className="accent-[var(--accent-solid)]"
            />
            Stream
          </label>

          {isActive ? (
            <button type="button" onClick={onStop} className="button-base button-secondary button-sm button-pill">
              Stop
            </button>
          ) : (
            <button type="button" onClick={onRun} disabled={!apiKey.trim()} className="button-base button-primary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50">
              Send request
            </button>
          )}
        </div>
      </section>

      <section className="surface-card rounded-[1.75rem] p-5">
        <div className="flex items-center justify-between">
          <label className="block text-xs font-semibold text-[var(--foreground)]">
            Enter your Google API Key
          </label>
          <a
            href="https://aistudio.google.com/apikey"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] font-medium text-[var(--accent)] hover:underline"
          >
            Get API key &rarr;
          </a>
        </div>
        <div className="relative mt-2">
          <input
            type={keyFocused || !apiKey ? "password" : "text"}
            value={keyFocused ? apiKey : maskApiKey(apiKey)}
            onChange={(event) => onApiKeyChange(event.target.value)}
            onFocus={() => onKeyFocusedChange(true)}
            onBlur={() => onKeyFocusedChange(false)}
            placeholder="AIza..."
            disabled={isActive}
            className={`input-shell w-full rounded-[1rem] px-4 py-2.5 font-mono text-xs leading-6 disabled:cursor-not-allowed disabled:opacity-60${errorMsg && /api.key|Missing x-api-key/i.test(errorMsg) ? " ring-2 ring-red-500/60" : ""}`}
            spellCheck={false}
            autoComplete="off"
          />
          {apiKey && !keyFocused && (
            <button
              type="button"
              onClick={() => onApiKeyChange("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] transition-colors hover:text-[var(--foreground)]"
              aria-label="Clear API key"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="size-3.5">
                <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z" />
              </svg>
            </button>
          )}
        </div>
        {errorMsg && /api.key|Missing x-api-key/i.test(errorMsg) ? (
          <p className="mt-1.5 text-[11px] font-medium leading-5 text-red-400">
            Invalid or expired API key
          </p>
        ) : (
          <p className="mt-1.5 text-[11px] leading-5 text-[var(--muted)]">
            Your key is never stored.
          </p>
        )}
      </section>

      <section className="surface-card rounded-[1.75rem] p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Projects</p>
            <p className="mt-1 text-base font-semibold text-[var(--foreground)]">Select a system</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${categoryBadgeTone[selected.category]}`}>
            {selected.category}
          </span>
        </div>

        <div className="mt-4 max-h-[420px] space-y-2.5 overflow-auto pr-1">
          {projectDetails.map((project) => {
            const isSelected = project.slug === selectedSlug;
            return (
              <button
                key={project.slug}
                type="button"
                onClick={() => onProjectChange(project.slug)}
                disabled={isActive}
                className={`w-full rounded-[1.25rem] border px-4 py-4 text-left transition-all duration-200 ease-in-out disabled:cursor-not-allowed disabled:opacity-60 ${
                  isSelected
                    ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft)] shadow-sm"
                    : "border-[var(--line)] bg-[var(--panel)] hover:-translate-y-1 hover:border-[var(--accent-border-soft)] hover:bg-[color-mix(in_srgb,var(--panel)_82%,var(--accent-soft)_18%)]"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold text-[var(--foreground)]">{project.name}</p>
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${categoryBadgeTone[project.category]}`}>
                    {project.category}
                  </span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--muted)]">{project.description}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="surface-card rounded-[1.75rem] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Account</p>
            <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">
              {authToken ? "Authenticated" : "Sign in required"}
            </p>
          </div>
          {authToken ? (
            <button type="button" onClick={onLogout} className="button-base button-secondary button-sm button-pill">Log out</button>
          ) : (
            <Link href="/auth" className="button-base button-primary button-sm button-pill">Login / Sign up</Link>
          )}
        </div>

        {authToken && (
          <>
            <div className="mt-4 border-t border-[var(--line)] pt-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Session</p>
                  <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">
                    {activeSessionId !== null ? "Session active" : "Session idle"}
                  </p>
                  {hasSessionContext && (
                    <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">Last few interactions are ready for reuse.</p>
                  )}
                </div>
                {activeSessionId !== null && (
                  <button
                    type="button"
                    onClick={onClearSession}
                    disabled={sessionLoading || clearingSession}
                    className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {clearingSession ? "Clearing..." : "Clear session"}
                  </button>
                )}
              </div>

              {sessionLoading && (
                <div className="mt-3 flex items-center gap-2 text-sm text-[var(--muted)]">
                  <Spinner className="h-4 w-4" /> Loading session...
                </div>
              )}

              {!sessionLoading && activeSessionId === null && (
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">Start a run to begin a reusable session.</p>
              )}

              {!sessionLoading && activeSessionId !== null && sessionEntries.length === 0 && (
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">This session is active, but no previous interactions are stored yet.</p>
              )}

              {sessionEntries.length > 0 && (
                <div className="mt-3 space-y-2">
                  {sessionEntries.map((entry, index) => (
                    <div key={`${activeSessionId ?? "session"}-${index}`} className="surface-panel rounded-[1rem] p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">Recent interaction</p>
                      <p className="mt-2 line-clamp-3 text-sm leading-6 text-[var(--muted)]">{entry}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 border-t border-[var(--line)] pt-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Saved Runs</p>
                <span className="surface-pill rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  {historyRuns.length} saved
                </span>
              </div>

              {historyLoading && (
                <div className="mt-3 flex items-center gap-2 text-sm text-[var(--muted)]">
                  <Spinner className="h-4 w-4" /> Loading...
                </div>
              )}

              {historyError && (
                <div className="error-panel mt-3 rounded-[1rem] px-4 py-3 text-sm text-[var(--danger-text)]">{historyError}</div>
              )}

              {!historyLoading && !historyError && recentRuns.length === 0 && (
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">No saved runs yet.</p>
              )}

              {recentRuns.length > 0 && (
                <div className="mt-3 space-y-2">
                  {recentRuns.map((run) => {
                    const proj = projectDetails.find((item) => item.slug === run.project);
                    const replaySelected = activeReplayRunId === run.id;
                    const explanationSelected = activeExplanationRunId === run.id;
                    const canReplay = run.timeline.length > 0;
                    const hasExplanation = Boolean(runExplanations[run.id]);
                    const isExplaining = explainingRunId === run.id;
                    return (
                      <div
                        key={run.id}
                        className={`surface-panel rounded-[1rem] p-3 ${replaySelected || explanationSelected ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft)]" : ""}`}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-[var(--foreground)]">{proj?.name ?? run.project}</p>
                            <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{formatRunTimestamp(run.timestamp)}</p>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="surface-pill rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                              {run.timeline.length} events
                            </span>
                            <ConfidenceIndicator confidence={run.confidence} compact />
                            <button
                              type="button"
                              onClick={() => onHistoryReplay(run)}
                              disabled={!canReplay}
                              className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              Replay
                            </button>
                            <button
                              type="button"
                              onClick={() => onHistoryExplain(run)}
                              disabled={explainingRunId !== null && explainingRunId !== run.id}
                              className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {isExplaining
                                ? "Explaining..."
                                : explanationSelected && hasExplanation
                                  ? "Hide Explanation"
                                  : hasExplanation
                                    ? "Show Explanation"
                                    : "Explain How It Worked"}
                            </button>
                            <button type="button" onClick={() => onHistoryRerun(run)} className="button-base button-primary button-sm button-pill">
                              Re-run
                            </button>
                            <button
                              type="button"
                              onClick={() => (run.is_public ? onUnshare(run) : onShare(run))}
                              disabled={sharingRunId !== null}
                              className={`button-base button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50 ${run.is_public ? "button-secondary border-[var(--success-text)] text-[var(--success-text)]" : "button-secondary"}`}
                            >
                              {sharingRunId === run.id
                                ? "Sharing..."
                                : run.is_public
                                  ? "Shared ✓"
                                  : "Share"}
                            </button>
                          </div>
                        </div>
                        <p className="mt-2 line-clamp-2 font-mono text-xs leading-6 text-[var(--muted)]">{run.input}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </aside>
  );
}