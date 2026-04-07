"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { projectDetails } from "@/data/projects";
import type { ProjectDetail } from "@/data/projects";
import { runProject, streamProject } from "@/lib/api";
import type { HistoryRun, LLMRequestOptions, RunMemoryEntry, StepEvent } from "@/lib/api";
import type { NodeStatusMap } from "@/components/animated-graph";
import type { MemoryEntry } from "@/components/memory-panel";
import {
  type AnyObj,
  type RunStatus,
  formatLogTimestamp,
  formatMemoryStepName,
  inferLifecycleStep,
  inferMemoryEntryType,
  isRunMemoryEntry,
  mapRunMemoryEntries,
  memoryContentForStep,
  projectApiName,
  tryParse,
} from "./playground-utils";

/* ── Types ────────────────────────────────────────────── */

export type InputMode = "json" | "text";

export interface PlaygroundRunDeps {
  authToken: string | null;
  activeSessionId: number | null;
  sessionMemoryPreview: string[];
  applySessionState: (sessionId: number | null, memory: string[]) => void;
  clearLocalSession: () => void;
  refreshHistory: (token: string) => Promise<void>;
}

export interface ExecuteRunOverrides {
  slug?: string;
  inputText?: string;
}

/* ── Hook ─────────────────────────────────────────────── */

/** A project is eligible for plain-text mode when its exampleInput is `{"input": "..."}` with no extra keys. */
function isTextModeEligible(project: ProjectDetail): boolean {
  try {
    const parsed = JSON.parse(project.exampleInput);
    const keys = Object.keys(parsed);
    return keys.length === 1 && keys[0] === "input" && typeof parsed.input === "string";
  } catch { return false; }
}

