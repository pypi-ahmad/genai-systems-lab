"use client";

import { useId } from "react";

export const agentGraphSteps = ["planner", "executor", "evaluator", "final"] as const;

export type AgentGraphStep = (typeof agentGraphSteps)[number];

interface AgentGraphProps {
  activeStep?: AgentGraphStep | null;
  completedSteps?: AgentGraphStep[];
  className?: string;
}

type VisualState = "idle" | "active" | "completed";
type EdgeVisualState = "idle" | "active" | "completed";

const STEP_LABELS: Record<AgentGraphStep, string> = {
  planner: "Planner",
  executor: "Executor",
  evaluator: "Evaluator",
  final: "Final",
};

const NODE_W = 136;
const NODE_H = 60;
const START_X = 36;
const START_Y = 56;
const GAP_X = 44;
const VIEWBOX_W = START_X * 2 + NODE_W * agentGraphSteps.length + GAP_X * (agentGraphSteps.length - 1);
const VIEWBOX_H = 172;

const NODE_POSITIONS: Record<AgentGraphStep, { x: number; y: number }> = {
  planner: { x: START_X + (NODE_W + GAP_X) * 0, y: START_Y },
  executor: { x: START_X + (NODE_W + GAP_X) * 1, y: START_Y },
  evaluator: { x: START_X + (NODE_W + GAP_X) * 2, y: START_Y },
  final: { x: START_X + (NODE_W + GAP_X) * 3, y: START_Y },
};

const EDGES: Array<{ from: AgentGraphStep; to: AgentGraphStep }> = [
  { from: "planner", to: "executor" },
  { from: "executor", to: "evaluator" },
  { from: "evaluator", to: "final" },
];

const NODE_STYLES: Record<VisualState, { fill: string; stroke: string; text: string; badgeFill: string; badgeText: string }> = {
  idle: {
    fill: "var(--panel-strong)",
    stroke: "var(--line)",
    text: "var(--muted)",
    badgeFill: "var(--surface-soft)",
    badgeText: "var(--muted)",
  },
  active: {
    fill: "var(--accent-soft-strong)",
    stroke: "var(--accent-solid)",
    text: "var(--accent-solid)",
    badgeFill: "var(--accent-solid)",
    badgeText: "var(--accent-contrast)",
  },
  completed: {
    fill: "var(--done-bg)",
    stroke: "var(--done-border)",
    text: "var(--done-text)",
    badgeFill: "color-mix(in srgb, var(--done-text) 14%, transparent)",
    badgeText: "var(--done-text)",
  },
};

const EDGE_STYLES: Record<EdgeVisualState, { stroke: string; marker: "idle" | "active" | "completed" }> = {
  idle: {
    stroke: "var(--viz-edge-default)",
    marker: "idle",
  },
  active: {
    stroke: "var(--accent-solid)",
    marker: "active",
  },
  completed: {
    stroke: "var(--done-text)",
    marker: "completed",
  },
};

function getNodeVisualState(
  step: AgentGraphStep,
  activeStep: AgentGraphStep | null,
  completedSteps: Set<AgentGraphStep>,
): VisualState {
  if (step === activeStep) {
    return "active";
  }

  if (completedSteps.has(step)) {
    return "completed";
  }

  return "idle";
}

function getEdgeVisualState(
  from: AgentGraphStep,
  to: AgentGraphStep,
  activeStep: AgentGraphStep | null,
  completedSteps: Set<AgentGraphStep>,
): EdgeVisualState {
  if (activeStep === to && completedSteps.has(from)) {
    return "active";
  }

  if (completedSteps.has(from) && completedSteps.has(to)) {
    return "completed";
  }

  return "idle";
}

