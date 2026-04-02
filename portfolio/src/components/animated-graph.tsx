"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { GraphNode, GraphEdge } from "@/data/projects";

/* ── Layout (shared logic with flow-diagram) ──────────── */

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

const NODE_W = 150;
const NODE_H = 48;
const GAP_X = 56;
const GAP_Y = 76;
const PAD = 28;

function topoSort(nodes: GraphNode[], edges: GraphEdge[]): string[] {
  const inDeg: Record<string, number> = {};
  const adj: Record<string, string[]> = {};
  for (const n of nodes) {
    inDeg[n.id] = 0;
    adj[n.id] = [];
  }
  for (const e of edges) {
    adj[e.from]?.push(e.to);
    if (inDeg[e.to] !== undefined) inDeg[e.to]++;
  }
  const order: string[] = [];
  const queue = nodes.filter((n) => inDeg[n.id] === 0).map((n) => n.id);
  const visited = new Set<string>();
  while (queue.length) {
    const id = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id);
    order.push(id);
    for (const next of adj[id] ?? []) {
      inDeg[next]--;
      if (inDeg[next] === 0) queue.push(next);
    }
  }
  for (const n of nodes) {
    if (!visited.has(n.id)) order.push(n.id);
  }
  return order;
}

function layoutNodes(nodes: GraphNode[], edges: GraphEdge[]): PositionedNode[] {
  const order = topoSort(nodes, edges);
  const maxPerRow = Math.min(4, nodes.length);
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));
  return order.map((id, i) => ({
    ...nodeMap[id],
    x: PAD + (i % maxPerRow) * (NODE_W + GAP_X),
    y: PAD + Math.floor(i / maxPerRow) * (NODE_H + GAP_Y),
  }));
}

function nodeCenter(n: PositionedNode) {
  return { cx: n.x + NODE_W / 2, cy: n.y + NODE_H / 2 };
}

function edgeAnchor(node: PositionedNode, target: { cx: number; cy: number }) {
  const { cx, cy } = nodeCenter(node);
  const dx = target.cx - cx;
  const dy = target.cy - cy;
  const sx = (NODE_W / 2) / Math.abs(dx || 1);
  const sy = (NODE_H / 2) / Math.abs(dy || 1);
  const s = Math.min(sx, sy);
  return { x: cx + dx * s, y: cy + dy * s };
}

/* ── Types ────────────────────────────────────────────── */

type StepStatus = "idle" | "running" | "done" | "error";

interface StepState {
  nodeStatuses: Record<string, StepStatus>;
  activeEdge: { from: string; to: string } | null;
  currentStep: number;
  totalSteps: number;
  playing: boolean;
}

/* ── Colors ───────────────────────────────────────────── */

const PALETTES: Record<string, {
  idle: { fill: string; stroke: string; text: string };
  running: { fill: string; stroke: string; text: string };
  done: { fill: string; stroke: string; text: string };
  error: { fill: string; stroke: string; text: string };
  edgeDefault: string;
  edgeActive: string;
}> = {
  blue: {
    idle:    { fill: "var(--viz-idle-fill)", stroke: "var(--viz-idle-stroke)", text: "var(--viz-idle-text)" },
    running: { fill: "var(--viz-running-blue-fill)", stroke: "var(--viz-running-blue-stroke)", text: "var(--viz-running-blue-text)" },
    done:    { fill: "var(--viz-done-fill)", stroke: "var(--viz-done-stroke)", text: "var(--viz-done-text)" },
    error:   { fill: "var(--danger-bg)", stroke: "var(--danger-text)", text: "var(--danger-text)" },
    edgeDefault: "var(--viz-edge-default)",
    edgeActive: "var(--viz-running-blue-stroke)",
  },
  emerald: {
    idle:    { fill: "var(--viz-idle-fill)", stroke: "var(--viz-idle-stroke)", text: "var(--viz-idle-text)" },
    running: { fill: "var(--viz-running-emerald-fill)", stroke: "var(--viz-running-emerald-stroke)", text: "var(--viz-running-emerald-text)" },
    done:    { fill: "var(--viz-done-fill)", stroke: "var(--viz-done-stroke)", text: "var(--viz-done-text)" },
    error:   { fill: "var(--danger-bg)", stroke: "var(--danger-text)", text: "var(--danger-text)" },
    edgeDefault: "var(--viz-edge-default)",
    edgeActive: "var(--viz-running-emerald-stroke)",
  },
  violet: {
    idle:    { fill: "var(--viz-idle-fill)", stroke: "var(--viz-idle-stroke)", text: "var(--viz-idle-text)" },
    running: { fill: "var(--viz-running-violet-fill)", stroke: "var(--viz-running-violet-stroke)", text: "var(--viz-running-violet-text)" },
    done:    { fill: "var(--viz-done-fill)", stroke: "var(--viz-done-stroke)", text: "var(--viz-done-text)" },
    error:   { fill: "var(--danger-bg)", stroke: "var(--danger-text)", text: "var(--danger-text)" },
    edgeDefault: "var(--viz-edge-default)",
    edgeActive: "var(--viz-running-violet-stroke)",
  },
};

