import Link from "next/link";
import { Card } from "@/components/card";

const highlights = [
  "20 end-to-end AI systems",
  "Retrieval, orchestration, and evaluation",
  "API and UI delivery built to ship",
];

const stats = [
  { value: "20", label: "AI systems" },
  { value: "3", label: "Paradigms" },
  { value: "GenAI · LangGraph · CrewAI", label: "Platform mix" },
];

const capabilities = [
  {
    title: "Multi-Agent Systems",
    description:
      "Orchestrated agent workflows with clear role boundaries, structured handoffs, and repeatable execution paths.",
  },
  {
    title: "RAG Pipelines",
    description:
      "Retrieval pipelines over documents, code, and structured data with grounded outputs and practical response quality.",
  },
  {
    title: "Evaluation & Benchmarking",
    description:
      "System evaluation focused on correctness, latency, and reliability so improvements are measurable rather than assumed.",
  },
  {
    title: "Deployment",
    description:
      "Delivery across API and UI layers with production-oriented interfaces built for clarity, performance, and maintainability.",
  },
];

export default function Home() {
  return (
    <div className="space-y-0">
      <section className="section-accent grid gap-8 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div className="title-stack">
          <p className="eyebrow">Ahmad&apos;s AI Engineering Lab</p>
          <h1 className="heading-display max-w-2xl text-4xl sm:text-5xl">
            Practical{" "}
            <span className="bg-[var(--accent)] bg-clip-text text-transparent">
              agentic AI
            </span>{" "}
            systems for production.
          </h1>
          <p className="copy-lead max-w-2xl text-base sm:text-lg">
            A focused collection of shipped AI work spanning retrieval,
            orchestration, evaluation, and usable interfaces.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/projects"
              className="button-base button-primary button-lg button-pill"
            >
              Browse Projects
            </Link>
            <Link
              href="/playground"
              className="button-base button-secondary button-lg button-pill"
            >
              Open Playground
            </Link>
          </div>
        </div>

        <Card className="surface-card p-6 sm:p-8">
          <p className="eyebrow">What You&apos;ll Find</p>
          <p className="heading-card mt-4 max-w-2xl text-xl">
            End-to-end systems with clear architecture and practical tradeoffs.
          </p>
          <div className="mt-5 space-y-6">
            {highlights.map((highlight, i) => (
              <div
                key={highlight}
                className="surface-panel flex items-center gap-3 rounded-[1.25rem] px-4 py-4 text-sm leading-7 text-[var(--foreground)]"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--foreground)] text-[10px] font-bold text-[var(--bg)]">
                  {i + 1}
                </span>
                {highlight}
              </div>
            ))}
          </div>
        </Card>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">Stats</p>
          <h2 className="heading-section text-3xl sm:text-4xl">
            Scope and platform coverage.
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {stats.map((stat) => (
            <Card key={stat.label} className="rounded-xl p-6 sm:p-8">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                {stat.label}
              </p>
              <p className="mt-5 text-4xl font-semibold tracking-[-0.04em]">
                {stat.value}
              </p>
            </Card>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">Key Capabilities</p>
          <h2 className="heading-section text-3xl sm:text-4xl">
            Core engineering strengths across the platform.
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {capabilities.map((item, i) => (
            <div key={item.title} className="surface-card surface-card-hover rounded-xl p-6 sm:p-8">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent-solid)]">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <p className="heading-card text-lg">{item.title}</p>
              </div>
              <p className="copy-body mt-4 text-sm">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-6 py-16">
        <div className="section-heading">
          <p className="eyebrow">Built With</p>
          <h2 className="heading-section text-3xl sm:text-4xl">
            Technology stack and open source.
          </h2>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {["Python", "FastAPI", "LangChain", "LangGraph", "CrewAI", "Next.js", "TypeScript", "Tailwind CSS", "Docker"].map((tech) => (
            <span key={tech} className="surface-pill rounded-full px-4 py-1.5 text-sm font-medium text-[var(--foreground)]">
              {tech}
            </span>
          ))}
        </div>
        <div className="flex flex-wrap gap-3 pt-2">
          <a
            href="https://github.com/pypi-ahmad/genai-systems-lab"
            target="_blank"
            rel="noopener noreferrer"
            className="button-base button-secondary button-pill"
          >
            View on GitHub ↗
          </a>
        </div>
      </section>

      <div className="section-divider" />

      <section className="py-16">
        <Card className="p-6 sm:p-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end lg:justify-between">
            <div className="section-heading">
              <p className="eyebrow">Get Started</p>
              <h2 className="heading-section text-3xl sm:text-4xl">
                Explore the systems in more detail.
              </h2>
              <p className="copy-body max-w-2xl text-sm sm:text-base">
                Browse the project archive for system architecture and implementation details, or review Ahmad&apos;s skills and working style.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/projects"
                className="button-base button-primary button-lg button-pill"
              >
                View Projects →
              </Link>
              <Link
                href="/about"
                className="button-base button-secondary button-lg button-pill"
              >
                View Skills
              </Link>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