export default function AgentGraph({
  activeStep = null,
  completedSteps = [],
  className = "",
}: AgentGraphProps) {
  const markerId = useId().replace(/:/g, "");
  const completedSet = new Set(completedSteps);

  return (
    <div className={`surface-panel-strong rounded-[1.25rem] p-4 sm:p-5 ${className}`.trim()}>
      <svg
        viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
        className="block h-auto w-full"
        role="img"
        aria-label="Agent workflow graph showing planner, executor, evaluator, and final steps"
      >
        <defs>
          <marker
            id={`${markerId}-arrow-idle`}
            markerWidth="10"
            markerHeight="8"
            refX="8"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 10 4, 0 8" fill="var(--viz-edge-default)" />
          </marker>
          <marker
            id={`${markerId}-arrow-active`}
            markerWidth="10"
            markerHeight="8"
            refX="8"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 10 4, 0 8" fill="var(--accent-solid)" />
          </marker>
          <marker
            id={`${markerId}-arrow-completed`}
            markerWidth="10"
            markerHeight="8"
            refX="8"
            refY="4"
            orient="auto"
          >
            <polygon points="0 0, 10 4, 0 8" fill="var(--done-text)" />
          </marker>
        </defs>

        {EDGES.map((edge) => {
          const from = NODE_POSITIONS[edge.from];
          const to = NODE_POSITIONS[edge.to];
          const state = getEdgeVisualState(edge.from, edge.to, activeStep, completedSet);
          const style = EDGE_STYLES[state];
          const y = from.y + NODE_H / 2;
          const startX = from.x + NODE_W;
          const endX = to.x;

          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={startX}
              y1={y}
              x2={endX}
              y2={y}
              stroke={style.stroke}
              strokeWidth={state === "active" ? 2.5 : 2}
              strokeDasharray={state === "active" ? "8 6" : undefined}
              markerEnd={`url(#${markerId}-arrow-${style.marker})`}
              className="transition-all duration-200 ease-in-out"
            >
              {state === "active" ? (
                <animate
                  attributeName="stroke-dashoffset"
                  from="28"
                  to="0"
                  dur="0.9s"
                  repeatCount="indefinite"
                />
              ) : null}
            </line>
          );
        })}

        {agentGraphSteps.map((step, index) => {
          const { x, y } = NODE_POSITIONS[step];
          const state = getNodeVisualState(step, activeStep, completedSet);
          const colors = NODE_STYLES[state];
          const isActive = state === "active";
          const isCompleted = state === "completed";

          return (
            <g
              key={step}
              className={`origin-center transition-transform duration-200 ease-in-out ${isActive ? "scale-110" : "scale-100"}`}
              style={{ transformBox: "fill-box" }}
            >
              {isActive ? (
                <rect
                  x={x - 8}
                  y={y - 8}
                  width={NODE_W + 16}
                  height={NODE_H + 16}
                  rx={18}
                  fill="var(--accent-soft)"
                  opacity="0.85"
                >
                  <animate attributeName="opacity" values="0.55;0.9;0.55" dur="1.3s" repeatCount="indefinite" />
                </rect>
              ) : null}

              <rect
                x={x}
                y={y}
                width={NODE_W}
                height={NODE_H}
                rx={16}
                fill={colors.fill}
                stroke={colors.stroke}
                strokeWidth={isActive ? 2.5 : isCompleted ? 2 : 1.4}
                className="transition-all duration-200 ease-in-out"
              />

              <rect
                x={x + 12}
                y={y + 12}
                width={26}
                height={18}
                rx={9}
                fill={colors.badgeFill}
                className="transition-all duration-200 ease-in-out"
              />
              <text
                x={x + 25}
                y={y + 25}
                textAnchor="middle"
                className="text-[10px] font-semibold uppercase tracking-[0.18em]"
                fill={colors.badgeText}
              >
                {index + 1}
              </text>

              <text
                x={x + NODE_W / 2}
                y={y + 35}
                textAnchor="middle"
                className="text-[13px] font-semibold"
                fill={colors.text}
              >
                {STEP_LABELS[step]}
              </text>

              <g transform={`translate(${x + NODE_W - 24}, ${y + 18})`}>
                {isCompleted ? (
                  <path
                    d="M0 5.5L4 9.5L12 1.5"
                    fill="none"
                    stroke={colors.text}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ) : (
                  <circle
                    cx="6"
                    cy="6"
                    r={isActive ? "4.5" : "3"}
                    fill={colors.text}
                    opacity={isActive ? "1" : "0.45"}
                    className="transition-all duration-200 ease-in-out"
                  />
                )}
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
}