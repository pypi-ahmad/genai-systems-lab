"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { projectDetails } from "@/data/projects";
import type { GraphNode } from "@/data/projects";
import { explainRun, logout as logoutSession, runProject, shareRun, unshareRun, streamProject } from "@/lib/api";
import type { HistoryRun, RunExplanation, RunMemoryEntry, StepEvent } from "@/lib/api";
import AnimatedGraph from "@/components/animated-graph";
import AgentGraph from "@/components/agent-graph";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { TimelineReplay, type TimelineReplayFrame } from "@/components/TimelineReplay";
import { RunExplanationPanel } from "@/components/RunExplanation";
import { MemoryPanel, type MemoryEntry } from "@/components/memory-panel";
import type { NodeStatusMap } from "@/components/animated-graph";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { clearAuthSession } from "@/lib/auth";
import { PlaygroundSidebar } from "./playground-sidebar";
import {
  AnyObj,
  assistantCardTone,
  assistantStateTitle,
  buildReplayLogLines,
  buildReplayNodeStatuses,
  categoryBadgeTone,
  categoryColor,
  extractKeyMetrics,
  extractSteps,
  extractTextOutput,
  formatLogTimestamp,
  formatMemoryStepName,
  formatRunTimestamp,
  inferLifecycleStep,
  inferMemoryEntryType,
  isRunMemoryEntry,
  lifecycleLabel,
  lifecycleState,
  mapRunMemoryEntries,
  memoryContentForStep,
  projectApiName,
  realtimeLifecycleState,
  replayRunStatus,
  RunStatus,
  statusLabel,
  statusTone,
  summarizeInputPayload,
  tryParse,
  type WorkspaceState,
  workspaceStateLabel,
  workspaceStateTone,
} from "./playground-utils";
import { usePlaygroundAccount } from "./use-playground-account";

/* ── Spinner ──────────────────────────────────────────── */

function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
    </svg>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 align-middle text-current">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-current"
          style={{ animation: `blink 900ms ${i * 120}ms infinite` }}
        />
      ))}
    </span>
  );
}

const thinkingStates = ["Thinking", "Analyzing", "Planning steps"] as const;

function ThinkingStateList() {
  return (
    <div className="mt-4 space-y-2.5">
      {thinkingStates.map((state, index) => (
        <div
          key={state}
          className="flex items-center gap-2 text-sm leading-7 text-[var(--muted)] transition-opacity duration-300 ease-in-out"
          style={{ animation: `thinkPulse 1800ms ease-in-out ${index * 180}ms infinite` }}
        >
          <span>{state}</span>
          <TypingDots />
        </div>
      ))}
    </div>
  );
}

function DebugPanel({
  logs,
  title = "Debug Panel",
  subtitle = "Live execution log",
  onClear,
}: {
  logs: string[];
  title?: string;
  subtitle?: string;
  onClear?: () => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (copyState === "idle") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyState("idle");
    }, 1600);

    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  const copyLogs = useCallback(async () => {
    if (logs.length === 0) {
      return;
    }

    try {
      await navigator.clipboard.writeText(logs.join("\n"));
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }, [logs]);

  return (
    <section className="overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#0B0F14] shadow-[0_22px_48px_-28px_rgba(2,6,23,0.72)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-4 py-3 sm:px-5">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
            {title}
          </p>
          <p className="mt-1 text-sm font-semibold text-white/82">
            {subtitle}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/45">
            {logs.length} lines
          </span>
          {copyState === "copied" && (
            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300">
              Copied
            </span>
          )}
          {copyState === "error" && (
            <span className="rounded-full border border-rose-400/20 bg-rose-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-rose-300">
              Copy failed
            </span>
          )}
          <button
            type="button"
            onClick={() => void copyLogs()}
            disabled={logs.length === 0}
            className="button-base button-sm button-pill border border-white/10 bg-white/5 text-white/72 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-35"
          >
            Copy
          </button>
          {onClear ? (
            <button
              type="button"
              onClick={onClear}
              disabled={logs.length === 0}
              className="button-base button-sm button-pill border border-white/10 bg-transparent text-white/58 hover:bg-white/8 hover:text-white disabled:cursor-not-allowed disabled:opacity-35"
            >
              Clear logs
            </button>
          ) : null}
        </div>
      </div>

      <div
        ref={scrollRef}
        className="max-h-[360px] overflow-y-auto px-5 py-5 font-mono text-[11px] leading-6 text-[#86EFAC] sm:px-6"
      >
        {logs.length > 0 ? (
          <div className="space-y-0.5">
            {logs.map((line, index) => (
              <div key={`${index}-${line}`} className="whitespace-pre-wrap break-words">
                {line}
              </div>
            ))}
          </div>
        ) : (
          <div className="whitespace-pre-wrap text-white/35">
            Waiting for execution logs.
          </div>
        )}
      </div>
    </section>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="surface-panel rounded-[1.25rem] px-5 py-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-2 text-base font-semibold text-[var(--foreground)]">
        {value}
      </p>
    </div>
  );
}

