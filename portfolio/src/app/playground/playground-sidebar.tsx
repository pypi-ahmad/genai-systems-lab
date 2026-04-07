"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { projectDetails } from "@/data/projects";
import type { ProjectDetail } from "@/data/projects";
import type { HistoryRun, LLMCatalogResponse, LLMProviderInfo, RunExplanation } from "@/lib/api";
import type { LLMProviderId } from "@/lib/apikey";
import { categoryBadgeTone, formatRunTimestamp, maskApiKey } from "./playground-utils";
import { ChevronIcon } from "./playground-icons";

const RECOMMENDED_PROJECT = "genai-research-system";
const GUIDE_DISMISSED_KEY = "playground-guide-dismissed";
const SUPPRESS_CLEAR_CONFIRM_KEY = "suppress-clear-session-confirm";
const SUPPRESS_RERUN_CONFIRM_KEY = "suppress-rerun-confirm";

/* ── Confirm Modal ────────────────────────────────────── */

interface ConfirmRequest {
  storageKey: string;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
}

function ConfirmModal({ request, onClose }: { request: ConfirmRequest; onClose: () => void }) {
  const [dontAskAgain, setDontAskAgain] = useState(false);

  const handleConfirm = () => {
    if (dontAskAgain) {
      localStorage.setItem(request.storageKey, "true");
    }
    request.onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-label={request.title}>
      <div className="w-full max-w-sm rounded-2xl border border-[var(--line)] bg-[var(--card)] p-6 shadow-xl">
        <h2 className="text-base font-semibold text-[var(--foreground)]">{request.title}</h2>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{request.description}</p>

        <label className="mt-4 flex cursor-pointer items-center gap-2 text-xs text-[var(--muted)]">
          <input
            type="checkbox"
            checked={dontAskAgain}
            onChange={(e) => setDontAskAgain(e.target.checked)}
            className="accent-[var(--accent-solid)]"
          />
          Don&apos;t ask again for this action
        </label>

        <div className="mt-5 flex items-center justify-end gap-3">
          <button type="button" onClick={onClose} className="button-base button-secondary button-sm button-pill">
            Cancel
          </button>
          <button type="button" onClick={handleConfirm} className="button-base button-primary button-sm button-pill">
            {request.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function useConfirmModal() {
  const [request, setRequest] = useState<ConfirmRequest | null>(null);

  const requestConfirm = useCallback((req: ConfirmRequest) => {
    if (localStorage.getItem(req.storageKey) === "true") {
      req.onConfirm();
      return;
    }
    setRequest(req);
  }, []);

  const close = useCallback(() => setRequest(null), []);

  return { request, requestConfirm, close };
}

function sortedProjects(projects: ProjectDetail[], search: string): ProjectDetail[] {
  let list = projects;
  if (search.trim()) {
    const q = search.toLowerCase().trim();
    list = list.filter(
      (p) => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q) || p.description.toLowerCase().includes(q),
    );
  } else {
    // When not searching, pin recommended project first
    list = [...list].sort((a, b) => {
      if (a.slug === RECOMMENDED_PROJECT) return -1;
      if (b.slug === RECOMMENDED_PROJECT) return 1;
      return 0;
    });
  }
  return list;
}

function PlaygroundGuide() {
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem(GUIDE_DISMISSED_KEY) === "true";
  });
  if (dismissed) {
    return (
      <button
        type="button"
        onClick={() => { localStorage.removeItem(GUIDE_DISMISSED_KEY); setDismissed(false); }}
        className="mt-2 text-[11px] text-[var(--muted)] underline decoration-[var(--line)] underline-offset-2 transition-colors hover:text-[var(--foreground)]"
      >
        Show quick-start guide
      </button>
    );
  }
  return (
    <div className="mt-4 rounded-2xl border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-4 py-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-[var(--foreground)]">Quick start</p>
        <button
          type="button"
          onClick={() => { localStorage.setItem(GUIDE_DISMISSED_KEY, "true"); setDismissed(true); }}
          className="shrink-0 text-[var(--muted)] hover:text-[var(--foreground)]"
          aria-label="Dismiss guide"
        >
          ✕
        </button>
      </div>
      <ol className="mt-2 space-y-1 text-sm leading-6 text-[var(--muted)]">
        <li><span className="font-semibold text-[var(--foreground)]">①</span> Pick a project</li>
        <li><span className="font-semibold text-[var(--foreground)]">②</span> Enter your API key</li>
        <li><span className="font-semibold text-[var(--foreground)]">③</span> Press Run</li>
      </ol>
    </div>
  );
}

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
  authToken: string | null;
  clearingSession: boolean;
  canRun: boolean;
  errorMsg: string | null;
  explainingRunId: number | null;
  hasSessionContext: boolean;
  historyError: string | null;
  historyLoading: boolean;
  historyRuns: HistoryRun[];
  input: string;
  inputMode: "json" | "text";
  textModeAvailable: boolean;
  onInputModeChange: (mode: "json" | "text") => void;
  isActive: boolean;
  keyFocused: boolean;
  llmCatalog: LLMCatalogResponse | null;
  llmCatalogError: string | null;
  llmCatalogLoading: boolean;
  onApiKeyChange: (value: string) => void;
  onClearSession: () => void;
  onHistoryExplain: (run: HistoryRun) => void;
  onHistoryReplay: (run: HistoryRun) => void;
  onHistoryRerun: (run: HistoryRun) => void;
  onInputChange: (value: string) => void;
  onKeyFocusedChange: (value: boolean) => void;
  onLogout: () => void;
  onModelChange: (value: string) => void;
  onProjectChange: (slug: string) => void;
  onRun: () => void;
  onShare: (run: HistoryRun) => void;
  onStop: () => void;
  onStreamModeChange: (value: boolean) => void;
  onUnshare: (run: HistoryRun) => void;
  providerAvailable: boolean;
  providerUnavailableReason: string | null;
  runExplanations: Record<number, RunExplanation>;
  selected: ProjectDetail;
  selectedApiKey: string;
  selectedModel: string;
  selectedProvider: LLMProviderId;
  selectedProviderInfo: LLMProviderInfo | null;
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
  authToken,
  clearingSession,
  canRun,
  errorMsg,
  explainingRunId,
  hasSessionContext,
  historyError,
  historyLoading,
  historyRuns,
  input,
  inputMode,
  textModeAvailable,
  onInputModeChange,
  isActive,
  keyFocused,
  llmCatalog,
  llmCatalogError,
  llmCatalogLoading,
  onApiKeyChange,
  onClearSession,
  onHistoryExplain,
  onHistoryReplay,
  onHistoryRerun,
  onInputChange,
  onKeyFocusedChange,
  onLogout,
  onModelChange,
  onProjectChange,
  onRun,
  onShare,
  onStop,
  onStreamModeChange,
  onUnshare,
  providerAvailable,
  providerUnavailableReason,
  runExplanations,
  selected,
  selectedApiKey,
  selectedModel,
  selectedProvider,
  selectedProviderInfo,
  selectedSlug,
  sessionEntries,
  sessionLoading,
  sharingRunId,
  streamMode,
}: PlaygroundSidebarProps) {
  const [keyTouched, setKeyTouched] = useState(false);
  const [projectSearch, setProjectSearch] = useState("");
  const [modelOpen, setModelOpen] = useState(true);
  const [accountOpen, setAccountOpen] = useState(() => Boolean(authToken));
  const { request: confirmRequest, requestConfirm, close: closeConfirm } = useConfirmModal();
  const recentRuns = historyRuns.slice(0, 6);
  const keyError = keyTouched && Boolean(errorMsg && /api.key|api key|x-api-key|missing x-api-key/i.test(errorMsg));
  const providerLabel = selectedProviderInfo?.label ?? selectedProvider;
  const apiKeyRequired = selectedProviderInfo?.requires_api_key ?? (selectedProvider !== "ollama");
  const apiKeyLabel = selectedProviderInfo?.api_key_label ?? "API key";
  const apiKeyPlaceholder = selectedProviderInfo?.api_key_placeholder ?? "";
  const apiKeyHelpUrl = selectedProviderInfo?.api_key_help_url ?? null;

  const jsonWarning = useMemo(() => {
    if (inputMode === "text") return null;
    const trimmed = input.trim();
    if (!trimmed) return null;
    try { JSON.parse(trimmed); return null; } catch {
      return "This doesn\u2019t look like valid JSON. Check for missing brackets or quotes.";
    }
  }, [input, inputMode]);

  return (
    <>
    <aside className="flex flex-col gap-7 xl:sticky xl:top-24">
      <section className="surface-card rounded-[1.75rem] p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Input</p>
            <p className="mt-1 text-base font-semibold text-[var(--foreground)]">Your input</p>
          </div>
          <div className="flex items-center gap-2">
            {textModeAvailable && (
              <div className="surface-pill flex items-center gap-0.5 rounded-full p-0.5">
                <button
                  type="button"
                  onClick={() => onInputModeChange("text")}
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${inputMode === "text" ? "bg-[var(--accent-solid)] text-white" : "text-[var(--muted)] hover:text-[var(--foreground)]"}`}
                >
                  Text
                </button>
                <button
                  type="button"
                  onClick={() => onInputModeChange("json")}
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${inputMode === "json" ? "bg-[var(--accent-solid)] text-white" : "text-[var(--muted)] hover:text-[var(--foreground)]"}`}
                >
                  JSON
                </button>
              </div>
            )}
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${categoryBadgeTone[selected.category]}`}>
              {selected.category}
            </span>
          </div>
        </div>

        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          rows={inputMode === "text" ? 4 : 8}
          disabled={isActive}
          placeholder={inputMode === "text" ? "Type your prompt here\u2026" : undefined}
          className={`input-shell mt-4 w-full resize-y rounded-[1.25rem] px-4 py-3.5 text-[13px] leading-7 disabled:cursor-not-allowed disabled:opacity-60 ${inputMode === "json" ? "font-mono" : ""}`}
          spellCheck={inputMode === "text"}
        />
        {jsonWarning && (
          <p className="mt-1.5 text-xs text-[var(--warning-text,#d97706)]" role="status">
            ⚠ {jsonWarning}
          </p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--muted)]">
            <input
              type="checkbox"
              checked={streamMode}
              onChange={(event) => onStreamModeChange(event.target.checked)}
              disabled={isActive}
              className="accent-[var(--accent-solid)]"
            />
            <span className="flex flex-col leading-tight">
              <span>Live streaming</span>
              <span className="text-[10px] opacity-70">See output as it generates</span>
            </span>
          </label>

          {isActive ? (
            <button type="button" onClick={onStop} className="button-base button-secondary button-sm button-pill">
              Stop
            </button>
          ) : (
            <button type="button" onClick={() => { setKeyTouched(true); onRun(); }} disabled={!canRun} className="button-base button-primary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50">
              Run
            </button>
          )}
        </div>
      </section>

      <section className="surface-card rounded-[1.75rem] p-5">
        <button
          type="button"
          onClick={() => setModelOpen((prev) => !prev)}
          className="flex w-full items-start justify-between gap-3 text-left"
        >
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Model</p>
            <p className="mt-1 text-base font-semibold text-[var(--foreground)]">AI model</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="surface-pill rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
              {providerLabel}
            </span>
            <ChevronIcon open={modelOpen} />
          </div>
        </button>

        {modelOpen && (
        <div className="mt-4 space-y-4">
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Available models
            </span>
            <select
              value={selectedModel}
              onChange={(event) => onModelChange(event.target.value)}
              disabled={isActive || llmCatalogLoading || !llmCatalog}
              className="input-shell mt-3 w-full rounded-[1rem] px-4 py-3 text-sm leading-6 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {llmCatalog
                ? (llmCatalog.providers.map((provider) => (
                    provider.models.length > 0 ? (
                      <optgroup
                        key={provider.id}
                        label={provider.available ? provider.label : `${provider.label} (unavailable)`}
                      >
                        {provider.models.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.label}
                          </option>
                        ))}
                      </optgroup>
                    ) : null
                  )))
                : <option value={selectedModel}>{llmCatalogError ? "Model catalog unavailable" : "Loading models..."}</option>}
            </select>
          </label>

          {llmCatalogError ? (
            <p className="text-[11px] leading-5 text-red-400">{llmCatalogError}</p>
          ) : null}

          {!providerAvailable && providerUnavailableReason ? (
            <p className="rounded-[1rem] border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-[11px] leading-5 text-amber-200">
              {providerUnavailableReason}
            </p>
          ) : null}

          {apiKeyRequired ? (
            <div>
              <div className="flex items-center justify-between gap-3">
                <label className="block text-xs font-semibold text-[var(--foreground)]">
                  {apiKeyLabel}
                </label>
                {apiKeyHelpUrl ? (
                  <a
                    href={apiKeyHelpUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-medium text-[var(--accent)] hover:underline"
                  >
                    Get a free key &rarr;
                  </a>
                ) : null}
              </div>
              <p className="mt-1.5 text-[11px] leading-5 text-[var(--muted)]">
                Each provider requires its own key. Most offer a free tier — click the link above to create one in seconds.
                Your key stays in this browser tab only and is never stored or sent to our servers.
              </p>

              <div className="relative mt-2">
                <input
                  type={keyFocused || !selectedApiKey ? "password" : "text"}
                  value={keyFocused ? selectedApiKey : maskApiKey(selectedApiKey)}
                  onChange={(event) => onApiKeyChange(event.target.value)}
                  onFocus={() => onKeyFocusedChange(true)}
                  onBlur={() => { onKeyFocusedChange(false); setKeyTouched(true); }}
                  placeholder={apiKeyPlaceholder || "Paste your API key to get started"}
                  disabled={isActive}
                  className={`input-shell w-full rounded-[1rem] px-4 py-2.5 font-mono text-xs leading-6 disabled:cursor-not-allowed disabled:opacity-60${keyError ? " ring-2 ring-red-500/60" : ""}`}
                  spellCheck={false}
                  autoComplete="off"
                />
                {selectedApiKey && !keyFocused && (
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

              {keyError ? (
                <p className="mt-1.5 text-[11px] font-medium leading-5 text-red-400">
                  API key not accepted. Make sure you copied the full key and that it matches the selected provider.
                </p>
              ) : null}
            </div>
          ) : (
            <div className="rounded-[1rem] border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-4 py-3 text-[11px] leading-5 text-[var(--muted)]">
              Ollama runs do not need an API key. The backend will use the models visible from its configured Ollama host.
            </div>
          )}
        </div>
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

        {/* B03: 3-step inline guide */}
        <PlaygroundGuide />

        {/* B12: Project search */}
        <input
          type="text"
          value={projectSearch}
          onChange={(event) => setProjectSearch(event.target.value)}
          placeholder="Search projects…"
          className="input-shell mt-4 w-full rounded-[1rem] px-4 py-2.5 text-sm leading-6"
          spellCheck={false}
        />

        <div className="mt-3 max-h-[420px] space-y-2.5 overflow-auto pr-1">
          {sortedProjects(projectDetails, projectSearch).map((project) => {
            const isSelected = project.slug === selectedSlug;
            const isRecommended = project.slug === RECOMMENDED_PROJECT;
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
                  <div className="flex flex-wrap items-center gap-1.5">
                    {isRecommended && !projectSearch && (
                      <span className="rounded-full border border-[var(--done-border)] bg-[var(--done-bg)] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[var(--done-text)]">
                        Recommended
                      </span>
                    )}
                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${categoryBadgeTone[project.category]}`}>
                      {project.category}
                    </span>
                  </div>
                </div>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--muted)]">{project.description}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="surface-card rounded-[1.75rem] p-5">
        <button
          type="button"
          onClick={() => setAccountOpen((prev) => !prev)}
          className="flex w-full flex-wrap items-center justify-between gap-3 text-left"
        >
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Account</p>
            <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">
              {authToken ? "Authenticated" : "Sign in required"}
            </p>
          </div>
          <ChevronIcon open={accountOpen} />
        </button>

        {accountOpen && (
          <>
            <div className="mt-4 flex flex-wrap items-center justify-end gap-3">
              {authToken ? (
                <button type="button" onClick={onLogout} className="button-base button-secondary button-sm button-pill">Log out</button>
              ) : (
                <Link href="/auth" className="button-base button-primary button-sm button-pill">Log in / Sign up</Link>
              )}
            </div>

            {authToken && (
            <>
            <div className="mt-4 border-t border-[var(--line)] pt-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Session</p>
                  <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">
                    {activeSessionId !== null ? "Conversation active" : "No active conversation"}
                  </p>
                  {hasSessionContext && (
                    <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">Previous messages in this conversation will be included.</p>
                  )}
                </div>
                {activeSessionId !== null && (
                  <button
                    type="button"
                    onClick={() => requestConfirm({ storageKey: SUPPRESS_CLEAR_CONFIRM_KEY, title: "Start new conversation?", description: "Current context will be cleared. You can still find past runs in your history.", confirmLabel: "Clear & start new", onConfirm: onClearSession })}
                    disabled={sessionLoading || clearingSession}
                    className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {clearingSession ? "Clearing..." : "Start new conversation"}
                  </button>
                )}
              </div>

              {sessionLoading && (
                <div className="mt-3 flex items-center gap-2 text-sm text-[var(--muted)]">
                  <Spinner className="h-4 w-4" /> Loading session...
                </div>
              )}

              {!sessionLoading && activeSessionId === null && (
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">Start a run to begin a conversation. Context carries across runs.</p>
              )}

              {!sessionLoading && activeSessionId !== null && sessionEntries.length === 0 && (
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">Conversation is active, but no previous messages are stored yet.</p>
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
                            <button type="button" onClick={() => requestConfirm({ storageKey: SUPPRESS_RERUN_CONFIRM_KEY, title: "Re-run this request?", description: "This will replace your current output with a fresh run.", confirmLabel: "Re-run", onConfirm: () => onHistoryRerun(run) })} className="button-base button-primary button-sm button-pill">
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
          </>
        )}
      </section>
    </aside>

    {confirmRequest && <ConfirmModal request={confirmRequest} onClose={closeConfirm} />}
    </>
  );
}