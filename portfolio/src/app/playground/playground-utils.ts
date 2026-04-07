import type { Category, GraphNode } from "@/data/projects";
import type { RunMemoryEntry, RunTimelineEntry, StepEvent } from "@/lib/api";
import type { MemoryEntry, MemoryEntryType } from "@/components/memory-panel";
import type { NodeStatusMap } from "@/components/animated-graph";
import type { TimelineReplayFrame } from "@/components/TimelineReplay";
import { agentGraphSteps, type AgentGraphStep } from "@/components/agent-graph";

export type RunStatus = "idle" | "connecting" | "running" | "streaming" | "success" | "error";

export type AnyObj = Record<string, unknown>;

export function projectApiName(apiEndpoint: string): string {
  return apiEndpoint.replace(/^\//, "").replace(/\/run$/, "");
}

export function maskApiKey(value: string): string {
  if (!value) {
    return "";
  }

  if (value.length <= 7) {
    return "\u2022".repeat(value.length);
  }

  const hiddenLength = Math.max(0, Math.min(value.length - 7, 20));
  return `${value.slice(0, 4)}${"\u2022".repeat(hiddenLength)}${value.slice(-3)}`;
}

export function tryParse(raw: string): AnyObj | null {
  try {
    const value = JSON.parse(raw);
    return typeof value === "object" && value !== null ? (value as AnyObj) : null;
  } catch {
    return null;
  }
}

export function extractSteps(data: AnyObj): string[] | null {
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
    const value = data[key];
    if (Array.isArray(value) && value.length > 0) {
      return value.map((item) => (typeof item === "string" ? item : JSON.stringify(item)));
    }
  }

  return null;
}

export function extractKeyMetrics(data: AnyObj): { label: string; value: string }[] {
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

  for (const [key, value] of Object.entries(data)) {
    if (skip.has(key) || Array.isArray(value)) {
      continue;
    }

    if (typeof value === "object" && value !== null) {
      for (const [subKey, subValue] of Object.entries(value as AnyObj)) {
        if (typeof subValue === "number" || typeof subValue === "boolean" || typeof subValue === "string") {
          metrics.push({ label: `${key}.${subKey}`, value: String(subValue) });
        }
      }
      continue;
    }

    if (typeof value === "number" || typeof value === "boolean" || typeof value === "string") {
      metrics.push({ label: key, value: String(value) });
    }
  }

  return metrics;
}

export function extractTextOutput(data: AnyObj): string | null {
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
    const value = data[key];
    if (typeof value === "string" && value.length > 20) {
      return value;
    }
  }

  return null;
}

export function summarizeInputPayload(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) {
    return "Empty request body.";
  }

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

export function formatRunTimestamp(value: string | null): string {
  if (!value) {
    return "Unknown time";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown time";
  }

  return parsed.toLocaleString();
}

export function isRunMemoryEntry(value: unknown): value is RunMemoryEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.step === "string"
    && typeof candidate.content === "string"
    && (candidate.type === "thought" || candidate.type === "action" || candidate.type === "observation");
}

export function mapRunMemoryEntries(entries: RunMemoryEntry[]): MemoryEntry[] {
  return entries.map((entry, index) => ({
    id: `memory-${index + 1}`,
    stepName: entry.step,
    type: entry.type,
    content: entry.content,
    initiallyExpanded: index === entries.length - 1,
  }));
}

export function isRunTimelineEntry(value: unknown): value is RunTimelineEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.timestamp === "number"
    && typeof candidate.step === "string"
    && typeof candidate.event === "string"
    && typeof candidate.data === "string";
}

function normalizeStepKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function formatMemoryStepName(stepId: string, graphNodes: GraphNode[]): string {
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

function formatTimelineTimestamp(timestamp: number): string {
  return `+${timestamp.toFixed(timestamp >= 10 ? 1 : 2)}s`;
}

function formatTimelineEventLabel(event: string): string {
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

export function buildReplayNodeStatuses(entries: RunTimelineEntry[], graphNodes: GraphNode[]): NodeStatusMap {
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

export function buildReplayLogLines(entries: RunTimelineEntry[], graphNodes: GraphNode[]): string[] {
  return entries.map((entry) => {
    return `[${formatTimelineTimestamp(entry.timestamp)}] ${formatMemoryStepName(entry.step, graphNodes)} → ${formatTimelineEventLabel(entry.event)}${entry.data ? ` · ${entry.data}` : ""}`;
  });
}

export function replayRunStatus(frame: TimelineReplayFrame | null, totalEvents: number): RunStatus {
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

/* ── Category styling ─────────────────────────────────── */

export const categoryColor: Record<Category, string> = {
  GenAI: "emerald",
  LangGraph: "blue",
  CrewAI: "violet",
};

export const categoryBadgeTone: Record<Category, string> = {
  GenAI: "bg-[var(--category-genai-bg)] text-[var(--category-genai-text)]",
  LangGraph: "bg-[var(--category-langgraph-bg)] text-[var(--category-langgraph-text)]",
  CrewAI: "bg-[var(--category-crewai-bg)] text-[var(--category-crewai-text)]",
};

/* ── Status helpers ───────────────────────────────────── */

export function statusTone(status: "idle" | "running" | "done" | "error") {
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

export function statusLabel(status: "idle" | "running" | "done" | "error") {
  if (status === "running") return "Running";
  if (status === "done") return "Done";
  if (status === "error") return "Failed";
  return "Queued";
}

export function formatLogTimestamp(date = new Date()) {
  return [
    String(date.getHours()).padStart(2, "0"),
    String(date.getMinutes()).padStart(2, "0"),
    String(date.getSeconds()).padStart(2, "0"),
  ].join(":");
}

/* ── Lifecycle helpers ────────────────────────────────── */

function matchesLifecycleKeyword(label: string, keywords: string[]) {
  return keywords.some((keyword) => label.includes(keyword));
}

export function inferLifecycleStep(stepId: string, graphNodes: GraphNode[]): AgentGraphStep | null {
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

export function realtimeLifecycleState(
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

export function lifecycleLabel(step: AgentGraphStep | null) {
  if (!step) {
    return "Idle";
  }

  return `${step.charAt(0).toUpperCase()}${step.slice(1)}`;
}

/* ── Workspace state helpers ──────────────────────────── */

export type WorkspaceState = "idle" | "thinking" | "streaming" | "completed" | "error";

export function workspaceStateLabel(state: WorkspaceState) {
  if (state === "thinking") return "Thinking";
  if (state === "streaming") return "Streaming";
  if (state === "completed") return "Completed";
  if (state === "error") return "Error";
  return "Idle";
}

export function workspaceStateTone(state: WorkspaceState) {
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

export function assistantCardTone(state: WorkspaceState) {
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

export function assistantStateTitle(state: WorkspaceState) {
  if (state === "thinking") return "Working through your request";
  if (state === "streaming") return "Streaming response";
  if (state === "completed") return "Response ready";
  if (state === "error") return "Something went wrong";
  return "Ready when you are";
}

/* ── Memory helpers ───────────────────────────────────── */

export function inferMemoryEntryType(
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

export function memoryContentForStep(
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