function WorkspaceStateBadge({ state }: { state: WorkspaceState }) {
  if (state === "thinking") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <Spinner className="h-3 w-3" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "streaming") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <Spinner className="h-3 w-3" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "completed") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--success-dot)]" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "error") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--error-dot)]" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
      {workspaceStateLabel(state)}
    </span>
  );
}

function ReplayStateBadge({
  frame,
  totalEvents,
}: {
  frame: TimelineReplayFrame | null;
  totalEvents: number;
}) {
  const replayFinished = totalEvents > 0 && (frame?.currentIndex ?? -1) >= totalEvents - 1;
  const isPlaying = Boolean(frame?.isPlaying) && !replayFinished;
  const tone = replayFinished
    ? "border-[var(--done-border)] bg-[var(--done-bg)] text-[var(--done-text)]"
    : isPlaying
      ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft-strong)] text-[color-mix(in_srgb,var(--accent-solid)_72%,var(--text)_28%)]"
      : "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]";
  const label = replayFinished ? "Replay complete" : isPlaying ? "Replay playing" : "Replay paused";

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}>
      {label}
    </span>
  );
}

/* ── Main Component ───────────────────────────────────── */

export default function PlaygroundClient() {
  const [selectedSlug, setSelectedSlug] = useState(projectDetails[0].slug);
  const [input, setInput] = useState(projectDetails[0].exampleInput);
  const [rawData, setRawData] = useState<AnyObj | null>(null);
  const [output, setOutput] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [streamMode, setStreamMode] = useState(true);
  const [streamText, setStreamText] = useState("");
  const [streamChunks, setStreamChunks] = useState<number>(0);
  const [stepStatuses, setStepStatuses] = useState<NodeStatusMap>({});
  const [logLines, setLogLines] = useState<string[]>([]);
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>([]);
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
  } = usePlaygroundAccount();
  const [usedSessionContext, setUsedSessionContext] = useState(false);
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
  const memoryEntryIdRef = useRef(0);
  const outputRef = useRef<HTMLDivElement>(null);
  const streamPanelRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const selected = projectDetails.find((p) => p.slug === selectedSlug)!;

  const appendLog = useCallback((message: string) => {
    setLogLines((prev) => [...prev, `[${formatLogTimestamp()}] ${message}`]);
  }, []);

  const resetMemoryEntries = useCallback(() => {
    memoryEntryIdRef.current = 0;
    setMemoryEntries([]);
  }, []);

  const appendMemoryEntry = useCallback((entry: Omit<MemoryEntry, "id" | "timestamp"> & { timestamp?: string }) => {
    memoryEntryIdRef.current += 1;
    setMemoryEntries((prev) => [
      ...prev,
      {
        id: `memory-${memoryEntryIdRef.current}`,
        timestamp: entry.timestamp ?? formatLogTimestamp(),
        ...entry,
      },
    ]);
  }, []);

  const replaceMemoryEntries = useCallback((entries: RunMemoryEntry[]) => {
    memoryEntryIdRef.current = entries.length;
    setMemoryEntries(mapRunMemoryEntries(entries));
  }, []);

  const clearReplay = useCallback(() => {
    setActiveReplayRun(null);
    setReplayFrame(null);
  }, []);

  const clearExplanation = useCallback(() => {
    setActiveExplanationRun(null);
    setExplainingRunId(null);
    setExplanationError(null);
  }, []);

  useEffect(() => {
    if (activeSessionId === null) {
      setUsedSessionContext(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    setStoredApiKey(apiKey.trim());
  }, [apiKey]);

  // Auto-scroll the conversation viewport as live content or final output arrives.
  useEffect(() => {
    if (status !== "idle" && streamPanelRef.current) {
      streamPanelRef.current.scrollTop = streamPanelRef.current.scrollHeight;
    }
  }, [streamText, output, errorMsg, status]);

  // Cleanup the active streaming connection on unmount or project change.
  const disconnect = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
  }, []);

  function handleProjectChange(slug: string) {
    disconnect();
    clearReplay();
    clearExplanation();
    setSelectedSlug(slug);
    const proj = projectDetails.find((p) => p.slug === slug)!;
    setInput(proj.exampleInput);
    setOutput(null);
    setRawData(null);
    setLatency(null);
    setConfidence(null);
    setUsedSessionContext(false);
    setStatus("idle");
    setErrorMsg(null);
    setStreamText("");
    setStepStatuses({});
    setStreamChunks(0);
    setLogLines([]);
    resetMemoryEntries();
  }

  function handleStop() {
    disconnect();
    appendLog("Stream disconnected by user");
    appendMemoryEntry({
      stepName: "Run control",
      type: "observation",
      content: "The run was stopped manually before the stream finished.",
      initiallyExpanded: true,
    });
    setUsedSessionContext(false);
    setConfidence(null);
    setStatus(streamText ? "success" : "idle");
  }

  async function executeRun(runOverride?: { slug?: string; inputText?: string }) {
    disconnect();
    clearReplay();
    clearExplanation();
    const targetSlug = runOverride?.slug ?? selectedSlug;
    const targetProject = projectDetails.find((project) => project.slug === targetSlug) ?? selected;
    const targetInput = runOverride?.inputText ?? input;

    setSelectedSlug(targetProject.slug);
    setInput(targetInput);
    setErrorMsg(null);
    setOutput(null);
    setRawData(null);
    setLatency(null);
    setConfidence(null);
    setUsedSessionContext(false);
    setStreamText("");
    setStepStatuses({});
    setStreamChunks(0);
    setLogLines([]);
    resetMemoryEntries();

    if (!authToken) {
      clearLocalSession();
      setUsedSessionContext(false);
    }

    // Validate JSON input
    let body: Record<string, unknown>;
    try {
      body = JSON.parse(targetInput);
    } catch {
      setStatus("error");
      setErrorMsg("Invalid JSON — check your input syntax.");
      appendMemoryEntry({
        stepName: "Input validation",
        type: "observation",
        content: "The request body is not valid JSON. Fix the syntax and try again.",
        initiallyExpanded: true,
      });
      return;
    }

    if (authToken && activeSessionId !== null) {
      body.session_id = activeSessionId;
    }

    setUsedSessionContext(Boolean(authToken) && activeSessionId !== null && sessionMemoryPreview.length > 0);

    const inputStr = typeof body.input === "string" ? body.input : JSON.stringify(body);
    appendLog(`Request prepared for ${targetProject.name}`);
    appendLog(`Endpoint ${streamMode ? `/stream/${projectApiName(targetProject.apiEndpoint)}` : targetProject.apiEndpoint}`);
    appendMemoryEntry({
      stepName: "Request",
      type: "action",
      content: `Prepared a ${streamMode ? "streaming" : "batch"} run for ${targetProject.name}.`,
      initiallyExpanded: true,
    });

    if (streamMode) {
      // ── Streaming path ───────────────────────────
      setStatus("connecting");
      appendLog("Opening streaming connection");
      let hasLoggedFirstToken = false;

      const abort = streamProject(
        projectApiName(targetProject.apiEndpoint),
        inputStr,
        {
          onOpen: () => {
            appendLog("Streaming connection established");
            appendMemoryEntry({
              stepName: "Stream",
              type: "observation",
              content: "Streaming connection established. Waiting for the first model tokens.",
              initiallyExpanded: false,
            });
            setStatus("streaming");
          },
          onToken: (token) => {
            if (!hasLoggedFirstToken && token.trim()) {
              hasLoggedFirstToken = true;
              appendMemoryEntry({
                stepName: "Output",
                type: "observation",
                content: "The first streamed tokens arrived from the model.",
                initiallyExpanded: false,
              });
            }
            setStreamText((prev) => prev + token);
            setStreamChunks((prev) => prev + 1);
          },
          onStep: (event: StepEvent) => {
            const stepLabel = event.status === "done"
              ? "success"
              : event.status === "error"
                ? `error${event.error ? ` (${event.error})` : ""}`
                : event.status;
            const stepName = formatMemoryStepName(event.step, targetProject.graph.nodes);
            const lifecycle = inferLifecycleStep(event.step, targetProject.graph.nodes);
            appendLog(`${event.step} → ${stepLabel}`);
            appendMemoryEntry({
              stepName,
              type: inferMemoryEntryType(event.step, targetProject.graph.nodes, event.status),
              content: memoryContentForStep(stepName, lifecycle, event.status, event.error),
              initiallyExpanded: event.status === "running",
            });
            setStepStatuses((prev) => {
              const next = { ...prev };

              if (event.status === "running") {
                for (const [stepId, stepStatus] of Object.entries(next)) {
                  if (stepId !== event.step && stepStatus === "running") {
                    next[stepId] = "done";
                  }
                }
              }

              if (event.status === "done") {
                next[event.step] = "done";
              } else if (event.status === "error") {
                next[event.step] = "error";
              } else {
                next[event.step] = "running";
              }
              return next;
            });
          },
          onDone: (meta) => {
            appendLog(`Execution completed in ${Math.round(meta.latency)} ms`);
            appendMemoryEntry({
              stepName: "Completion",
              type: "observation",
              content: `Execution completed in ${Math.round(meta.latency)} ms.`,
              initiallyExpanded: true,
            });
            setLatency(Math.round(meta.latency));
            setConfidence(typeof meta.confidence === "number" ? meta.confidence : null);
            applySessionState(meta.sessionId, meta.sessionMemory);
            setUsedSessionContext(meta.usedSessionContext);
            if (meta.usedSessionContext) {
              appendLog("Using previous context from this session");
            }
            setStatus("success");
            if (authToken) {
              void refreshHistory(authToken);
            }
            // Also populate rawData/output for the tabs
            setStreamText((prev) => {
              const final = prev;
              const parsed = tryParse(final);
              if (parsed) {
                setRawData(parsed);
                setOutput(JSON.stringify(parsed, null, 2));
              } else {
                setRawData({ output: final });
                setOutput(final);
              }
              return final;
            });
          },
          onError: (error) => {
            appendLog(`Execution failed: ${error}`);
            appendMemoryEntry({
              stepName: "Failure",
              type: "observation",
              content: `Execution failed: ${error}`,
              initiallyExpanded: true,
            });
            setUsedSessionContext(false);
            setConfidence(null);
            setStatus("error");
            setErrorMsg(error);
          },
        },
        authToken ?? undefined,
        apiKey || undefined,
        authToken ? activeSessionId : null,
      );
      abortRef.current = abort;
    } else {
      // ── Batch path (original) ────────────────────
      setStatus("running");
      appendLog("Batch execution started");
      appendMemoryEntry({
        stepName: "Batch request",
        type: "action",
        content: "Executing the run and waiting for a complete response payload.",
        initiallyExpanded: true,
      });

      try {
        const result = await runProject(projectApiName(targetProject.apiEndpoint), body, authToken ?? undefined, apiKey || undefined);

        if (result.ok) {
          const data = result.data;
          const responseMemory = Array.isArray(data?.memory)
            ? data.memory.filter(isRunMemoryEntry)
            : [];
          const runSucceeded = data?.success !== false;

          setStatus(runSucceeded ? "success" : "error");
          setLatency(typeof data?.latency === "number" ? Math.round(data.latency) : null);
          setConfidence(typeof data?.confidence === "number" ? data.confidence : null);
          applySessionState(
            typeof data?.session_id === "number" ? data.session_id : null,
            Array.isArray(data?.session_memory)
              ? data.session_memory.filter((entry): entry is string => typeof entry === "string")
              : [],
          );
          setUsedSessionContext(data?.used_session_context === true);
          if (data?.used_session_context === true) {
            appendLog("Using previous context from this session");
          }
          appendLog(
            `${runSucceeded ? "Execution completed" : "Execution finished with an error"}${typeof data?.latency === "number" ? ` in ${Math.round(data.latency)} ms` : ""}`,
          );
          if (responseMemory.length > 0) {
            replaceMemoryEntries(responseMemory);
          } else {
            appendMemoryEntry({
              stepName: runSucceeded ? "Completion" : "Failure",
              type: "observation",
              content: typeof data?.latency === "number"
                ? `${runSucceeded ? "Batch response returned" : "Batch run failed"} in ${Math.round(data.latency)} ms.`
                : runSucceeded
                  ? "Batch response returned successfully."
                  : "Batch run failed.",
              initiallyExpanded: true,
            });
          }
          const innerRaw = typeof data?.output === "string" ? data.output : null;
          const inner = innerRaw ? tryParse(innerRaw) : null;
          if (inner) {
            setRawData(inner);
            setOutput(JSON.stringify(inner, null, 2));
          } else if (innerRaw) {
            setRawData({ output: innerRaw });
            setOutput(innerRaw);
          } else {
            setRawData(data as unknown as AnyObj);
            setOutput(JSON.stringify(data, null, 2));
          }
          if (!runSucceeded) {
            setErrorMsg(typeof data?.output === "string" ? data.output : "Execution failed.");
          }
          if (authToken) {
            void refreshHistory(authToken);
          }
        } else {
          setStatus("error");
          setUsedSessionContext(false);
          setConfidence(null);
          appendLog(`Execution failed: ${result.error}`);
          appendMemoryEntry({
            stepName: "Failure",
            type: "observation",
            content: `Execution failed: ${result.error}`,
            initiallyExpanded: true,
          });
          setErrorMsg(result.error);
        }
      } catch (err) {
        setStatus("error");
        setUsedSessionContext(false);
        setConfidence(null);
        const message = err instanceof Error ? err.message : "Network error — is the API running?";
        appendLog(`Execution failed: ${message}`);
        appendMemoryEntry({
          stepName: "Failure",
          type: "observation",
          content: `Execution failed: ${message}`,
          initiallyExpanded: true,
        });
        setErrorMsg(message);
      }
    }

    setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
  }

  function handleRun() {
    void executeRun();
  }

  function handleHistoryReplay(run: HistoryRun) {
    disconnect();
    clearReplay();
    const replayProject = projectDetails.find((item) => item.slug === run.project);

    if (replayProject) {
      setSelectedSlug(replayProject.slug);
    }

    setInput(run.input);
    setOutput(null);
    setRawData(null);
    setLatency(null);
    setConfidence(run.confidence);
    setUsedSessionContext(false);
    setStatus("idle");
    setErrorMsg(null);
    setStreamText("");
    setStepStatuses({});
    setStreamChunks(0);
    setLogLines([]);

    if (run.memory.length > 0) {
      replaceMemoryEntries(run.memory);
    } else {
      resetMemoryEntries();
    }

    setActiveReplayRun(run);
    setReplayFrame(null);
    setReplayAutoplayKey((value) => value + 1);
    setTimeout(() => outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
  }

  async function handleHistoryExplain(run: HistoryRun) {
    if (!authToken) {
      setExplanationError("Sign in is required to generate saved-run explanations.");
      return;
    }

    if (activeExplanationRun?.id === run.id && Boolean(runExplanations[run.id])) {
      clearExplanation();
      return;
    }

    setActiveExplanationRun(run);
    setExplanationError(null);

    if (runExplanations[run.id]) {
      return;
    }

    setExplainingRunId(run.id);

    try {
      const explanation = await explainRun(run.id, authToken, apiKey || undefined);
      setRunExplanations((previous) => ({
        ...previous,
        [run.id]: explanation,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to explain this saved run.";
      setExplanationError(message);
    } finally {
      setExplainingRunId((value) => (value === run.id ? null : value));
    }
  }

  function handleHistoryRerun(run: HistoryRun) {
    void executeRun({ slug: run.project, inputText: run.input });
  }

  async function handleShare(run: HistoryRun) {
    if (!authToken) return;
    setSharingRunId(run.id);
    try {
      const res = await shareRun(run.id, authToken);
      setHistoryRuns((prev) =>
        prev.map((r) =>
          r.id === run.id
            ? { ...r, share_token: res.share_token, is_public: true, expires_at: res.expires_at }
            : r,
        ),
      );
      const shareUrl = `${window.location.origin}/run/${res.share_token}`;
      await navigator.clipboard.writeText(shareUrl);
      appendLog(`Shared run #${run.id} – link copied to clipboard`);
    } catch {
      appendLog(`Failed to share run #${run.id}`);
    } finally {
      setSharingRunId(null);
    }
  }

  async function handleUnshare(run: HistoryRun) {
    if (!authToken) return;
    setSharingRunId(run.id);
    try {
      await unshareRun(run.id, authToken);
      setHistoryRuns((prev) =>
        prev.map((r) =>
          r.id === run.id
            ? { ...r, share_token: null, is_public: false, expires_at: null }
            : r,
        ),
      );
      appendLog(`Unshared run #${run.id}`);
    } catch {
      appendLog(`Failed to unshare run #${run.id}`);
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
