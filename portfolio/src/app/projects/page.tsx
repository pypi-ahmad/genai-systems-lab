import Link from "next/link";
import { projects, type Category } from "@/data/projects";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Projects — GenAI Systems Lab",
};

const groups: { label: string; category: Category; accent: string; dot: string }[] = [
  { label: "GenAI", category: "GenAI", accent: "bg-[var(--category-genai-bg)] text-[var(--category-genai-text)]", dot: "bg-[var(--category-genai-dot)]" },
  { label: "LangGraph", category: "LangGraph", accent: "bg-[var(--category-langgraph-bg)] text-[var(--category-langgraph-text)]", dot: "bg-[var(--category-langgraph-dot)]" },
  { label: "CrewAI", category: "CrewAI", accent: "bg-[var(--category-crewai-bg)] text-[var(--category-crewai-text)]", dot: "bg-[var(--category-crewai-dot)]" },
];

export default function ProjectsPage() {
  return (
    <div className="space-y-0">
      <section className="grid gap-8 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div className="title-stack">
          <p className="eyebrow">Projects</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Twenty AI systems organized for quick scanning.
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            Browse the full collection grouped by GenAI, LangGraph, and CrewAI.
            Each project card keeps the signal tight: name, short description,
            category, and a direct path to the detail page.
          </p>
        </div>

        <div className="surface-card rounded-xl p-6 sm:p-8">
          <div className="grid grid-cols-3 gap-6 text-center">
            {groups.map((group) => {
              const count = projects.filter((project) => project.category === group.category).length;

              return (
                <div key={group.category} className="surface-panel rounded-[1.25rem] px-3 py-5">
                  <p className="text-3xl font-semibold tracking-[-0.04em]">{count}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                    {group.label}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {groups.map((group, gi) => {
        const items = projects.filter((project) => project.category === group.category);

        return (
          <section key={group.category} className="space-y-6 py-16">
            {gi > 0 && <div className="section-divider mb-6" />}
            <div className="flex items-center gap-3">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${group.dot}`} />
              <h2 className="heading-card text-3xl">{group.label}</h2>
              <span className="surface-pill rounded-full px-3 py-1 text-xs text-[var(--muted)]">
                {items.length} projects
              </span>
            </div>

            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {items.map((project) => (
                <article key={project.slug} className="h-full">
                  <Link
                    href={`/projects/${project.slug}`}
                    className="group surface-card surface-card-hover flex h-full flex-col rounded-xl border border-[color-mix(in_srgb,var(--line)_92%,transparent)] bg-[color-mix(in_srgb,var(--card)_94%,var(--surface-soft)_6%)] p-6 sm:p-8"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${group.accent}`}
                      >
                        {group.label}
                      </span>
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[var(--line)] bg-[var(--panel)] text-sm text-[var(--muted)] transition-all duration-200 ease-in-out group-hover:border-[var(--accent-border-soft)] group-hover:bg-[var(--accent-soft)] group-hover:text-[var(--accent-solid)]">
                        ↗
                      </span>
                    </div>

                    <div className="mt-5 space-y-3">
                      <h3 className="heading-card text-xl transition-colors duration-200 ease-in-out group-hover:text-[var(--accent-solid)]">
                        {project.name}
                      </h3>
                      <p className="copy-body text-sm">
                        {project.description}
                      </p>
                    </div>

                    <div className="mt-auto flex items-center justify-between gap-4 border-t border-[color-mix(in_srgb,var(--line)_88%,transparent)] pt-6">
                      <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
                        Open project
                      </span>
                      <span className="text-sm font-medium text-[var(--muted)] transition-all duration-200 ease-in-out group-hover:translate-x-0.5 group-hover:text-[var(--accent-solid)]">
                        View details →
                      </span>
                    </div>
                  </Link>
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
