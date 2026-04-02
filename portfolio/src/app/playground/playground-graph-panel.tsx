"use client";

import AnimatedGraph, { type NodeStatusMap } from "@/components/animated-graph";
import AgentGraph from "@/components/agent-graph";
import { MemoryPanel, type MemoryEntry } from "@/components/memory-panel";
import { TimelineReplay, type TimelineReplayFrame } from "@/components/TimelineReplay";
import type { ProjectDetail } from "@/data/projects";
import type { HistoryRun } from "@/lib/api";
import {
  buildReplayNodeStatuses,
  categoryColor,
  formatMemoryStepName,
  lifecycleLabel,
  replayRunStatus,
  realtimeLifecycleState,
  statusLabel,
  statusTone,
  type RunStatus,
  type WorkspaceState,
} from "./playground-utils";
import { ReplayStateBadge, StatCard, WorkspaceStateBadge } from "./playground-widgets";

interface PlaygroundGraphPanelProps {
  activeReplayRun: HistoryRun | null;
  graphProject: ProjectDetail;
  memoryEntries: MemoryEntry[];
  onReplayClose: () => void;
  onReplayFrameChange: (frame: TimelineReplayFrame | null) => void;
  replayAutoplayKey: number;
  replayFrame: TimelineReplayFrame | null;
  replaySourceLabel?: string;
  selected: ProjectDetail;
  status: RunStatus;
  stepStatuses: NodeStatusMap;
  steps: string[] | null;
  streamMode: boolean;
  workspaceState: WorkspaceState;
}

export function PlaygroundGraphPanel({
  activeReplayRun,
  graphProject,
  memoryEntries,
  onReplayClose,
  onReplayFrameChange,
  replayAutoplayKey,
  replayFrame,
  replaySourceLabel,
  selected,
  status,
  stepStatuses,
  steps,
  streamMode,
  workspaceState,
}: PlaygroundGraphPanelProps) {
  const graphNodes = graphProject.graph.nodes;
  const showAgentBreakdown = graphProject.category === "LangGraph" || graphProject.category === "CrewAI";
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
  const accent = categoryColor[graphProject.category];

  return (
    <div className="space-y-8">
      {/* ── Run Lifecycle — full width hero ── */}
      <section className="surface-card rounded-[1.75rem] p-6 sm:p-8 transition-all duration-300 ease-in-out">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Run Lifecycle</p>
            <p className="mt-1.5 text-lg font-semibold text-[var(--foreground)]">
              {activeReplayRun
                ? "Saved timeline events are driving the lifecycle below."
                : "Planner → Executor → Evaluator → Final"}
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
          </div>
        </div>
        <div className="mt-6">
          <AgentGraph activeStep={runLifecycle.activeStep} completedSteps={runLifecycle.completedSteps} />
        </div>
      </section>

      {/* ── Execution Flow — full width hero ── */}
      <section className="surface-card rounded-[1.75rem] p-6 sm:p-8 transition-all duration-300 ease-in-out">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              {activeReplayRun
                ? showAgentBreakdown ? "Replay agent flow" : "Replay execution flow"
                : showAgentBreakdown ? "Agent flow" : "Execution flow"}
            </p>
            <p className="mt-1.5 text-lg font-semibold text-[var(--foreground)]">
              {activeReplayRun
                ? "Node transitions are synchronized with the replay timeline."
                : "Node transitions update live as streamed step events arrive."}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
              {graphNodes.length} {showAgentBreakdown ? "agents" : "nodes"}
            </span>
          </div>
        </div>
        <div className="mt-6">
          <AnimatedGraph
            nodes={graphNodes}
            edges={graphProject.graph.edges}
            accentColor={accent}
            liveStatuses={Object.keys(effectiveStepStatuses).length > 0 ? effectiveStepStatuses : undefined}
            speed={Object.keys(effectiveStepStatuses).length > 0 ? undefined : 1000}
          />
        </div>
      </section>

      {/* ── Agent Graph inspector — remaining cards ── */}
      <section className="surface-card rounded-[1.75rem] p-6 sm:p-7 transition-all duration-300 ease-in-out">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Agent Graph</p>
            <p className="mt-1 text-lg font-semibold text-[var(--foreground)]">
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
              onFrameChange={onReplayFrameChange}
              onClose={onReplayClose}
            />
          </div>
        )}

        <div className="mt-6 space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Project" value={selected.name} />
            <StatCard label="Mode" value={streamMode ? "SSE Stream" : "Batch POST"} />
            <StatCard label={showAgentBreakdown ? "Agent Nodes" : "Flow Nodes"} value={String(graphNodes.length)} />
            <StatCard label="Steps" value={steps ? String(steps.length) : workspaceState === "completed" ? "Not returned" : "Live"} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-3 rounded-[1.35rem] border border-[var(--line)] bg-[var(--card)] p-5 transition-all duration-300 ease-in-out sm:p-6">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                {activeReplayRun ? "Replay Step Status" : "Step Status"}
              </p>
              <div className="grid gap-3">
                {liveNodeItems.map((node) => (
                  <div
                    key={node.id}
                    className={`flex items-start justify-between gap-4 rounded-[1rem] border px-4 py-3.5 text-sm transition-all duration-300 ease-in-out ${statusTone(node.status)}`}
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-[var(--foreground)]">{node.label}</p>
                      <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.16em] opacity-75">{node.id}</p>
                    </div>
                    <span className="rounded-full border border-current/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]">
                      {statusLabel(node.status)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <MemoryPanel
              className="p-5 sm:p-6"
              entries={memoryEntries}
              description={activeReplayRun
                ? "Memory captured for this saved run. Replay controls above animate the execution timeline."
                : "Ordered trace of what the agent is thinking, doing, and observing during the run."}
              emptyState={activeReplayRun
                ? "This saved run does not include persisted memory entries."
                : "Start a run to populate agent memory with thoughts, actions, and observations."}
            />
          </div>

          {steps && steps.length > 0 && (
            <div className="rounded-[1.35rem] border border-[var(--line)] bg-[var(--card)] p-5 transition-all duration-300 ease-in-out sm:p-6">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Parsed Steps</p>
              <ol className="mt-4 space-y-3 text-sm leading-7 text-[var(--foreground)]">
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
      </section>
    </div>
  );
}