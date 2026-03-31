"use client";

import Link from "next/link";
import { useState, useRef, useCallback, useEffect } from "react";
import { projectDetails } from "@/data/projects";
import type { Category, GraphNode } from "@/data/projects";
import { clearRunSession, explainRun, fetchHistory, fetchRunSession, runProject, shareRun, unshareRun, streamProject } from "@/lib/api";
import type { HistoryRun, RunExplanation, RunMemoryEntry, RunTimelineEntry, StepEvent } from "@/lib/api";
import AnimatedGraph from "@/components/animated-graph";
import AgentGraph from "@/components/agent-graph";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { TimelineReplay, type TimelineReplayFrame } from "@/components/TimelineReplay";
import { RunExplanationPanel } from "@/components/RunExplanation";
import { MemoryPanel, type MemoryEntry, type MemoryEntryType } from "@/components/memory-panel";
import { agentGraphSteps, type AgentGraphStep } from "@/components/agent-graph";
import type { NodeStatusMap } from "@/components/animated-graph";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { clearAuthToken, getStoredAuthToken } from "@/lib/auth";
import { clearStoredSessionId, getStoredSessionId, storeSessionId } from "@/lib/session";

/* ── Helpers ──────────────────────────────────────────── */

function projectApiName(apiEndpoint: string): string {
  return apiEndpoint.replace(/^\//, "").replace(/\/run$/, "");
}

function maskApiKey(value: string): string {
  if (!value) {
    return "";
  }

  if (value.length <= 7) {
    return "\u2022".repeat(value.length);
  }

  const hiddenLength = Math.max(0, Math.min(value.length - 7, 20));
  return `${value.slice(0, 4)}${"\u2022".repeat(hiddenLength)}${value.slice(-3)}`;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyObj = Record<string, any>;

/** Try to parse a JSON string, return null on failure. */
function tryParse(raw: string): AnyObj | null {
  try {
    const v = JSON.parse(raw);
    return typeof v === "object" && v !== null ? v : null;
  } catch {
    return null;
  }
}

/** Extract step-like arrays from the response data. */
function extractSteps(data: AnyObj): string[] | null {
  // Look for common step-related keys
  for (const key of [
    "steps",
    "checkpoints",
    "plan",
    "channels",
    "risk_flags",
    "risks",
    "formats",
    "sources",
    "bias_flags",
  ]) {
    const val = data[key];
    if (Array.isArray(val) && val.length > 0) {
      return val.map((v) => (typeof v === "string" ? v : JSON.stringify(v)));
    }
  }
  return null;
}

/** Build a "key metrics" summary from scalar fields. */
function extractKeyMetrics(data: AnyObj): { label: string; value: string }[] {
  const skip = new Set([
    "output",
    "report",
    "summary",
    "answer",
    "response",
    "draft",
    "code",
    "patch",
    "memo",
    "plan",
    "assessment",
    "thesis",
    "interpretation",
  ]);
  const metrics: { label: string; value: string }[] = [];
  for (const [key, val] of Object.entries(data)) {
    if (skip.has(key)) continue;
    if (Array.isArray(val)) continue;
    if (typeof val === "object" && val !== null) {
      // Flatten one level for nested score objects like { scores: { technical: 0.88 } }
      for (const [subKey, subVal] of Object.entries(val as AnyObj)) {
        if (typeof subVal === "number" || typeof subVal === "boolean" || typeof subVal === "string") {
          metrics.push({ label: `${key}.${subKey}`, value: String(subVal) });
        }
      }
      continue;
    }
    if (typeof val === "number" || typeof val === "boolean" || typeof val === "string") {
      metrics.push({ label: key, value: String(val) });
    }
  }
  return metrics;
}

/** Extract long-form text fields (report, summary, answer, etc). */
function extractTextOutput(data: AnyObj): string | null {
  for (const key of [
    "report",
    "summary",
    "answer",
    "response",
    "draft",
    "assessment",
    "interpretation",
    "memo",
    "plan",
    "thesis",
    "output",
    "code",
    "patch",
  ]) {
    const val = data[key];
    if (typeof val === "string" && val.length > 20) return val;
  }
  return null;
}

const categoryColor: Record<Category, string> = {
  GenAI: "emerald",
  LangGraph: "blue",
  CrewAI: "violet",
};

const categoryBadgeTone: Record<Category, string> = {
  GenAI: "bg-[var(--category-genai-bg)] text-[var(--category-genai-text)]",
  LangGraph: "bg-[var(--category-langgraph-bg)] text-[var(--category-langgraph-text)]",
  CrewAI: "bg-[var(--category-crewai-bg)] text-[var(--category-crewai-text)]",
};

function summarizeInputPayload(raw: string) {
  const trimmed = raw.trim();
  if (!trimmed) return "Empty request body.";

  const parsed = tryParse(trimmed);
  if (!parsed) {
    return trimmed.length > 240 ? `${trimmed.slice(0, 237)}...` : trimmed;
  }

  if (typeof parsed.input === "string" && parsed.input.trim()) {
    return parsed.input.length > 240 ? `${parsed.input.slice(0, 237)}...` : parsed.input;
  }

  const serialized = JSON.stringify(parsed);
  return serialized.length > 240 ? `${serialized.slice(0, 237)}...` : serialized;
}

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

function formatLogTimestamp(date = new Date()) {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
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

function statusTone(status: "idle" | "running" | "done" | "error") {
  if (status === "running") {
    return "border-[var(--running-border)] bg-[var(--running-bg)] text-[var(--running-text)]";
  }
  if (status === "done") {
    return "border-[var(--done-border)] bg-[var(--done-bg)] text-[var(--done-text)]";
  }
  if (status === "error") {
    return "border-[var(--danger-border)] bg-[var(--danger-bg)] text-[var(--danger-text)]";
  }
  return "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]";
}

function statusLabel(status: "idle" | "running" | "done" | "error") {
  if (status === "running") return "Running";
  if (status === "done") return "Done";
  if (status === "error") return "Failed";
  return "Queued";
}

function formatRunTimestamp(value: string | null) {
  if (!value) return "Unknown time";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown time";
  return parsed.toLocaleString();
}

function formatMemoryStepName(stepId: string, graphNodes: GraphNode[]) {
  const matchedNode = graphNodes.find((node) => {
    return normalizeStepKey(node.id) === normalizeStepKey(stepId)
      || normalizeStepKey(node.label) === normalizeStepKey(stepId);
  });

  if (matchedNode) {
    return matchedNode.label;
  }

  const cleaned = stepId.replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
  return cleaned ? cleaned.replace(/\b\w/g, (character) => character.toUpperCase()) : "Agent Step";
}

function normalizeStepKey(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function matchesLifecycleKeyword(label: string, keywords: string[]) {
  return keywords.some((keyword) => label.includes(keyword));
}

function inferLifecycleStep(stepId: string, graphNodes: GraphNode[]): AgentGraphStep | null {
  const normalizedStep = normalizeStepKey(stepId);
  const matchedNode = graphNodes.find((node) => {
    return normalizeStepKey(node.id) === normalizedStep || normalizeStepKey(node.label) === normalizedStep;
  });
  const descriptor = normalizeStepKey(
    [matchedNode?.id, matchedNode?.label, stepId].filter(Boolean).join(" "),
  );

  if (matchesLifecycleKeyword(descriptor, ["planner", "plan", "schema", "spec", "perception", "analyzer", "classifier", "screener"])) {
    return "planner";
  }

  if (matchesLifecycleKeyword(descriptor, ["evaluator", "critic", "validator", "review", "reviewer", "auditor", "red team", "redteam", "adjuster", "checkpoint", "router"])) {
    return "evaluator";
  }

  if (matchesLifecycleKeyword(descriptor, ["final", "formatter", "summarizer", "summary", "reporter", "report", "compiler", "coordinator", "responder", "insight", "seo"])) {
    return "final";
  }

  if (matchedNode) {
    const matchedIndex = graphNodes.findIndex((node) => node.id === matchedNode.id);

    if (matchedIndex === 0) {
      return "planner";
    }

    if (matchedIndex === graphNodes.length - 1) {
      return "final";
    }

    if (matchedIndex === graphNodes.length - 2) {
      return "evaluator";
    }

    return "executor";
  }

  if (matchesLifecycleKeyword(descriptor, ["executor"])) {
    return "executor";
  }

  return null;
}

function lifecycleState(status: RunStatus): {
  activeStep: AgentGraphStep | null;
  completedSteps: AgentGraphStep[];
} {
  if (status === "connecting") {
    return { activeStep: "planner", completedSteps: [] };
  }

  if (status === "running" || status === "streaming") {
    return { activeStep: "executor", completedSteps: ["planner"] };
  }

  if (status === "error") {
    return { activeStep: "evaluator", completedSteps: ["planner", "executor"] };
  }

  if (status === "success") {
    return {
      activeStep: "final",
      completedSteps: ["planner", "executor", "evaluator"],
    };
  }

  return { activeStep: null, completedSteps: [] };
}

function realtimeLifecycleState(
  status: RunStatus,
  graphNodes: GraphNode[],
  stepStatuses: NodeStatusMap,
): {
  activeStep: AgentGraphStep | null;
  completedSteps: AgentGraphStep[];
} {
  const lifecycleStatuses: Record<AgentGraphStep, "idle" | "running" | "done" | "error"> = {
    planner: "idle",
    executor: "idle",
    evaluator: "idle",
    final: "idle",
  };

  let mappedCount = 0;

  for (const [stepId, stepStatus] of Object.entries(stepStatuses)) {
    const lifecycleStep = inferLifecycleStep(stepId, graphNodes);

    if (!lifecycleStep) {
      continue;
    }

    mappedCount += 1;

    if (stepStatus === "running") {
      lifecycleStatuses[lifecycleStep] = "running";
      continue;
    }

    if (stepStatus === "error") {
      lifecycleStatuses[lifecycleStep] = "error";
      continue;
    }

    if (lifecycleStatuses[lifecycleStep] !== "running" && lifecycleStatuses[lifecycleStep] !== "error") {
      lifecycleStatuses[lifecycleStep] = "done";
    }
  }

  if (mappedCount === 0) {
    return lifecycleState(status);
  }

  const completedSteps = agentGraphSteps.filter((step) => lifecycleStatuses[step] === "done");
  const failedStep = [...agentGraphSteps]
    .reverse()
    .find((step) => lifecycleStatuses[step] === "error") ?? null;
  if (failedStep) {
    return { activeStep: failedStep, completedSteps };
  }

  const activeStep = [...agentGraphSteps]
    .reverse()
    .find((step) => lifecycleStatuses[step] === "running") ?? null;

  if (!activeStep && status === "success" && !completedSteps.includes("final")) {
    return { activeStep: "final", completedSteps };
  }

  if (!activeStep && status === "error" && !completedSteps.includes("evaluator")) {
    return { activeStep: "evaluator", completedSteps };
  }

  if (!activeStep && status === "connecting" && completedSteps.length === 0) {
    return { activeStep: "planner", completedSteps };
  }

  return { activeStep, completedSteps };
}

function lifecycleLabel(step: AgentGraphStep | null) {
  if (!step) {
    return "Idle";
  }

  return `${step.charAt(0).toUpperCase()}${step.slice(1)}`;
}

type WorkspaceState = "idle" | "thinking" | "streaming" | "completed" | "error";

function workspaceStateLabel(state: WorkspaceState) {
  if (state === "thinking") return "Thinking";
  if (state === "streaming") return "Streaming";
  if (state === "completed") return "Completed";
  if (state === "error") return "Error";
  return "Idle";
}

function workspaceStateTone(state: WorkspaceState) {
  if (state === "thinking") {
    return "border-[var(--running-border)] bg-[var(--running-bg)] text-[var(--running-text)]";
  }
  if (state === "streaming") {
    return "border-[var(--accent-border-soft)] bg-[var(--accent-soft-strong)] text-[color-mix(in_srgb,var(--accent-solid)_72%,var(--text)_28%)]";
  }
  if (state === "completed") {
    return "border-[var(--done-border)] bg-[var(--done-bg)] text-[var(--done-text)]";
  }
  if (state === "error") {
    return "border-[var(--danger-border)] bg-[var(--danger-bg)] text-[var(--danger-text)]";
  }
  return "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]";
}

function assistantCardTone(state: WorkspaceState) {
  if (state === "thinking") {
    return "border-[var(--running-border)] bg-[color-mix(in_srgb,var(--card)_90%,var(--running-bg)_10%)]";
  }
  if (state === "streaming") {
    return "border-[var(--accent-border-soft)] bg-[color-mix(in_srgb,var(--card)_92%,var(--accent-soft)_8%)]";
  }
  if (state === "completed") {
    return "border-[var(--done-border)] bg-[color-mix(in_srgb,var(--card)_92%,var(--done-bg)_8%)]";
  }
  if (state === "error") {
    return "border-[var(--danger-border)] bg-[var(--danger-bg)]";
  }
  return "border-[var(--line)] bg-[var(--card)]";
}

function assistantStateTitle(state: WorkspaceState) {
  if (state === "thinking") return "Working through your request";
  if (state === "streaming") return "Streaming response";
  if (state === "completed") return "Response ready";
  if (state === "error") return "Something went wrong";
  return "Ready when you are";
}

function inferMemoryEntryType(
  stepId: string,
  graphNodes: GraphNode[],
  status: StepEvent["status"],
): MemoryEntryType {
  if (status !== "running") {
    return "observation";
  }

  const lifecycle = inferLifecycleStep(stepId, graphNodes);
  if (lifecycle === "planner" || lifecycle === "evaluator") {
    return "thought";
  }

  return "action";
}

function memoryContentForStep(
  stepName: string,
  lifecycle: AgentGraphStep | null,
  status: StepEvent["status"],
  error?: string,
) {
  if (status === "running") {
    if (lifecycle === "planner") {
      return `${stepName} is reasoning through the next plan.`;
    }

    if (lifecycle === "evaluator") {
      return `${stepName} is reviewing the current state before the next handoff.`;
    }

    if (lifecycle === "final") {
      return `${stepName} is shaping the final response.`;
    }

    return `${stepName} is executing its assigned action.`;
  }

  if (status === "done") {
    return `${stepName} completed and handed control to the next stage.`;
  }

  return error ? `${stepName} failed: ${error}` : `${stepName} failed during execution.`;
}

function isRunMemoryEntry(value: unknown): value is RunMemoryEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.step === "string"
    && typeof candidate.content === "string"
    && (candidate.type === "thought" || candidate.type === "action" || candidate.type === "observation");
}

function mapRunMemoryEntries(entries: RunMemoryEntry[]): MemoryEntry[] {
  return entries.map((entry, index) => ({
    id: `memory-${index + 1}`,
    stepName: entry.step,
    type: entry.type,
    content: entry.content,
    initiallyExpanded: index === entries.length - 1,
  }));
}

function isRunTimelineEntry(value: unknown): value is RunTimelineEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.timestamp === "number"
    && typeof candidate.step === "string"
    && typeof candidate.event === "string"
    && typeof candidate.data === "string";
}

function formatTimelineTimestamp(timestamp: number) {
  return `+${timestamp.toFixed(timestamp >= 10 ? 1 : 2)}s`;
}

function formatTimelineEventLabel(event: string) {
  if (event === "running") return "Running";
  if (event === "done") return "Completed";
  if (event === "error") return "Failed";
  if (event === "completed") return "Run complete";
  if (event === "failed") return "Run failed";
  return event.replace(/[_-]+/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function timelineEventToNodeStatus(event: string): "running" | "done" | "error" | null {
  if (event === "running") return "running";
  if (event === "done" || event === "completed") return "done";
  if (event === "error" || event === "failed") return "error";
  return null;
}

function buildReplayNodeStatuses(entries: RunTimelineEntry[], graphNodes: GraphNode[]): NodeStatusMap {
  const statuses: NodeStatusMap = {};

  for (const entry of entries) {
    const matchedNode = graphNodes.find((node) => {
      return normalizeStepKey(node.id) === normalizeStepKey(entry.step)
        || normalizeStepKey(node.label) === normalizeStepKey(entry.step);
    });
    if (!matchedNode) {
      continue;
    }

    const nextStatus = timelineEventToNodeStatus(entry.event);
    if (!nextStatus) {
      continue;
    }

    if (nextStatus === "running") {
      for (const [stepId, stepStatus] of Object.entries(statuses)) {
        if (stepId !== matchedNode.id && stepStatus === "running") {
          statuses[stepId] = "done";
        }
      }
    }

    statuses[matchedNode.id] = nextStatus;
  }

  return statuses;
}

function buildReplayLogLines(entries: RunTimelineEntry[], graphNodes: GraphNode[]): string[] {
  return entries.map((entry) => {
    return `[${formatTimelineTimestamp(entry.timestamp)}] ${formatMemoryStepName(entry.step, graphNodes)} → ${formatTimelineEventLabel(entry.event)}${entry.data ? ` · ${entry.data}` : ""}`;
  });
}

function replayRunStatus(frame: TimelineReplayFrame | null, totalEvents: number): RunStatus {
  if (!frame || frame.currentIndex < 0 || totalEvents === 0) {
    return "idle";
  }

  if (frame.currentEntry?.event === "error" || frame.currentEntry?.event === "failed") {
    return "error";
  }

  if (frame.currentIndex >= totalEvents - 1) {
    return "success";
  }

  return "streaming";
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

type RunStatus = "idle" | "connecting" | "running" | "streaming" | "success" | "error";

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
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [sessionMemoryPreview, setSessionMemoryPreview] = useState<string[]>([]);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [clearingSession, setClearingSession] = useState(false);
  const [usedSessionContext, setUsedSessionContext] = useState(false);
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());
  const [keyFocused, setKeyFocused] = useState(false);
  const [historyRuns, setHistoryRuns] = useState<HistoryRun[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
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

  const clearLocalSession = useCallback(() => {
    setActiveSessionId(null);
    setSessionMemoryPreview([]);
    setUsedSessionContext(false);
    clearStoredSessionId();
  }, []);

  const applySessionState = useCallback((sessionId: number | null, memory: string[]) => {
    if (sessionId === null) {
      clearLocalSession();
      return;
    }

    setActiveSessionId(sessionId);
    setSessionMemoryPreview(memory.slice(-5));
    storeSessionId(sessionId);
  }, [clearLocalSession]);

  const loadSession = useCallback(async (sessionId: number, token: string) => {
    setSessionLoading(true);
    try {
      const response = await fetchRunSession(sessionId, token);
      applySessionState(response.id, response.memory);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load session.";
      if (message.startsWith("401") || message.startsWith("404")) {
        clearLocalSession();
      }
    } finally {
      setSessionLoading(false);
    }
  }, [applySessionState, clearLocalSession]);

  const loadHistory = useCallback(async (token: string) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await fetchHistory(token);
      setHistoryRuns(
        response.runs.map((run) => ({
          ...run,
          memory: Array.isArray(run.memory) ? run.memory.filter(isRunMemoryEntry) : [],
          timeline: Array.isArray(run.timeline) ? run.timeline.filter(isRunTimelineEntry) : [],
        })),
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load history.";
      setHistoryError(message);
      if (message.startsWith("401")) {
        clearAuthToken();
        setAuthToken(null);
        setHistoryRuns([]);
        clearLocalSession();
      }
    } finally {
      setHistoryLoading(false);
    }
  }, [clearLocalSession]);

  useEffect(() => {
    const token = getStoredAuthToken();
    setAuthToken(token);
    if (token) {
      void loadHistory(token);
      const storedSessionId = getStoredSessionId();
      if (storedSessionId !== null) {
        void loadSession(storedSessionId, token);
      }
    } else {
      clearLocalSession();
    }
  }, [clearLocalSession, loadHistory, loadSession]);

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
              void loadHistory(authToken);
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
            setRawData(data);
            setOutput(JSON.stringify(data, null, 2));
          }
          if (!runSucceeded) {
            setErrorMsg(typeof data?.output === "string" ? data.output : "Execution failed.");
          }
          if (authToken) {
            void loadHistory(authToken);
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
    if (!authToken || activeSessionId === null) {
      return;
    }

    setClearingSession(true);
    try {
      const response = await clearRunSession(activeSessionId, authToken);
      applySessionState(response.id, response.memory);
      setUsedSessionContext(false);
      appendLog("Session memory cleared");
    } catch {
      appendLog("Failed to clear session memory");
    } finally {
      setClearingSession(false);
    }
  }

  function handleLogout() {
    disconnect();
    clearReplay();
    clearExplanation();
    clearLocalSession();
    clearAuthToken();
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
  const recentRuns = historyRuns.slice(0, 6);
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

        {/* ════════════ LEFT: Input + Project Selector ════════════ */}
        <aside className="flex flex-col gap-7 xl:sticky xl:top-24">

          {/* ── Input Card ── */}
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
              onChange={(e) => setInput(e.target.value)}
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
                  onChange={(e) => setStreamMode(e.target.checked)}
                  disabled={isActive}
                  className="accent-[var(--accent-solid)]"
                />
                Stream
              </label>

              {isActive ? (
                <button type="button" onClick={handleStop} className="button-base button-secondary button-sm button-pill">
                  Stop
                </button>
              ) : (
                <button type="button" onClick={handleRun} disabled={!apiKey.trim()} className="button-base button-primary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50">
                  Send request
                </button>
              )}
            </div>
          </section>

          {/* ── API Key (BYOK) ── */}
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
                onChange={(e) => setApiKey(e.target.value)}
                onFocus={() => setKeyFocused(true)}
                onBlur={() => setKeyFocused(false)}
                placeholder="AIza..."
                disabled={isActive}
                className={`input-shell w-full rounded-[1rem] px-4 py-2.5 font-mono text-xs leading-6 disabled:cursor-not-allowed disabled:opacity-60${errorMsg && /api.key|Missing x-api-key/i.test(errorMsg) ? " ring-2 ring-red-500/60" : ""}`}
                spellCheck={false}
                autoComplete="off"
              />
              {apiKey && !keyFocused && (
                <button
                  type="button"
                  onClick={() => setApiKey("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
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

          {/* ── Project Selector ── */}
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
                    onClick={() => handleProjectChange(project.slug)}
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

          {/* ── Account & History ── */}
          <section className="surface-card rounded-[1.75rem] p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Account</p>
                <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">
                  {authToken ? "Authenticated" : "Sign in required"}
                </p>
              </div>
              {authToken ? (
                <button type="button" onClick={handleLogout} className="button-base button-secondary button-sm button-pill">Log out</button>
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
                        onClick={() => void handleClearSession()}
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
                        const replaySelected = activeReplayRun?.id === run.id;
                        const explanationSelected = activeExplanationRun?.id === run.id;
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
                                  onClick={() => handleHistoryReplay(run)}
                                  disabled={!canReplay}
                                  className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Replay
                                </button>
                                <button
                                  type="button"
                                  onClick={() => void handleHistoryExplain(run)}
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
                                <button type="button" onClick={() => handleHistoryRerun(run)} className="button-base button-primary button-sm button-pill">
                                  Re-run
                                </button>
                                <button
                                  type="button"
                                  onClick={() => void (run.is_public ? handleUnshare(run) : handleShare(run))}
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
