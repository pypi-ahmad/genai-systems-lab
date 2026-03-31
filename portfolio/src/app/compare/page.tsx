import type { Metadata } from "next";
import Link from "next/link";
import { projects } from "@/data/projects";

export const metadata: Metadata = {
  title: "LangGraph vs CrewAI — Portfolio",
  description:
    "Technical comparison of LangGraph and CrewAI multi-agent frameworks.",
};

const overviewCards = [
  {
    name: "LangGraph",
    tag: "Stateful orchestration",
    description:
      "LangGraph is a graph-based orchestration framework for long-running agent systems with explicit state, conditional routing, retries, checkpoints, and controlled execution boundaries.",
  },
  {
    name: "CrewAI",
    tag: "Role-based collaboration",
    description:
      "CrewAI is a multi-agent collaboration framework centered on agents, tasks, and process modes. It is designed to model specialist roles, staged handoffs, and prompt-driven coordination.",
  },
] as const;

const comparisonRows = [
  {
    feature: "control flow",
    langgraph:
      "Graph topology is explicit in code. Nodes, edges, and branch conditions are developer-owned, so retries, exits, and loops stay inspectable.",
    crewai:
      "Control flow is mostly expressed through task order and process mode. The framework manages agent execution and collaboration semantics.",
  },
  {
    feature: "determinism",
    langgraph:
      "Higher determinism at the orchestration layer. You can combine LLM nodes with deterministic validators, executors, and recovery paths in the same graph.",
    crewai:
      "Lower determinism at the orchestration layer. Outputs and intermediate decisions are more prompt-shaped, even when task ordering is fixed.",
  },
  {
    feature: "flexibility",
    langgraph:
      "Better for branching, loops, stateful recovery, human approval steps, and workflows where execution policy needs custom code.",
    crewai:
      "Better for quickly composing multiple agent personas into a coherent workflow without writing detailed routing logic.",
  },
  {
    feature: "use cases",
    langgraph:
      "Agents that need explicit state machines, streaming status, checkpointing, validation gates, or data-dependent routing.",
    crewai:
      "Analyst, editorial, research, and planning teams where collaborative reasoning and role separation matter more than graph control.",
  },
] as const;

const repoExamples = {
  langgraph: [
    {
      slug: "lg-debugging-agent",
      pattern: "Evaluator-driven retry loop",
      detail:
        "A downstream evaluator decides whether execution ends or routes back into the fixer path, which is a graph-native control mechanism.",
    },
    {
      slug: "lg-data-agent",
      pattern: "State-based backend routing",
      detail:
        "Structured state determines whether the run continues through the pandas or DuckDB execution branch.",
    },
    {
      slug: "lg-workflow-agent",
      pattern: "Checkpoint and resume",
      detail:
        "Progress is governed by explicit workflow state, which makes recovery deterministic instead of purely prompt-dependent.",
    },
  ],
  crewai: [
    {
      slug: "crew-content-pipeline",
      pattern: "Specialist handoff chain",
      detail:
        "Research, writing, editing, and SEO are modeled as agent roles with clean task-to-task context transfer.",
    },
    {
      slug: "crew-hiring-system",
      pattern: "Composable crew review",
      detail:
        "Candidate evaluation and final comparison are split into separate collaborative crews instead of one explicit execution graph.",
    },
    {
      slug: "crew-startup-simulator",
      pattern: "Cross-functional perspective synthesis",
      detail:
        "Multiple business roles contribute outputs that are stronger as agent personas than as graph nodes with rigid transitions.",
    },
  ],
} as const;

const projectMap = new Map(projects.map((project) => [project.slug, project]));