/* ── Status icon ──────────────────────────────────────── */

function StatusIcon({ status }: { status: StepStatus }) {
  if (status === "running") {
    return (
      <circle r="5" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="20" strokeDashoffset="0">
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="0.8s" repeatCount="indefinite" />
      </circle>
    );
  }
  if (status === "done") {
    return <path d="M-3.5 0.5L-1 3L3.5-2.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />;
  }
  if (status === "error") {
    return <path d="M-3 -3L3 3M3 -3L-3 3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />;
  }
  return <circle r="3" fill="currentColor" opacity="0.3" />;
}

function statusLabel(status: StepStatus) {
  if (status === "running") return "Running";
  if (status === "done") return "Done";
  if (status === "error") return "Failed";
  return "Queued";
}

/* ── Component ────────────────────────────────────────── */

export type NodeStatusMap = Record<string, StepStatus>;

interface AnimatedGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  accentColor?: string;
  /** Auto-play speed in ms per step (default 1200) */
  speed?: number;
  /**
   * When provided, the graph is driven externally (e.g. from SSE step events).
   * The internal Play/Step/Reset controls are hidden.
   */
  liveStatuses?: NodeStatusMap;
}

export default function AnimatedGraph({
  nodes,
  edges,
  accentColor = "blue",
  speed = 1200,
  liveStatuses,
}: AnimatedGraphProps) {
  const isLive = liveStatuses !== undefined;
  const positioned = layoutNodes(nodes, edges);
  const posMap = Object.fromEntries(positioned.map((n) => [n.id, n]));
  const palette = PALETTES[accentColor] ?? PALETTES.blue;
  const order = topoSort(nodes, edges);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const maxX = positioned.length > 0
    ? Math.max(...positioned.map((n) => n.x + NODE_W)) + PAD
    : NODE_W + PAD * 2;
  const maxY = positioned.length > 0
    ? Math.max(...positioned.map((n) => n.y + NODE_H)) + PAD
    : NODE_H + PAD * 2;

  // Build step sequence: for each node in order, we activate it then mark done
  // Between consecutive nodes connected by an edge, we also animate the edge
  const buildInitialState = useCallback((): StepState => ({
    nodeStatuses: Object.fromEntries(nodes.map((n) => [n.id, "idle" as StepStatus])),
    activeEdge: null,
    currentStep: -1,
    totalSteps: order.length,
    playing: false,
  }), [nodes, order.length]);

  const [state, setState] = useState<StepState>(buildInitialState);

  // Reset when graph changes
  useEffect(() => {
    setState(buildInitialState());
  }, [buildInitialState]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const advanceStep = useCallback((prev: StepState): StepState => {
    const next = prev.currentStep + 1;
    if (next >= order.length) {
      // All done
      return { ...prev, activeEdge: null, playing: false };
    }

    const nodeId = order[next];
    const newStatuses = { ...prev.nodeStatuses };

    // Mark previous node as done
    if (prev.currentStep >= 0) {
      newStatuses[order[prev.currentStep]] = "done";
    }
    // Mark current node as running
    newStatuses[nodeId] = "running";

    // Find edge from previous to current
    const prevId = prev.currentStep >= 0 ? order[prev.currentStep] : null;
    const activeEdge = prevId
      ? edges.find((e) => e.from === prevId && e.to === nodeId) ?? null
      : null;

    return {
      ...prev,
      nodeStatuses: newStatuses,
      activeEdge,
      currentStep: next,
    };
  }, [order, edges]);

  const play = useCallback(() => {
    setState((prev) => {
      // Reset if already finished
      const start = prev.currentStep >= order.length - 1
        ? { ...buildInitialState(), playing: true }
        : { ...prev, playing: true };
      return start;
    });
  }, [order.length, buildInitialState]);

  // Auto-advance when playing
  useEffect(() => {
    if (!state.playing) return;

    timerRef.current = setTimeout(() => {
      setState((prev) => {
        const next = advanceStep(prev);
        // If we just processed the last node, mark it done and stop
        if (next.currentStep >= order.length - 1 && next.playing) {
          const finalStatuses = { ...next.nodeStatuses };
          finalStatuses[order[next.currentStep]] = "done";
          return { ...next, nodeStatuses: finalStatuses, activeEdge: null, playing: false };
        }
        return next;
      });
    }, speed);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [state.playing, state.currentStep, speed, advanceStep, order]);

  const pause = useCallback(() => {
    setState((prev) => ({ ...prev, playing: false }));
  }, []);

  const reset = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setState(buildInitialState());
  }, [buildInitialState]);

  const stepForward = useCallback(() => {
    setState((prev) => {
      if (prev.currentStep >= order.length - 1) {
        // Mark last as done
        const finalStatuses = { ...prev.nodeStatuses };
        if (prev.currentStep >= 0) finalStatuses[order[prev.currentStep]] = "done";
        return { ...prev, nodeStatuses: finalStatuses, activeEdge: null };
      }
      return { ...advanceStep(prev), playing: false };
    });
  }, [advanceStep, order]);

  // ── Resolve effective statuses (live mode overrides internal state) ──
  const effectiveStatuses: Record<string, StepStatus> = isLive ? liveStatuses : state.nodeStatuses;

  // Derive active edge for live mode: find an edge where `from` is done and `to` is running
  const effectiveEdge: { from: string; to: string } | null = isLive
    ? edges.find((e) => effectiveStatuses[e.from] === "done" && effectiveStatuses[e.to] === "running") ?? null
    : state.activeEdge;

  const doneCount = Object.values(effectiveStatuses).filter((s) => s === "done").length;
  const errorCount = Object.values(effectiveStatuses).filter((s) => s === "error").length;
  const runningCount = Object.values(effectiveStatuses).filter((s) => s === "running").length;
  const allDone = doneCount === nodes.length;

  if (nodes.length === 0) {
    return (
      <div className="surface-panel rounded-xl border-dashed p-6 text-sm text-[var(--muted)]">
        No graph nodes available for this agent flow.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Controls — hidden in live mode */}
      {!isLive && (
        <div className="flex items-center gap-2">
          {!state.playing ? (
            <button
              onClick={play}
              className="button-base button-primary button-sm"
            >
              <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4.5 2.5a.5.5 0 01.8-.4l8 5.5a.5.5 0 010 .8l-8 5.5a.5.5 0 01-.8-.4v-11z" />
              </svg>
              {allDone ? "Replay" : "Play"}
            </button>
          ) : (
            <button
              onClick={pause}
              className="button-base button-primary button-sm"
            >
              <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                <rect x="3" y="2" width="4" height="12" rx="0.5" />
                <rect x="9" y="2" width="4" height="12" rx="0.5" />
              </svg>
              Pause
            </button>
          )}
          <button
            onClick={stepForward}
            disabled={state.playing || allDone}
            className="button-base button-secondary button-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3.5 2.5a.5.5 0 01.8-.4l6 4.5a.5.5 0 010 .8l-6 4.5a.5.5 0 01-.8-.4v-9zM12 3v10" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            Step
          </button>
          <button
            onClick={reset}
            disabled={state.currentStep < 0 && !state.playing}
            className="button-base button-secondary button-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            Reset
          </button>
          <span className="ml-auto text-xs tabular-nums text-[var(--muted)]">
            {Math.max(0, state.currentStep + 1)} / {state.totalSteps}
          </span>
        </div>
      )}

      {/* Live mode status bar */}
      {isLive && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]">
          <span className="tabular-nums">{doneCount} / {nodes.length} steps</span>
          {runningCount > 0 && (
            <span className="inline-flex items-center gap-1 text-[var(--running-text)]">
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
              Running
            </span>
          )}
          {doneCount === nodes.length && (
            <span className="inline-flex items-center gap-1 text-[var(--done-text)]">
              <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor"><path d="M12.2 4.5a.75.75 0 010 1.06l-5.5 5.5a.75.75 0 01-1.06 0l-2.5-2.5a.75.75 0 111.06-1.06L6.2 9.44l4.97-4.97a.75.75 0 011.06 0z" /></svg>
              Complete
            </span>
          )}
          {errorCount > 0 && (
            <span className="inline-flex items-center gap-1 text-[var(--danger-text)]">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--danger-text)]" />
              Failed
            </span>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[10px] font-medium text-[var(--muted)]">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm border" style={{ borderColor: palette.idle.stroke, background: palette.idle.fill }} />
          Idle
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm border" style={{ borderColor: palette.running.stroke, background: palette.running.fill }} />
          Running
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm border" style={{ borderColor: palette.done.stroke, background: palette.done.fill }} />
          Done
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm border" style={{ borderColor: palette.error.stroke, background: palette.error.fill }} />
          Failed
        </span>
      </div>

      {/* SVG diagram */}
      <div className="surface-panel-strong overflow-x-auto rounded-xl px-3 py-4 sm:px-4">
        <svg
          viewBox={`0 0 ${maxX} ${maxY}`}
          className="mx-auto block h-auto"
          style={{ width: maxX, minWidth: maxX, minHeight: maxY, maxWidth: "none" }}
        >
          <defs>
            <marker id="ag-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill={palette.edgeDefault} />
            </marker>
            <marker id="ag-arrow-active" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill={palette.edgeActive} />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((e) => {
            const from = posMap[e.from];
            const to = posMap[e.to];
            if (!from || !to) return null;
            const tc = nodeCenter(to);
            const fc = nodeCenter(from);
            const p1 = edgeAnchor(from, tc);
            const p2 = edgeAnchor(to, fc);
            const isActive = effectiveEdge?.from === e.from && effectiveEdge?.to === e.to;
            const mx = (p1.x + p2.x) / 2;
            const my = (p1.y + p2.y) / 2;

            return (
              <g key={`${e.from}-${e.to}`}>
                <line
                  x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                  stroke={isActive ? palette.edgeActive : palette.edgeDefault}
                  strokeWidth={isActive ? 2.5 : 1.5}
                  strokeDasharray={isActive ? "6 3" : "none"}
                  markerEnd={isActive ? "url(#ag-arrow-active)" : "url(#ag-arrow)"}
                  style={{ transition: "stroke 0.3s, stroke-width 0.3s" }}
                >
                  {isActive && (
                    <animate attributeName="stroke-dashoffset" from="18" to="0" dur="0.6s" repeatCount="indefinite" />
                  )}
                </line>
                {isActive && (
                  <circle r="5" fill={palette.edgeActive} opacity="0.9">
                    <animateMotion
                      dur="0.8s"
                      repeatCount="indefinite"
                      path={`M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`}
                    />
                    <animate attributeName="r" values="4.5;5.5;4.5" dur="0.8s" repeatCount="indefinite" />
                  </circle>
                )}
                {e.label && (
                  <text x={mx} y={my - 7} textAnchor="middle" className="text-[10px]" fill={isActive ? palette.edgeActive : "var(--viz-edge-muted)"} style={{ transition: "fill 0.3s" }}>
                    {e.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {positioned.map((n) => {
            const st = effectiveStatuses[n.id] ?? "idle";
            const colors = palette[st];

            return (
              <g key={n.id}>
                {/* Pulse ring for running node */}
                {st === "running" && (
                  <rect
                    x={n.x - 4} y={n.y - 4}
                    width={NODE_W + 8} height={NODE_H + 8}
                    rx={14}
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth="1.5"
                    opacity="0.4"
                  >
                    <animate attributeName="opacity" values="0.4;0.1;0.4" dur="1.2s" repeatCount="indefinite" />
                    <animate attributeName="stroke-width" values="1.5;3;1.5" dur="1.2s" repeatCount="indefinite" />
                  </rect>
                )}

                {/* Box */}
                <rect
                  x={n.x} y={n.y}
                  width={NODE_W} height={NODE_H}
                  rx={10}
                  fill={colors.fill}
                  stroke={colors.stroke}
                  strokeWidth={st === "running" || st === "error" ? 2.5 : st === "done" ? 2 : 1.2}
                  style={{ transition: "fill 0.3s, stroke 0.3s, stroke-width 0.3s" }}
                />

                {/* Label */}
                <text
                  x={n.x + 16} y={n.y + 19}
                  dominantBaseline="central"
                  className="text-[12px] font-medium"
                  fill={colors.text}
                  style={{ transition: "fill 0.3s" }}
                >
                  {n.label}
                </text>

                <text
                  x={n.x + 16}
                  y={n.y + 34}
                  className="text-[9px] font-semibold uppercase tracking-[0.18em]"
                  fill={colors.stroke}
                  style={{ transition: "fill 0.3s" }}
                >
                  {statusLabel(st)}
                </text>

                {/* Status icon */}
                <g
                  transform={`translate(${n.x + NODE_W - 18}, ${n.y + NODE_H / 2})`}
                  color={colors.stroke}
                  style={{ transition: "color 0.3s" }}
                >
                  <StatusIcon status={st} />
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