export function usePlaygroundRun(deps: PlaygroundRunDeps) {
  const {
    authToken,
    activeSessionId,
    sessionMemoryPreview,
    applySessionState,
    clearLocalSession,
    refreshHistory,
  } = deps;

  /* ── Core run state ── */
  const [selectedSlug, setSelectedSlug] = useState(projectDetails[0].slug);
  const [input, setInput] = useState(() => {
    if (isTextModeEligible(projectDetails[0])) {
      try { return JSON.parse(projectDetails[0].exampleInput).input as string; } catch { /* fall through */ }
    }
    return projectDetails[0].exampleInput;
  });
  const [inputMode, setInputMode] = useState<InputMode>(
    isTextModeEligible(projectDetails[0]) ? "text" : "json",
  );
  const [rawData, setRawData] = useState<AnyObj | null>(null);
  const [output, setOutput] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [streamText, setStreamText] = useState("");
  const [streamChunks, setStreamChunks] = useState<number>(0);
  const [stepStatuses, setStepStatuses] = useState<NodeStatusMap>({});
  const [usedSessionContext, setUsedSessionContext] = useState(false);

  /* ── Memory / log state ── */
  const [logLines, setLogLines] = useState<string[]>([]);
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>([]);
  const memoryEntryIdRef = useRef(0);

  /* ── Refs ── */
  const outputRef = useRef<HTMLDivElement>(null);
  const streamPanelRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  /* ── Derived ── */
  const selected = projectDetails.find((p) => p.slug === selectedSlug)!;
  const textModeAvailable = isTextModeEligible(selected);

  /* ── Memory helpers ── */

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

  /* ── Effects ── */

  // Auto-scroll the conversation viewport as live content or final output arrives.
  useEffect(() => {
    if (status !== "idle" && streamPanelRef.current) {
      streamPanelRef.current.scrollTop = streamPanelRef.current.scrollHeight;
    }
  }, [streamText, output, errorMsg, status]);

  /* ── Connection management ── */

  const disconnect = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
  }, []);

  const scrollOutputIntoView = useCallback(() => {
    window.setTimeout(() => {
      outputRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 100);
  }, []);

  /* ── Reset all run state to idle ── */

  const resetRunState = useCallback(() => {
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
  }, [resetMemoryEntries]);

  /* ── Stop current stream ── */

  const handleStop = useCallback(() => {
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
    setStatus((prev) => {
      // If we already had stream text, treat as success; otherwise revert to idle.
      return prev === "streaming" ? "success" : "idle";
    });
  }, [disconnect, appendLog, appendMemoryEntry]);

  const hydrateSavedRun = useCallback((historyRun: HistoryRun) => {
    const replayProject = projectDetails.find((item) => item.slug === historyRun.project);

    if (replayProject) {
      setSelectedSlug(replayProject.slug);
    }

    // History stores raw JSON; extract text for text-eligible projects
    const eligible = replayProject ? isTextModeEligible(replayProject) : false;
    if (eligible) {
      try {
        const parsed = JSON.parse(historyRun.input);
        if (typeof parsed.input === "string") {
          setInput(parsed.input);
          setInputMode("text");
        } else {
          setInput(historyRun.input);
          setInputMode("json");
        }
      } catch {
        setInput(historyRun.input);
        setInputMode("json");
      }
    } else {
      setInput(historyRun.input);
      setInputMode("json");
    }
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
  }, [replaceMemoryEntries, resetMemoryEntries]);

  /* ── Execute a project run ── */

  const executeRun = useCallback(
    (
      streamMode: boolean,
      llm: LLMRequestOptions,
      overrides?: ExecuteRunOverrides,
    ) => {
      disconnect();
      const targetSlug = overrides?.slug ?? selectedSlug;
      const targetProject: ProjectDetail = projectDetails.find((p) => p.slug === targetSlug) ?? selected;
      const targetInput = overrides?.inputText ?? input;

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

      // Validate / build JSON input
      let body: Record<string, unknown>;
      if (inputMode === "text") {
        body = { input: targetInput };
      } else {
        try {
          body = JSON.parse(targetInput);
        } catch {
          setStatus("error");
          setErrorMsg("Invalid JSON — check your input syntax.");
          appendMemoryEntry({
            stepName: "Input validation",
            type: "observation",
            content: "The input is not valid JSON. Fix the syntax and try again.",
            initiallyExpanded: true,
          });
          return;
        }
      }

      if (authToken && activeSessionId !== null) {
        body.session_id = activeSessionId;
      }

      setUsedSessionContext(Boolean(authToken) && activeSessionId !== null && sessionMemoryPreview.length > 0);

      const inputStr = typeof body.input === "string" ? body.input : JSON.stringify(body);
      appendLog(`Request prepared for ${targetProject.name}`);
      appendLog(`Endpoint ${streamMode ? `/stream/${projectApiName(targetProject.apiEndpoint)}` : targetProject.apiEndpoint}`);
      if (llm.model) {
        appendLog(`Model ${llm.model}${llm.provider ? ` (${llm.provider})` : ""}`);
      }
      appendMemoryEntry({
        stepName: "Request",
        type: "action",
        content: `Prepared a ${streamMode ? "streaming" : "standard"} run for ${targetProject.name}.`,
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
          llm,
          authToken ? activeSessionId : null,
        );
        abortRef.current = abort;
      } else {
        // ── Standard path (original) ────────────────────
        setStatus("running");
        appendLog("Standard execution started");
        appendMemoryEntry({
          stepName: "Standard request",
          type: "action",
          content: "Executing the run and waiting for the complete response.",
          initiallyExpanded: true,
        });

        void (async () => {
          try {
            const result = await runProject(projectApiName(targetProject.apiEndpoint), body, authToken ?? undefined, llm);

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
                    ? `${runSucceeded ? "Response returned" : "Run failed"} in ${Math.round(data.latency)} ms.`
                    : runSucceeded
                      ? "Response returned successfully."
                      : "Run failed.",
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
        })();
      }

      scrollOutputIntoView();
    },
    [
      activeSessionId,
      appendLog,
      appendMemoryEntry,
      applySessionState,
      authToken,
      clearLocalSession,
      disconnect,
      input,
      inputMode,
      refreshHistory,
      replaceMemoryEntries,
      resetMemoryEntries,
      selected,
      selectedSlug,
      sessionMemoryPreview,
      scrollOutputIntoView,
    ],
  );

  const effectiveUsedSessionContext = activeSessionId === null ? false : usedSessionContext;

  return {
    /* State */
    selectedSlug,
    input,
    inputMode,
    textModeAvailable,
    status,
    output,
    rawData,
    streamText,
    streamChunks,
    stepStatuses,
    errorMsg,
    latency,
    confidence,
    usedSessionContext: effectiveUsedSessionContext,
    logLines,
    memoryEntries,

    /* Derived */
    selected,

    /* Refs */
    outputRef,
    streamPanelRef,

    /* Actions used by parent-level orchestration */
    hydrateSavedRun,
    scrollOutputIntoView,

    /* Setters — retained for parent-level orchestration */
    setSelectedSlug,
    setInput,
    setInputMode,
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

    /* Actions */
    disconnect,
    executeRun,
    handleStop,
    resetRunState,

    /* Memory actions */
    appendLog,
    resetMemoryEntries,
    replaceMemoryEntries,
  };
}