function ExampleColumn({
  title,
  tone,
  items,
}: {
  title: string;
  tone: "accent" | "neutral";
  items: readonly {
    slug: string;
    pattern: string;
    detail: string;
  }[];
}) {
  const toneClasses =
    tone === "accent"
      ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft)]"
      : "surface-panel";

  return (
    <div className="space-y-4">
      <div className="section-heading">
        <p className="eyebrow">{title}</p>
        <h3 className="heading-section text-3xl">
          Representative implementations.
        </h3>
      </div>
      <div className="space-y-4">
        {items.map((item) => {
          const project = projectMap.get(item.slug);
          if (!project) {
            return null;
          }

          return (
            <Link
              key={item.slug}
              href={`/projects/${item.slug}`}
              className={`surface-card surface-card-hover block rounded-xl border p-6 sm:p-8 ${toneClasses}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="heading-card text-lg">
                    {project.name}
                  </p>
                  <p className="mt-2 text-sm font-medium text-[var(--foreground)]">
                    {item.pattern}
                  </p>
                </div>
                <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  {project.category}
                </span>
              </div>
              <p className="copy-body mt-3 text-sm">
                {item.detail}
              </p>
              <p className="copy-body mt-4 text-sm">
                {project.description}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <div className="space-y-0">
      <section className="grid gap-8 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div className="title-stack">
          <p className="eyebrow">Framework Comparison</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            LangGraph vs CrewAI
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            Both frameworks support agentic systems, but they optimize for
            different layers of the stack. LangGraph is strongest when the
            workflow itself needs to be modeled precisely. CrewAI is strongest
            when the system is better expressed as collaborating roles with
            structured handoffs.
          </p>
        </div>
        <div className="surface-card rounded-xl p-6 sm:p-8">
          <p className="eyebrow">Decision Lens</p>
          <div className="mt-5 grid gap-6">
            {[
              "Choose LangGraph for explicit routing and stateful execution.",
              "Choose CrewAI for role-based collaboration and faster multi-agent assembly.",
              "Use repo examples below as implementation references, not abstractions.",
            ].map((item, index) => (
              <div
                key={item}
                className="surface-panel flex items-center gap-3 rounded-[1.25rem] px-4 py-4 text-sm leading-7"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--foreground)] text-[10px] font-bold text-[var(--bg)]">
                  {index + 1}
                </span>
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">1. Overview</p>
          <h2 className="heading-section text-3xl">
            Two different orchestration models.
          </h2>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          {overviewCards.map((card, index) => (
            <div
              key={card.name}
              className="surface-card rounded-xl p-6 sm:p-8"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent-solid)]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="heading-card text-lg">
                    {card.name}
                  </p>
                  <p className="text-sm text-[var(--muted)]">{card.tag}</p>
                </div>
              </div>
              <p className="copy-body mt-4 text-sm">
                {card.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">2. Comparison Table</p>
          <h2 className="heading-section text-3xl">
            Core trade-offs at the orchestration layer.
          </h2>
        </div>
        <div className="surface-card overflow-x-auto rounded-xl">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--line)] bg-[var(--surface-soft)]">
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Feature
                </th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  LangGraph
                </th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  CrewAI
                </th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row) => (
                <tr
                  key={row.feature}
                  className="border-b border-[var(--line)] last:border-b-0"
                >
                  <td className="px-6 py-5 align-top text-sm font-semibold capitalize text-[var(--foreground)]">
                    {row.feature}
                  </td>
                  <td className="px-6 py-5 align-top text-sm leading-7 text-[var(--muted)]">
                    {row.langgraph}
                  </td>
                  <td className="px-6 py-5 align-top text-sm leading-7 text-[var(--muted)]">
                    {row.crewai}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">3. Examples From This Repo</p>
          <h2 className="heading-section text-3xl">
            Concrete implementations, not toy examples.
          </h2>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <ExampleColumn
            title="LangGraph"
            tone="accent"
            items={repoExamples.langgraph}
          />
          <ExampleColumn
            title="CrewAI"
            tone="neutral"
            items={repoExamples.crewai}
          />
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">4. When To Use Which</p>
          <h2 className="heading-section text-3xl">
            Pick based on where complexity lives.
          </h2>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="surface-card rounded-xl p-6 sm:p-8">
            <p className="heading-card text-lg">
              Use LangGraph when the workflow is the hard part.
            </p>
            <div className="copy-stack copy-body mt-4 text-sm">
              <p>
                Reach for LangGraph when execution order, branch conditions,
                retries, persistence, or validation gates need to be designed as
                first-class code constructs.
              </p>
              <p>
                It is the better fit for systems that mix deterministic runtime
                logic with LLM reasoning, especially when you need observability
                into every transition or recovery path.
              </p>
            </div>
          </div>
          <div className="surface-card rounded-xl p-6 sm:p-8">
            <p className="heading-card text-lg">
              Use CrewAI when the collaboration model is the hard part.
            </p>
            <div className="copy-stack copy-body mt-4 text-sm">
              <p>
                Reach for CrewAI when you want multiple specialized agents to
                contribute perspectives, reviews, or staged outputs without
                spending much time encoding low-level routing mechanics.
              </p>
              <p>
                It is the better fit for analyst teams, editorial flows,
                planning groups, and other systems where agent identity and
                handoff semantics carry more value than explicit graph control.
              </p>
            </div>
          </div>
        </div>

        <div className="surface-card rounded-xl p-6 sm:p-8">
          <p className="eyebrow">Practical Rule</p>
          <p className="copy-lead mt-3 max-w-2xl text-base sm:text-lg">
            If you need to prove why the system took a specific path, recover a
            run from structured state, or enforce deterministic gates around LLM
            calls, prefer LangGraph. If you need domain-specialized agents to
            collaborate quickly on a shared deliverable with minimal orchestration
            code, prefer CrewAI.
          </p>
        </div>
      </section>
    </div>
  );
}
