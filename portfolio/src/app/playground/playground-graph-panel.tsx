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
            onFrameChange={onReplayFrameChange}
            onClose={onReplayClose}
          />
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(300px,0.95fr)]">
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
  );
}