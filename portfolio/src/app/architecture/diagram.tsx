"use client";

import { useState } from "react";

interface DiagramStep {
  id: string;
  title: string;
  subtitle: string;
  description: string;
}

const STEPS: DiagramStep[] = [
  {
    id: "ui",
    title: "UI",
    subtitle: "Next.js frontend",
    description:
      "The frontend renders project pages, demos, metrics, and navigation. It collects user input and sends requests to the backend over HTTP.",
  },
  {
    id: "api",
    title: "API",
    subtitle: "FastAPI gateway",
    description:
      "The shared API layer handles routing, validation, timing, logging, and standardized response envelopes before dispatching work to a selected project.",
  },
  {
    id: "project",
    title: "Project",
    subtitle: "Per-project runtime",
    description:
      "Each project owns its workflow logic, prompting strategy, and execution path. This is where a LangGraph, CrewAI, or GenAI system actually runs.",
  },
  {
    id: "shared",
    title: "Shared Layer",
    subtitle: "Schemas, logging, LLM, eval",
    description:
      "Common infrastructure supports every project: shared schemas, logging, tracing, LLM clients, metrics, and reusable utility code.",
  },
];

function stepIndex(id: string | null) {
  return STEPS.findIndex((step) => step.id === id);
}

export default function ArchitectureDiagram() {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>(STEPS[1].id);

  const activeId = hoveredId ?? selectedId;
  const activeIndex = stepIndex(activeId);
  const selectedStep = STEPS.find((step) => step.id === selectedId) ?? STEPS[1];

  return (
    <div className="space-y-8">
      <div className="surface-card rounded-xl p-6 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] lg:items-center">
          {STEPS.map((step, index) => {
            const isActive = activeId === step.id;
            const isConnected = activeIndex !== -1 && Math.abs(index - activeIndex) <= 1;

            return (
              <div key={step.id} className="contents">
                <button
                  type="button"
                  onMouseEnter={() => setHoveredId(step.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  onFocus={() => setHoveredId(step.id)}
                  onBlur={() => setHoveredId(null)}
                  onClick={() => setSelectedId(step.id)}
                  className={[
                    "rounded-[1.5rem] border p-5 text-left transition-all duration-200",
                    "bg-[var(--card-strong)] shadow-[var(--card-hover-shadow)]",
                    isActive
                      ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft-strong)]"
                      : isConnected
                        ? "border-[var(--accent-border-soft)] bg-[var(--surface-soft)]"
                        : "border-[var(--line)]",
                  ].join(" ")}
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                    {String(index + 1).padStart(2, "0")}
                  </p>
                  <p className="mt-3 text-lg font-semibold tracking-[-0.03em] text-[var(--foreground)]">
                    {step.title}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                    {step.subtitle}
                  </p>
                </button>

                {index < STEPS.length - 1 ? (
                  <div className="hidden lg:flex lg:items-center lg:justify-center">
                    <div className="flex items-center gap-2">
                      <span
                        className={[
                          "h-px w-10 transition-colors duration-200",
                          activeIndex !== -1 && index >= activeIndex - 1 && index <= activeIndex
                            ? "bg-[var(--accent-solid)]"
                            : "bg-[var(--line)]",
                        ].join(" ")}
                      />
                      <span
                        className={[
                          "text-sm transition-colors duration-200",
                          activeIndex !== -1 && index >= activeIndex - 1 && index <= activeIndex
                            ? "text-[var(--accent-solid)]"
                            : "text-[var(--muted)]",
                        ].join(" ")}
                      >
                        →
                      </span>
                      <span
                        className={[
                          "h-px w-10 transition-colors duration-200",
                          activeIndex !== -1 && index >= activeIndex - 1 && index <= activeIndex
                            ? "bg-[var(--accent-solid)]"
                            : "bg-[var(--border)]",
                        ].join(" ")}
                      />
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-col gap-3 lg:hidden">
          {STEPS.slice(0, -1).map((step, index) => {
            const connectorActive = activeIndex !== -1 && index >= activeIndex - 1 && index <= activeIndex;

            return (
              <div key={`${step.id}-mobile-arrow`} className="flex justify-center">
                <span className={connectorActive ? "text-[var(--accent-solid)]" : "text-[var(--muted)]"}>
                  ↓
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="surface-card rounded-xl p-6 sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Selected Component</p>
            <h3 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">
              {selectedStep.title}
            </h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {selectedStep.subtitle}
            </p>
          </div>
          <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Click nodes to inspect
          </span>
        </div>
        <p className="copy-body mt-5 max-w-2xl text-sm sm:text-base">
          {selectedStep.description}
        </p>
      </div>
    </div>
  );
}
