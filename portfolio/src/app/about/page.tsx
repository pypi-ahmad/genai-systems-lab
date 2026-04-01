import type { Metadata } from "next";
import { Card } from "@/components/card";

export const metadata: Metadata = {
  title: "About — GenAI Systems Lab",
};

const skills = [
  { group: "Languages", items: ["Python", "TypeScript", "SQL"] },
  { group: "Frameworks", items: ["LangGraph", "CrewAI", "FastAPI", "Next.js"] },
  {
    group: "AI / ML",
    items: ["LLM Integration", "Multi-Agent Systems", "RAG Pipelines", "Prompt Engineering"],
  },
  { group: "Infra", items: ["Docker", "OpenTelemetry", "DuckDB", "ChromaDB"] },
];

export default function AboutPage() {
  return (
    <div className="space-y-0">
      <section className="grid gap-8 py-16 lg:grid-cols-[1fr_0.9fr] lg:items-start">
        <div className="title-stack">
          <p className="eyebrow">About</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Building software that stays understandable as it scales.
          </h1>
          <div className="copy-stack copy-lead max-w-2xl text-lg">
            <p>
              I&apos;m Ahmad, a GenAI Systems Engineer focused on building
              production-grade AI applications. My work spans multi-agent
              orchestration, LLM-powered pipelines, and developer tooling for
              generative AI.
            </p>
            <p>
              The projects in this portfolio are part of the GenAI Systems Lab,
              a collection of end-to-end AI systems built with LangGraph,
              CrewAI, and custom agentic architectures.
            </p>
            <p>
              I care about clean architecture, observable systems, and shipping
              code that works beyond the demo stage.
            </p>
          </div>
        </div>
      </section>

      <section className="py-16">
        <Card className="p-6 sm:p-8">
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              { label: "Primary focus", value: "AI systems engineering" },
              { label: "Delivery style", value: "Typed, minimal, measurable" },
              { label: "Front-end stack", value: "Next.js + Tailwind" },
            ].map((item) => (
              <div key={item.label} className="surface-panel rounded-[1.25rem] p-5">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                  {item.label}
                </p>
                <p className="mt-3 text-lg font-semibold tracking-[-0.03em]">
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">Core Skills</p>
          <h2 className="heading-section text-3xl">
            Tools and systems I work with.
          </h2>
        </div>
        <div className="grid gap-6 sm:grid-cols-2">
          {skills.map((s) => (
            <Card
              key={s.group}
              className="surface-card-hover rounded-xl p-6 sm:p-8"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                {s.group}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {s.items.map((item) => (
                  <span
                    key={item}
                    className="surface-pill rounded-full px-3.5 py-1.5 text-sm font-medium text-[var(--foreground)]"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      <section className="space-y-8 py-16">
        <div className="section-heading">
          <p className="eyebrow">Approach</p>
          <h2 className="heading-section text-3xl">
            Principles that shape the work.
          </h2>
        </div>
        <div className="grid gap-6 sm:grid-cols-3">
          {[
            {
              title: "Ship, don\u2019t demo",
              text: "Every project includes runnable structure, tests, and evaluation instead of isolated prototypes.",
            },
            {
              title: "Observe everything",
              text: "Logs, traces, and metrics matter because debugging AI systems without visibility is mostly guesswork.",
            },
            {
              title: "Keep it legible",
              text: "The implementation should stay understandable for the next engineer, not just impressive in a screenshot.",
            },
          ].map((v) => (
            <Card
              key={v.title}
              className="surface-card-hover rounded-xl p-6 sm:p-8"
            >
              <h3 className="heading-card text-lg">{v.title}</h3>
              <p className="copy-body mt-3 text-sm">
                {v.text}
              </p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
