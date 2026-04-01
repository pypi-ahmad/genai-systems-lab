"use client";

import { useState, useCallback, useEffect } from "react";
import { projectDetails } from "@/data/projects";
import { explainRun, logout as logoutSession, shareRun, unshareRun } from "@/lib/api";
import type { HistoryRun, RunExplanation } from "@/lib/api";
import AnimatedGraph from "@/components/animated-graph";
import AgentGraph from "@/components/agent-graph";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { TimelineReplay, type TimelineReplayFrame } from "@/components/TimelineReplay";
import { RunExplanationPanel } from "@/components/RunExplanation";
import { MemoryPanel } from "@/components/memory-panel";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { clearAuthSession } from "@/lib/auth";
import { PlaygroundSidebar } from "./playground-sidebar";
import {
  assistantCardTone,
  assistantStateTitle,
  buildReplayLogLines,
  buildReplayNodeStatuses,
  categoryBadgeTone,
  categoryColor,
  extractKeyMetrics,
  extractSteps,
  extractTextOutput,
  formatMemoryStepName,
  formatRunTimestamp,
  lifecycleLabel,
  realtimeLifecycleState,
  replayRunStatus,
  statusLabel,
  statusTone,
  summarizeInputPayload,
  type WorkspaceState,
} from "./playground-utils";
import { usePlaygroundAccount } from "./use-playground-account";
import { usePlaygroundRun } from "./use-playground-run";
import { DebugPanel, StatCard, WorkspaceStateBadge, ReplayStateBadge, ThinkingStateList } from "./playground-widgets";

/* ── Main Component ───────────────────────────────────── */

