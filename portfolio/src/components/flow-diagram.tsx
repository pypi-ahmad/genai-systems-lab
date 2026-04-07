"use client";

import { useState } from "react";
import type { GraphNode, GraphEdge } from "@/data/projects";

/* ── Layout ───────────────────────────────────────────── */

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

const NODE_W = 140;
const NODE_H = 44;
const GAP_X = 60;
const GAP_Y = 80;
const PAD = 24;

/**
 * Auto-layout: arrange nodes in rows. Walk edges to determine topo
 * order, then wrap into rows so the diagram stays compact.
 */
function layout(nodes: GraphNode[], edges: GraphEdge[]): PositionedNode[] {
  // Build adjacency for topological sort
  const inDeg: Record<string, number> = {};
  const adj: Record<string, string[]> = {};
  for (const n of nodes) {
    inDeg[n.id] = 0;
    adj[n.id] = [];
  }
  for (const e of edges) {
    // Skip back-edges (cycles) for layout purposes
    if (adj[e.to]?.some(() => false)) continue;
    adj[e.from]?.push(e.to);
    if (inDeg[e.to] !== undefined) inDeg[e.to]++;
  }

  // Kahn's algorithm
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
  // Append any nodes not reached (part of cycles)
  for (const n of nodes) {
    if (!visited.has(n.id)) order.push(n.id);
  }

  // Decide columns per row — max 4 per row keeps it readable
  const maxPerRow = Math.min(4, nodes.length);
  const positioned: PositionedNode[] = [];
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  for (let i = 0; i < order.length; i++) {
    const col = i % maxPerRow;
    const row = Math.floor(i / maxPerRow);
    positioned.push({
      ...nodeMap[order[i]],
      x: PAD + col * (NODE_W + GAP_X),
      y: PAD + row * (NODE_H + GAP_Y),
    });
  }
  return positioned;
}

/* ── Geometry helpers ─────────────────────────────────── */

function center(n: PositionedNode) {
  return { cx: n.x + NODE_W / 2, cy: n.y + NODE_H / 2 };
}

function edgeAnchor(
  node: PositionedNode,
  target: { cx: number; cy: number },
) {
  const { cx, cy } = center(node);
  const dx = target.cx - cx;
  const dy = target.cy - cy;
  const hw = NODE_W / 2;
  const hh = NODE_H / 2;
  const sx = hw / Math.abs(dx || 1);
  const sy = hh / Math.abs(dy || 1);
  const s = Math.min(sx, sy);
  return { x: cx + dx * s, y: cy + dy * s };
}

/* ── Component ────────────────────────────────────────── */

interface FlowDiagramProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  accentColor?: string; // tailwind color name, default "blue"
}

const COLORS: Record<string, { stroke: string; fill: string; text: string; activeFill: string }> = {
  blue:    { stroke: "var(--viz-running-blue-stroke)", fill: "var(--viz-running-blue-fill)", text: "var(--viz-running-blue-text)", activeFill: "var(--viz-running-blue-fill)" },
  emerald: { stroke: "var(--viz-running-emerald-stroke)", fill: "var(--viz-running-emerald-fill)", text: "var(--viz-running-emerald-text)", activeFill: "var(--viz-running-emerald-fill)" },
  violet:  { stroke: "var(--viz-running-violet-stroke)", fill: "var(--viz-running-violet-fill)", text: "var(--viz-running-violet-text)", activeFill: "var(--viz-running-violet-fill)" },
};

export default function FlowDiagram({
  nodes,
  edges,
  accentColor = "blue",
}: FlowDiagramProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

  const positioned = layout(nodes, edges);
  const posMap = Object.fromEntries(positioned.map((n) => [n.id, n]));
  const palette = COLORS[accentColor] ?? COLORS.blue;

  // Compute viewBox from laid-out nodes
  const maxX = Math.max(...positioned.map((n) => n.x + NODE_W)) + PAD;
  const maxY = Math.max(...positioned.map((n) => n.y + NODE_H)) + PAD;

  // connected set for highlight
  const connected = new Set<string>();
  if (hoveredId) {
    connected.add(hoveredId);
    for (const e of edges) {
      if (e.from === hoveredId) connected.add(e.to);
      if (e.to === hoveredId) connected.add(e.from);
    }
  }

  return (
    <div className="surface-panel-strong overflow-auto rounded-xl">
      <div className="flex items-center justify-end gap-1 px-3 pt-2">
        <button type="button" onClick={() => setZoom((z) => Math.min(3, z + 0.25))} className="button-base button-ghost button-sm px-2" aria-label="Zoom in">+</button>
        <button type="button" onClick={() => setZoom(1)} className="button-base button-ghost button-sm px-2 text-[11px]">{Math.round(zoom * 100)}%</button>
        <button type="button" onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))} className="button-base button-ghost button-sm px-2" aria-label="Zoom out">−</button>
      </div>
      <div style={{ transform: `scale(${zoom})`, transformOrigin: "top left", width: maxX * zoom, height: maxY * zoom }}>
      <svg
        viewBox={`0 0 ${maxX} ${maxY}`}
        className="mx-auto block w-full"
        style={{ maxWidth: maxX, minHeight: maxY }}
      >
        <defs>
          <marker
            id="flow-arrow"
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon
              points="0 0, 8 3, 0 6"
              fill={palette.stroke}
              opacity={0.5}
            />
          </marker>
          <marker
            id="flow-arrow-active"
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill={palette.stroke} />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((e) => {
          const from = posMap[e.from];
          const to = posMap[e.to];
          if (!from || !to) return null;
          const fc = center(from);
          const tc = center(to);
          const p1 = edgeAnchor(from, tc);
          const p2 = edgeAnchor(to, fc);
          const active =
            hoveredId && connected.has(e.from) && connected.has(e.to);
          const mx = (p1.x + p2.x) / 2;
          const my = (p1.y + p2.y) / 2;

          return (
            <g key={`${e.from}-${e.to}`}>
              <line
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={active ? palette.stroke : "var(--viz-edge-default)"}
                strokeWidth={active ? 2 : 1.5}
                markerEnd={
                  active ? "url(#flow-arrow-active)" : "url(#flow-arrow)"
                }
                className="transition-all duration-150"
              />
              {e.label && (
                <text
                  x={mx}
                  y={my - 7}
                  textAnchor="middle"
                  className="text-[10px] transition-colors duration-150"
                  fill={active ? palette.text : "var(--viz-edge-muted)"}
                >
                  {e.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {positioned.map((n) => {
          const active = hoveredId ? connected.has(n.id) : false;
          return (
            <g
              key={n.id}
              onMouseEnter={() => setHoveredId(n.id)}
              onMouseLeave={() => setHoveredId(null)}
              className="cursor-default"
            >
              <rect
                x={n.x}
                y={n.y}
                width={NODE_W}
                height={NODE_H}
                rx={10}
                fill={active ? palette.activeFill : palette.fill}
                stroke={active ? palette.stroke : "var(--viz-edge-default)"}
                strokeWidth={active ? 2 : 1.2}
                className="transition-all duration-150"
              />
              <text
                x={n.x + NODE_W / 2}
                y={n.y + NODE_H / 2 + 1}
                textAnchor="middle"
                dominantBaseline="central"
                className="text-[12px] font-medium transition-colors duration-150"
                fill={active ? palette.text : "var(--viz-node-muted)"}
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
      </div>
    </div>
  );
}
