import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CopyButton } from "@/components/copy-button";
import FlowDiagram from "@/components/flow-diagram";
import { getProject, projects } from "@/data/projects";
import ProjectDemo from "./project-demo";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return projects.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);
  return { title: project ? `${project.name} — GenAI Systems Lab` : "Not Found" };
}

const categoryAccent: Record<string, string> = {
  GenAI: "bg-[var(--category-genai-bg)] text-[var(--category-genai-text)]",
  LangGraph: "bg-[var(--category-langgraph-bg)] text-[var(--category-langgraph-text)]",
  CrewAI: "bg-[var(--category-crewai-bg)] text-[var(--category-crewai-text)]",
};

const categoryDiagramAccent: Record<string, string> = {
  GenAI: "emerald",
  LangGraph: "blue",
  CrewAI: "violet",
};

function formatJson(value: string) {
  return JSON.stringify(JSON.parse(value), null, 2);
}

export default async function ProjectDetailPage({ params }: Props) {
  const { slug } = await params;
  const project = getProject(slug);

  if (!project) {
    notFound();
  }

  return (
    <article className="mx-auto max-w-6xl space-y-0">
      <section className="space-y-6 py-16">
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-[var(--muted)]">
          <Link href="/" className="hover:text-[var(--foreground)] transition-colors">Home</Link>
          <span aria-hidden>›</span>
          <Link href="/projects" className="hover:text-[var(--foreground)] transition-colors">Projects</Link>
          <span aria-hidden>›</span>
          <span className="text-[var(--foreground)] font-medium">{project.name}</span>
        </nav>

        <header className="surface-card overflow-hidden rounded-xl p-6 sm:p-8">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${categoryAccent[project.category] ?? ""}`}
                >
                  {project.category}
                </span>
                <span className="surface-pill rounded-full px-3 py-1 font-mono text-[11px] tracking-[0.16em] text-[var(--muted)] uppercase">
                  {project.slug}
                </span>
              </div>

              <div className="title-stack">
                <h1 className="heading-display max-w-2xl text-4xl sm:text-5xl">
                  {project.name}
                </h1>
                <p className="copy-lead max-w-2xl text-base sm:text-lg">
                  {project.description}
                </p>
              </div>
            </div>

            <div className="grid w-full gap-6 sm:grid-cols-3 lg:max-w-sm lg:grid-cols-1 xl:max-w-md xl:grid-cols-3">
              <div className="surface-panel rounded-[1.5rem] px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Category
                </p>
                <p className="mt-2 text-sm font-semibold text-[var(--foreground)]">{project.category}</p>
              </div>
              <div className="surface-panel rounded-[1.5rem] px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Features
                </p>
                <p className="mt-2 text-sm font-semibold text-[var(--foreground)]">{project.features.length}</p>
              </div>
              <div className="surface-panel rounded-[1.5rem] px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  API
                </p>
                <p className="mt-2 text-sm font-semibold text-[var(--foreground)]">FastAPI</p>
              </div>
            </div>
          </div>
        </header>
      </section>

      <section className="py-16">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start">
        <div className="space-y-6">
          <section className="surface-card rounded-xl p-6 sm:p-8">
            <p className="eyebrow">Architecture</p>
            <h2 className="heading-section mt-3 text-3xl text-[var(--foreground)]">
              System design and execution flow
            </h2>
            <p className="copy-body mt-5 max-w-2xl text-base">
              {project.architecture}
            </p>

            {project.graph.nodes.length > 0 && project.graph.edges.length > 0 ? (
              <div className="mt-8 space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-semibold tracking-[-0.01em] text-[var(--foreground)]">
                    Component flow
                  </p>
                  <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                    nodes = components, edges = flow
                  </p>
                </div>

                <FlowDiagram
                  nodes={project.graph.nodes}
                  edges={project.graph.edges}
                  accentColor={categoryDiagramAccent[project.category] ?? "blue"}
                />
              </div>
            ) : null}
          </section>

          <section className="surface-card rounded-xl p-6 sm:p-8">
            <p className="eyebrow">Features</p>
            <h2 className="heading-section mt-3 text-3xl text-[var(--foreground)]">
              Built for practical developer workflows
            </h2>
            <ul className="mt-6 grid gap-6 sm:grid-cols-2">
              {project.features.map((feature) => (
                <li
                  key={feature}
                  className="surface-panel rounded-[1.25rem] px-4 py-4 text-sm leading-7 text-[var(--foreground)]"
                >
                  <div className="flex items-start gap-3">
                    <span className="mt-1 inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--accent-solid)]" />
                    <span>{feature}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="surface-card rounded-xl p-6 sm:p-8">
            <p className="eyebrow">Example Input / Output</p>
            <h2 className="heading-section mt-3 text-3xl text-[var(--foreground)]">
              Request and response shape
            </h2>
            <div className="mt-6 grid gap-6 xl:grid-cols-2">
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold tracking-[-0.01em] text-[var(--foreground)]">Input</p>
                  <CopyButton text={formatJson(project.exampleInput)} />
                </div>
                <pre className="min-h-56 rounded-[1.5rem] border border-[var(--line)] bg-[var(--code-sample-bg)] p-5 font-mono text-[13px] leading-7 text-[var(--code-sample-text)] shadow-[var(--code-inset-shadow)]">
                  {formatJson(project.exampleInput)}
                </pre>
              </div>
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold tracking-[-0.01em] text-[var(--foreground)]">Output</p>
                  <CopyButton text={formatJson(project.exampleOutput)} />
                </div>
                <pre className="min-h-56 rounded-[1.5rem] border border-[var(--line)] bg-[var(--code-sample-bg)] p-5 font-mono text-[13px] leading-7 text-[var(--code-sample-text)] shadow-[var(--code-inset-shadow)]">
                  {formatJson(project.exampleOutput)}
                </pre>
              </div>
            </div>
          </section>
        </div>

        <aside className="space-y-8 xl:sticky xl:top-24">
          <section className="surface-card rounded-xl p-6 sm:p-8">
            <p className="eyebrow">Project Snapshot</p>
            <div className="mt-5 space-y-5 text-sm text-[var(--foreground)]">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                  Category
                </p>
                <p className="mt-2 font-medium">{project.category}</p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                  Tags
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="surface-pill rounded-full px-3 py-1 text-xs text-[var(--muted)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                  Project Slug
                </p>
                <p className="mt-2 font-mono text-xs text-[var(--muted)]">{project.slug}</p>
              </div>
            </div>
          </section>

          {project.apiEndpoint && (project.demo?.enabled ?? true) ? (
            <>
              <section className="surface-card rounded-xl p-6 sm:p-8">
                <p className="eyebrow">FastAPI Endpoint</p>
                <p className="surface-panel mt-4 rounded-[1rem] px-4 py-3 font-mono text-sm leading-7 text-[var(--foreground)]">
                  {project.apiEndpoint}
                </p>
              </section>

              <ProjectDemo
                apiEndpoint={project.apiEndpoint}
                exampleInput={project.exampleInput}
                title={project.demo?.title}
                description={project.demo?.description}
                ctaLabel={project.demo?.ctaLabel}
              />
            </>
          ) : null}
        </aside>
        </div>
      </section>
    </article>
  );
}