export default function PlaygroundClient() {
  const account = usePlaygroundAccount();
  const {
    activeSessionId,
    applySessionState,
    authToken,
    clearLocalSession,
    clearSession,
    clearingSession,
    historyError,
    historyLoading,
    historyRuns,
    refreshHistory,
    sessionLoading,
    sessionMemoryPreview,
    setAuthToken,
    setHistoryError,
    setHistoryRuns,
  } = account;

  const run = usePlaygroundRun({
    authToken,
    activeSessionId,
    sessionMemoryPreview,
    applySessionState,
    clearLocalSession,
    refreshHistory,
  });
  const {
    selectedSlug,
    input,
    status,
    output,
    rawData,
    streamText,
    streamChunks,
    stepStatuses,
    errorMsg,
    latency,
    confidence,
    usedSessionContext,
    logLines,
    memoryEntries,
    selected,
    outputRef,
    streamPanelRef,
    setSelectedSlug,
    setInput,
    setStatus,
    setOutput,
    setRawData,
    setLatency,
    setConfidence,
    setUsedSessionContext,
    setErrorMsg,
    setStreamText,
    setStepStatuses,
    setStreamChunks,
    setLogLines,
    disconnect,
    executeRun,
    handleStop,
    resetRunState,
    appendLog,
    resetMemoryEntries,
    replaceMemoryEntries,
  } = run;

  const [streamMode, setStreamMode] = useState(true);
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());
  const [keyFocused, setKeyFocused] = useState(false);
  const [activeReplayRun, setActiveReplayRun] = useState<HistoryRun | null>(null);
  const [replayFrame, setReplayFrame] = useState<TimelineReplayFrame | null>(null);
  const [replayAutoplayKey, setReplayAutoplayKey] = useState(0);
  const [runExplanations, setRunExplanations] = useState<Record<number, RunExplanation>>({});
  const [activeExplanationRun, setActiveExplanationRun] = useState<HistoryRun | null>(null);
  const [explainingRunId, setExplainingRunId] = useState<number | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [sharingRunId, setSharingRunId] = useState<number | null>(null);

  useEffect(() => {
    setStoredApiKey(apiKey.trim());
  }, [apiKey]);

  const clearReplay = useCallback(() => {
    setActiveReplayRun(null);
    setReplayFrame(null);
  }, []);

  const clearExplanation = useCallback(() => {
    setActiveExplanationRun(null);
    setExplainingRunId(null);
    setExplanationError(null);
  }, []);

  function handleProjectChange(slug: string) {
    disconnect();
    clearReplay();
    clearExplanation();
    setSelectedSlug(slug);
    const proj = projectDetails.find((p) => p.slug === slug)!;
    setInput(proj.exampleInput);
    resetRunState();
  }

  function handleRun() {
    clearReplay();
    clearExplanation();
    void executeRun(streamMode, apiKey);
  }

  function handleHistoryReplay(historyRun: HistoryRun) {
    disconnect();
    clearReplay();
    const replayProject = projectDetails.find((item) => item.slug === historyRun.project);

    if (replayProject) {
      setSelectedSlug(replayProject.slug);
    }

    setInput(historyRun.input);
    setOutput(null);
    setRawData(null);
    setLatency(null);
    setConfidence(historyRun.confidence);
    setUsedSessionContext(false);
    setStatus("idle");
    setErrorMsg(null);
    setStreamText("");
    setStepStatuses({});
    setStreamChunks(0);
    setLogLines([]);

    if (historyRun.memory.length > 0) {
      replaceMemoryEntries(historyRun.memory);
    } else {
      resetMemoryEntries();
    }

    setActiveReplayRun(historyRun);
    setReplayFrame(null);
    setReplayAutoplayKey((value) => value + 1);
    setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
  }

  async function handleHistoryExplain(historyRun: HistoryRun) {
    if (!authToken) {
      setExplanationError("Sign in is required to generate saved-run explanations.");
      return;
    }

    if (activeExplanationRun?.id === historyRun.id && Boolean(runExplanations[historyRun.id])) {
      clearExplanation();
      return;
    }

    setActiveExplanationRun(historyRun);
    setExplanationError(null);

    if (runExplanations[historyRun.id]) {
      return;
    }

    setExplainingRunId(historyRun.id);

    try {
      const explanation = await explainRun(historyRun.id, authToken, apiKey || undefined);
      setRunExplanations((previous) => ({
        ...previous,
        [historyRun.id]: explanation,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to explain this saved run.";
      setExplanationError(message);
    } finally {
      setExplainingRunId((value) => (value === historyRun.id ? null : value));
    }
  }

  function handleHistoryRerun(historyRun: HistoryRun) {
    clearReplay();
    clearExplanation();
    void executeRun(streamMode, apiKey, { slug: historyRun.project, inputText: historyRun.input });
  }

  async function handleShare(historyRun: HistoryRun) {
    if (!authToken) return;
    setSharingRunId(historyRun.id);
    try {
      const res = await shareRun(historyRun.id, authToken);
      setHistoryRuns((prev) =>
        prev.map((r) =>
          r.id === historyRun.id
            ? { ...r, share_token: res.share_token, is_public: true, expires_at: res.expires_at }
            : r,
        ),
      );
      const shareUrl = `${window.location.origin}/run/${res.share_token}`;
      await navigator.clipboard.writeText(shareUrl);
      appendLog(`Shared run #${historyRun.id} – link copied to clipboard`);
    } catch {
      appendLog(`Failed to share run #${historyRun.id}`);
    } finally {
      setSharingRunId(null);
    }
  }

  async function handleUnshare(historyRun: HistoryRun) {
    if (!authToken) return;
    setSharingRunId(historyRun.id);
    try {
      await unshareRun(historyRun.id, authToken);
      setHistoryRuns((prev) =>
        prev.map((r) =>
          r.id === historyRun.id
            ? { ...r, share_token: null, is_public: false, expires_at: null }
            : r,
        ),
      );
      appendLog(`Unshared run #${historyRun.id}`);
    } catch {
      appendLog(`Failed to unshare run #${historyRun.id}`);
    } finally {
      setSharingRunId(null);
    }
  }

  async function handleClearSession() {
    const cleared = await clearSession();
    if (cleared) {
      setUsedSessionContext(false);
      appendLog("Session memory cleared");
    } else {
      appendLog("Failed to clear session memory");
    }
  }

  function handleLogout() {
    disconnect();
    clearReplay();
    clearExplanation();
    clearLocalSession();
    setUsedSessionContext(false);
    void logoutSession().catch(() => undefined);
    clearAuthSession();
    setAuthToken(null);
    setHistoryRuns([]);
    setHistoryError(null);
    setRunExplanations({});
    setConfidence(null);
    setStatus("idle");
  }

  // Derived data for tabs
  const steps = rawData ? extractSteps(rawData) : null;
  const keyMetrics = rawData ? extractKeyMetrics(rawData) : [];
  const textOutput = rawData ? extractTextOutput(rawData) : null;
  const sessionEntries = [...sessionMemoryPreview].reverse();
  const hasSessionContext = activeSessionId !== null && sessionMemoryPreview.length > 0;
  const replayProject = activeReplayRun
    ? projectDetails.find((project) => project.slug === activeReplayRun.project) ?? selected
    : null;
  const graphProject = replayProject ?? selected;
  const graphNodes = graphProject.graph.nodes;
  const accent = categoryColor[graphProject.category];
  const showAgentBreakdown = graphProject.category === "LangGraph" || graphProject.category === "CrewAI";
  const isActive = status === "connecting" || status === "running" || status === "streaming";
  const replayStepStatuses = activeReplayRun
    ? buildReplayNodeStatuses(replayFrame?.playedEntries ?? [], graphNodes)
    : null;
  const effectiveStepStatuses = replayStepStatuses ?? stepStatuses;
  const liveNodeItems = graphNodes.map((node) => ({
    ...node,
    status: effectiveStepStatuses[node.id] ?? "idle",
  }));
  const graphStatus = activeReplayRun ? replayRunStatus(replayFrame, activeReplayRun.timeline.length) : status;
  const runLifecycle = realtimeLifecycleState(graphStatus, graphNodes, effectiveStepStatuses);
  const inputPreview = summarizeInputPayload(input);
  const conversationStarted = status !== "idle" || Boolean(output) || Boolean(streamText) || Boolean(errorMsg);
  const showAssistantInProgress = status === "connecting" || status === "running" || status === "streaming";
  const hasLiveStreamOutput = status === "streaming" && streamText.length > 0;
  const workspaceState: WorkspaceState = status === "success"
    ? "completed"
    : status === "error"
      ? "error"
      : hasLiveStreamOutput
        ? "streaming"
        : showAssistantInProgress
          ? "thinking"
          : "idle";
  const replaySourceLabel = activeReplayRun
    ? `${graphProject.name} · ${formatRunTimestamp(activeReplayRun.timestamp)}`
    : undefined;
  const activeExplanation = activeExplanationRun ? runExplanations[activeExplanationRun.id] ?? null : null;
  const activeExplanationProject = activeExplanationRun
    ? projectDetails.find((project) => project.slug === activeExplanationRun.project) ?? null
    : null;
  const explanationSourceLabel = activeExplanationRun
    ? `${activeExplanationProject?.name ?? activeExplanationRun.project} · ${formatRunTimestamp(activeExplanationRun.timestamp)}`
    : undefined;
  const displayedLogs = activeReplayRun
    ? buildReplayLogLines(replayFrame?.playedEntries ?? [], graphNodes)
    : logLines;
  const showLogs = conversationStarted || Boolean(activeReplayRun);

  return (
    <>
    <style>{`@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes thinkPulse {
  0%, 100% { opacity: 0.42; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-1px); }
}`}</style>
    <div className="space-y-8">
      {/* ── Header ── */}
      <section className="title-stack">
        <p className="eyebrow">Playground</p>
        <h1 className="heading-display text-3xl sm:text-4xl">AI Playground</h1>
        <p className="copy-lead max-w-2xl text-base sm:text-lg">
          Compose a request on the left, then watch the response stream into the workspace on the right.
        </p>
      </section>

      {/* ── Two-column grid ── */}
      <div className="grid gap-10 xl:grid-cols-[420px_minmax(0,1fr)] xl:items-start">
        <PlaygroundSidebar
          activeExplanationRunId={activeExplanationRun?.id ?? null}
          activeReplayRunId={activeReplayRun?.id ?? null}
          activeSessionId={activeSessionId}
          apiKey={apiKey}
          authToken={authToken}
          clearingSession={clearingSession}
          errorMsg={errorMsg}
          explainingRunId={explainingRunId}
          hasSessionContext={hasSessionContext}
          historyError={historyError}
          historyLoading={historyLoading}
          historyRuns={historyRuns}
          input={input}
          isActive={isActive}
          keyFocused={keyFocused}
          onApiKeyChange={setApiKey}
          onClearSession={() => void handleClearSession()}
          onHistoryExplain={(run) => void handleHistoryExplain(run)}
          onHistoryReplay={handleHistoryReplay}
          onHistoryRerun={handleHistoryRerun}
          onInputChange={setInput}
          onKeyFocusedChange={setKeyFocused}
          onLogout={handleLogout}
          onProjectChange={handleProjectChange}
          onRun={handleRun}
          onShare={(run) => void handleShare(run)}
          onStop={handleStop}
          onStreamModeChange={setStreamMode}
          onUnshare={(run) => void handleUnshare(run)}
          runExplanations={runExplanations}
          selected={selected}
          selectedSlug={selectedSlug}
          sessionEntries={sessionEntries}
          sessionLoading={sessionLoading}
          sharingRunId={sharingRunId}
          streamMode={streamMode}
        />

        {/* ════════════ RIGHT: Output → Graph → Debug ════════════ */}
        <div className="flex flex-col gap-8">

          {/* ── Conversation / Chat Output ── */}
          <section className="surface-card overflow-hidden rounded-[1.75rem] transition-all duration-300 ease-in-out">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--surface-soft)_78%,transparent)] px-5 py-4">
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Conversation</p>
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${categoryBadgeTone[selected.category]}`}>
                    {selected.category}
                  </span>
                </div>
                <p className="mt-1 text-base font-semibold text-[var(--foreground)]">{selected.name}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <WorkspaceStateBadge state={workspaceState} />
                <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                  {streamMode ? "Streaming on" : "Batch mode"}
                </span>
                {workspaceState === "streaming" && streamChunks > 0 && (
                  <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                    {streamChunks} chunks
                  </span>
                )}
                {latency !== null && (
                  <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                    {latency.toLocaleString()} ms
                  </span>
                )}
                {confidence !== null && <ConfidenceIndicator confidence={confidence} compact />}
              </div>
            </div>

            {usedSessionContext && (
              <div className="border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--surface-soft)_84%,transparent)] px-5 py-2">
                <p className="text-[11px] leading-5 text-[var(--muted)]">Using previous context from this session</p>
              </div>
            )}

            {confidence !== null && (
              <div className="border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--surface-soft)_78%,transparent)] px-5 py-4">
                <ConfidenceIndicator confidence={confidence} />
              </div>
            )}

            <div ref={streamPanelRef} className="max-h-[820px] min-h-[480px] overflow-y-auto bg-[color-mix(in_srgb,var(--surface-soft)_62%,transparent)] transition-all duration-300 ease-in-out">
              <div className="mx-auto flex max-w-3xl flex-col gap-6 p-5 sm:p-8">
                {/* System intro bubble */}
                <div className="flex justify-start">
                  <div className="max-w-2xl rounded-[1.5rem] border border-[var(--line)] bg-[var(--panel-strong)] px-5 py-4 shadow-sm transition-all duration-300 ease-in-out">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">System</p>
                    <p className="mt-2 text-sm leading-7 text-[var(--foreground)]">{selected.description}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                        {streamMode ? "SSE stream" : "Batch request"}
                      </span>
                      <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                        {graphNodes.length} {showAgentBreakdown ? "agents" : "nodes"}
                      </span>
                      {selected.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Idle placeholder */}
                {!conversationStarted && (
                  <div className="rounded-[1.75rem] border border-dashed border-[var(--line)] bg-[var(--panel)]/70 px-6 py-12 text-center transition-all duration-300 ease-in-out">
                    <p className="text-sm font-semibold text-[var(--foreground)]">Output will stream here.</p>
                    <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                      Edit the request body on the left, then press Send request.
                    </p>
                  </div>
                )}

                {/* Active conversation */}
                {conversationStarted && (
                  <>
                    {/* User bubble */}
                    <div className="flex justify-end">
                      <div className="max-w-2xl rounded-[1.5rem] bg-[var(--foreground)] px-5 py-4 text-[var(--bg)] shadow-sm transition-all duration-300 ease-in-out">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color-mix(in_srgb,var(--bg)_64%,transparent)]">You</p>
                        <p className="mt-2 whitespace-pre-wrap text-sm leading-7">{inputPreview}</p>
                        <p className="mt-3 text-[11px] font-medium text-[color-mix(in_srgb,var(--bg)_64%,transparent)]">
                          JSON request prepared for {selected.name}
                        </p>
                      </div>
                    </div>

                    {/* Assistant bubble */}
                    <div className="flex justify-start">
                      <div className={`max-w-2xl rounded-[1.5rem] border px-5 py-4 shadow-sm transition-all duration-300 ease-in-out ${assistantCardTone(workspaceState)}`}>
                        <div className="flex flex-wrap items-center gap-3">
                          <span className={`flex h-8 w-8 items-center justify-center rounded-full ${workspaceState === "error" ? "bg-[var(--danger-text)] text-[var(--accent-contrast)]" : "bg-[var(--foreground)] text-[var(--bg)]"}`}>
                            AI
                          </span>
                          <p className={`text-sm font-semibold ${workspaceState === "error" ? "text-[var(--danger-text)]" : "text-[var(--foreground)]"}`}>
                            {assistantStateTitle(workspaceState)}
                          </p>
                          <WorkspaceStateBadge state={workspaceState} />
                        </div>

                        {/* State: thinking */}
                        {workspaceState === "thinking" && (
                          <div className="transition-opacity duration-300 ease-in-out">
                            <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                              {status === "running"
                                ? "Batch mode is preparing the full assistant reply before rendering it here."
                                : "The stream is open and the model is working through the request before the first tokens arrive."}
                            </p>
                            <ThinkingStateList />
                          </div>
                        )}

                        {/* State: streaming */}
                        {workspaceState === "streaming" && (
                          <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-[var(--foreground)] transition-opacity duration-300 ease-in-out">
                            {streamText}
                            <span className="ml-1 inline-block h-[1.1em] w-[2px] bg-[var(--accent-solid)] align-text-bottom" style={{ animation: "blink 530ms steps(2, start) infinite" }} />
                          </div>
                        )}

                        {/* State: completed */}
                        {workspaceState === "completed" && (
                          <>
                            {textOutput ? (
                              <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-[var(--foreground)] transition-opacity duration-300 ease-in-out">{textOutput}</div>
                            ) : output ? (
                              <pre className="mt-4 max-h-[360px] overflow-auto rounded-[1.25rem] bg-[var(--surface-soft)] p-4 font-mono text-xs leading-6 text-[var(--foreground)] transition-all duration-300 ease-in-out">{output}</pre>
                            ) : (
                              <p className="mt-4 text-sm leading-7 text-[var(--muted)]">The request completed, but no displayable output was returned.</p>
                            )}
                            {keyMetrics.length > 0 && (
                              <div className="mt-4 flex flex-wrap gap-2">
                                {keyMetrics.slice(0, 4).map((metric) => (
                                  <span key={metric.label} className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">
                                    {metric.label}: {metric.value}
                                  </span>
                                ))}
                              </div>
                            )}
                          </>
                        )}

                        {/* State: error */}
                        {workspaceState === "error" && (
                          <>
                            <p className="mt-3 text-sm leading-7 text-[var(--danger-text)]">{errorMsg}</p>
                            {streamText && (
                              <pre className="mt-4 max-h-[240px] overflow-auto rounded-[1.25rem] bg-[var(--danger-surface)] p-4 font-mono text-xs leading-6 text-[var(--danger-text-soft)] transition-all duration-300 ease-in-out">{streamText}</pre>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </section>

          {/* ── Agent Graph ── */}
          <section className="surface-card rounded-[1.75rem] p-5 sm:p-6 transition-all duration-300 ease-in-out">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Agent Graph</p>
                <p className="mt-1 text-base font-semibold text-[var(--foreground)]">
                  {activeReplayRun
                    ? showAgentBreakdown ? "Replay graph" : "Replay flow overview"
                    : showAgentBreakdown ? "Live agent flow" : "Execution flow overview"}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {activeReplayRun ? (
                  <ReplayStateBadge frame={replayFrame} totalEvents={activeReplayRun.timeline.length} />
                ) : (
                  <WorkspaceStateBadge state={workspaceState} />
                )}
                <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                  {lifecycleLabel(runLifecycle.activeStep)}
                </span>
                <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                  {graphNodes.length} {showAgentBreakdown ? "agents" : "nodes"}
                </span>
              </div>
            </div>

            {activeReplayRun && (
              <div className="mt-5">
                <TimelineReplay
                  entries={activeReplayRun.timeline}
                  title="Timeline Replay"
                  description="Replay saved execution events in sequence and drive the graph plus debug log in lockstep."
                  emptyState="This saved run does not include replay events yet. Run it again to capture a replay timeline."
                  sourceLabel={replaySourceLabel}
                  autoplayKey={`${activeReplayRun.id}-${replayAutoplayKey}`}
                  formatStepLabel={(step) => formatMemoryStepName(step, graphNodes)}
                  onFrameChange={setReplayFrame}
                  onClose={() => {
                    clearReplay();
                    resetMemoryEntries();
                    setLogLines([]);
                  }}
                />
              </div>
            )}

            <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(300px,0.95fr)]">
              {/* Left: graphs */}
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Run Lifecycle</p>
                      <p className="mt-1 text-sm text-[var(--muted)]">
                        {activeReplayRun
                          ? "Saved timeline events are driving the lifecycle below."
                          : "Planner → Executor → Evaluator → Final"}
                      </p>
                    </div>
                    <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                      {lifecycleLabel(runLifecycle.activeStep)}
                    </span>
                  </div>
                  <AgentGraph activeStep={runLifecycle.activeStep} completedSteps={runLifecycle.completedSteps} />
                </div>

                <div className="surface-panel rounded-[1.25rem] p-4 transition-all duration-300 ease-in-out">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                    {activeReplayRun
                      ? showAgentBreakdown ? "Replay agent flow" : "Replay execution flow"
                      : showAgentBreakdown ? "Agent flow" : "Execution flow"}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {activeReplayRun
                      ? "Node transitions are synchronized with the replay timeline above."
                      : "Node transitions update live as streamed step events arrive."}
                  </p>
                  <div className="mt-4">
                    <AnimatedGraph
                      nodes={graphNodes}
                      edges={graphProject.graph.edges}
                      accentColor={accent}
                      liveStatuses={Object.keys(effectiveStepStatuses).length > 0 ? effectiveStepStatuses : undefined}
                      speed={Object.keys(effectiveStepStatuses).length > 0 ? undefined : 1000}
                    />
                  </div>
                </div>
              </div>

              {/* Right: stats + step status */}
              <div className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2">
                  <StatCard label="Project" value={selected.name} />
                  <StatCard label="Mode" value={streamMode ? "SSE Stream" : "Batch POST"} />
                  <StatCard label={showAgentBreakdown ? "Agent Nodes" : "Flow Nodes"} value={String(graphNodes.length)} />
                  <StatCard label="Steps" value={steps ? String(steps.length) : workspaceState === "completed" ? "Not returned" : "Live"} />
                </div>

                <div className="space-y-2.5 rounded-[1.25rem] border border-[var(--line)] bg-[var(--card)] p-4 transition-all duration-300 ease-in-out">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                    {activeReplayRun ? "Replay Step Status" : "Step Status"}
                  </p>
                  <div className="grid gap-2">
                    {liveNodeItems.map((node) => (
                      <div
                        key={node.id}
                        className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-xs transition-all duration-300 ease-in-out ${statusTone(node.status)}`}
                      >
                        <div>
                          <p className="font-semibold text-[var(--foreground)]">{node.label}</p>
                          <p className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.14em] opacity-75">{node.id}</p>
                        </div>
                        <span className="rounded-full border border-current/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]">
                          {statusLabel(node.status)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <MemoryPanel
                  entries={memoryEntries}
                  description={activeReplayRun
                    ? "Memory captured for this saved run. Replay controls above animate the execution timeline."
                    : "Ordered trace of what the agent is thinking, doing, and observing during the run."}
                  emptyState={activeReplayRun
                    ? "This saved run does not include persisted memory entries."
                    : "Start a run to populate agent memory with thoughts, actions, and observations."}
                />

                {steps && steps.length > 0 && (
                  <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--card)] p-4 transition-all duration-300 ease-in-out">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Parsed Steps</p>
                    <ol className="mt-3 space-y-2 text-sm leading-7 text-[var(--foreground)]">
                      {steps.slice(0, 5).map((step, index) => (
                        <li key={`${index}-${step}`} className="flex gap-3">
                          <span className="surface-pill mt-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
                            {index + 1}
                          </span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          </section>

          {activeExplanationRun && (
            <RunExplanationPanel
              explanation={activeExplanation}
              isLoading={explainingRunId === activeExplanationRun.id}
              error={explanationError}
              sourceLabel={explanationSourceLabel}
              onClose={clearExplanation}
            />
          )}

          {/* ── Debug Panel ── */}
          {showLogs && (
            <div className="transition-all duration-300 ease-in-out">
              <DebugPanel
                logs={displayedLogs}
                title={activeReplayRun ? "Replay Log" : "Debug Panel"}
                subtitle={activeReplayRun ? "Timeline-synced execution log" : "Live execution log"}
                onClear={activeReplayRun ? undefined : () => setLogLines([])}
              />
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
