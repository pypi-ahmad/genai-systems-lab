"use client";

import { useState, useEffect } from "react";
import { projectDetails } from "@/data/projects";
import { logout as logoutSession } from "@/lib/api";
import { RunExplanationPanel } from "@/components/RunExplanation";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { clearAuthSession } from "@/lib/auth";
import { PlaygroundSidebar } from "./playground-sidebar";
import { PlaygroundConversationPanel } from "./playground-conversation-panel";
import { PlaygroundGraphPanel } from "./playground-graph-panel";
import {
  buildReplayLogLines,
  extractKeyMetrics,
  extractSteps,
  extractTextOutput,
  formatRunTimestamp,
  summarizeInputPayload,
  type WorkspaceState,
} from "./playground-utils";
import { usePlaygroundAccount } from "./use-playground-account";
import { usePlaygroundHistory } from "./use-playground-history";
import { usePlaygroundRun } from "./use-playground-run";
import { DebugPanel, PlaygroundMotionStyles } from "./playground-widgets";

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
    streamPanelRef,
    setSelectedSlug,
    setInput,
    setStatus,
    setConfidence,
    setUsedSessionContext,
    setLogLines,
    disconnect,
    executeRun,
    handleStop,
    hydrateSavedRun,
    resetRunState,
    scrollOutputIntoView,
    appendLog,
    resetMemoryEntries,
  } = run;

  const [streamMode, setStreamMode] = useState(true);
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());
  const [keyFocused, setKeyFocused] = useState(false);

  useEffect(() => {
    setStoredApiKey(apiKey.trim());
  }, [apiKey]);

  const history = usePlaygroundHistory({
    authToken,
    apiKey,
    appendLog,
    disconnect,
    executeRun,
    hydrateSavedRun,
    scrollOutputIntoView,
    setHistoryRuns,
    streamMode,
  });
  const {
    activeExplanationRun,
    activeReplayRun,
    clearExplanation,
    clearReplay,
    explanationError,
    explainingRunId,
    handleHistoryExplain,
    handleHistoryReplay,
    handleHistoryRerun,
    handleShare,
    handleUnshare,
    replayAutoplayKey,
    replayFrame,
    runExplanations,
    setReplayFrame,
    setRunExplanations,
    sharingRunId,
  } = history;

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
  const isActive = status === "connecting" || status === "running" || status === "streaming";
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
    ? buildReplayLogLines(replayFrame?.playedEntries ?? [], graphProject.graph.nodes)
    : logLines;
  const showLogs = conversationStarted || Boolean(activeReplayRun);

  return (
    <>
    <PlaygroundMotionStyles />
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
          <PlaygroundConversationPanel
            confidence={confidence}
            conversationStarted={conversationStarted}
            errorMsg={errorMsg}
            inputPreview={inputPreview}
            keyMetrics={keyMetrics}
            latency={latency}
            output={output}
            selected={selected}
            status={status}
            streamChunks={streamChunks}
            streamMode={streamMode}
            streamPanelRef={streamPanelRef}
            streamText={streamText}
            textOutput={textOutput}
            usedSessionContext={usedSessionContext}
            workspaceState={workspaceState}
          />

          <PlaygroundGraphPanel
            activeReplayRun={activeReplayRun}
            graphProject={graphProject}
            memoryEntries={memoryEntries}
            onReplayClose={() => {
              clearReplay();
              resetMemoryEntries();
              setLogLines([]);
            }}
            onReplayFrameChange={setReplayFrame}
            replayAutoplayKey={replayAutoplayKey}
            replayFrame={replayFrame}
            replaySourceLabel={replaySourceLabel}
            selected={selected}
            status={status}
            stepStatuses={stepStatuses}
            steps={steps}
            streamMode={streamMode}
            workspaceState={workspaceState}
          />

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
