"use client";

import { useState, type RefObject } from "react";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import type { ProjectDetail } from "@/data/projects";
import { splitErrorDetail } from "@/lib/api";
import {
  assistantCardTone,
  assistantStateTitle,
  categoryBadgeTone,
  type RunStatus,
  type WorkspaceState,
} from "./playground-utils";
import { ThinkingStateList, WorkspaceStateBadge } from "./playground-widgets";

interface PlaygroundConversationPanelProps {
  confidence: number | null;
  conversationStarted: boolean;
  errorMsg: string | null;
  inputPreview: string;
  keyMetrics: Array<{ label: string; value: string }>;
  latency: number | null;
  output: string | null;
  selected: ProjectDetail;
  status: RunStatus;
  streamChunks: number;
  streamMode: boolean;
  streamPanelRef: RefObject<HTMLDivElement | null>;
  streamText: string;
  textOutput: string | null;
  usedSessionContext: boolean;
  workspaceState: WorkspaceState;
}

function ErrorDisplay({ errorMsg, streamText }: { errorMsg: string; streamText?: string }) {
  const [showDetail, setShowDetail] = useState(false);
  const { friendly, detail } = splitErrorDetail(errorMsg);
  return (
    <>
      <p className="mt-3 text-sm leading-7 text-[var(--danger-text)]">{friendly}</p>
      {detail && (
        <button
          type="button"
          onClick={() => setShowDetail((v) => !v)}
          className="mt-1 text-xs text-[var(--muted)] underline hover:text-[var(--foreground)]"
        >
          {showDetail ? "Hide details" : "Show details"}
        </button>
      )}
      {showDetail && detail && (
        <pre className="mt-2 max-h-[160px] overflow-auto rounded-[1rem] bg-[var(--danger-surface,var(--surface-soft))] p-3 font-mono text-xs leading-6 text-[var(--danger-text-soft,var(--muted))]">
          {detail}
        </pre>
      )}
      {streamText && (
        <pre className="mt-4 max-h-[240px] overflow-auto rounded-[1.25rem] bg-[var(--danger-surface)] p-4 font-mono text-xs leading-6 text-[var(--danger-text-soft)] transition-all duration-300 ease-in-out">{streamText}</pre>
      )}
    </>
  );
}

export function PlaygroundConversationPanel({
  confidence,
  conversationStarted,
  errorMsg,
  inputPreview,
  keyMetrics,
  latency,
  output,
  selected,
  status,
  streamChunks,
  streamMode,
  streamPanelRef,
  streamText,
  textOutput,
  usedSessionContext,
  workspaceState,
}: PlaygroundConversationPanelProps) {
  const graphNodes = selected.graph.nodes;
  const showAgentBreakdown = selected.category === "LangGraph" || selected.category === "CrewAI";

  return (
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

          {!conversationStarted && (
            <div className="rounded-[1.75rem] border border-dashed border-[var(--line)] bg-[var(--panel)]/70 px-6 py-12 text-center transition-all duration-300 ease-in-out">
              <p className="text-sm font-semibold text-[var(--foreground)]">Output will stream here.</p>
              <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                Edit the request body on the left, then press Send request.
              </p>
            </div>
          )}

          {conversationStarted && (
            <>
              <div className="flex justify-end">
                <div className="max-w-2xl rounded-[1.5rem] bg-[var(--foreground)] px-5 py-4 text-[var(--bg)] shadow-sm transition-all duration-300 ease-in-out">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color-mix(in_srgb,var(--bg)_64%,transparent)]">You</p>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-7">{inputPreview}</p>
                  <p className="mt-3 text-[11px] font-medium text-[color-mix(in_srgb,var(--bg)_64%,transparent)]">
                    JSON request prepared for {selected.name}
                  </p>
                </div>
              </div>

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

                  {workspaceState === "streaming" && (
                    <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-[var(--foreground)] transition-opacity duration-300 ease-in-out">
                      {streamText}
                      <span className="ml-1 inline-block h-[1.1em] w-[2px] bg-[var(--accent-solid)] align-text-bottom" style={{ animation: "blink 530ms steps(2, start) infinite" }} />
                    </div>
                  )}

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

                  {workspaceState === "error" && errorMsg && (
                    <ErrorDisplay errorMsg={errorMsg} streamText={streamText} />
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}