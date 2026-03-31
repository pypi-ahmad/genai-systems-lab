import type { Metadata } from "next";
import ArchitectureDiagram from "./diagram";

export const metadata: Metadata = {
  title: "Architecture — Portfolio",
  description: "Interactive system architecture diagram for GenAI Systems Lab.",
};

export default function ArchitecturePage() {
  return (
    <div className="space-y-0">
      <section className="grid gap-8 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="title-stack">
          <p className="eyebrow">System Architecture</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            System Architecture
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            A lightweight view of how requests move through the portfolio stack:
            from the UI into the shared API, into a project runtime, and down
            into the shared infrastructure used across systems.
          </p>
        </div>

        <div className="surface-card rounded-xl p-6 sm:p-8">
          <p className="eyebrow">Interaction</p>
          <div className="mt-5 space-y-6">
            {[
              "Hover a box to highlight its immediate neighborhood in the flow.",
              "Click a box to pin its description in the detail panel.",
              "The diagram stays intentionally small: boxes, arrows, and no heavy rendering layer.",
            ].map((item, index) => (
              <div
                key={item}
                className="surface-panel flex items-center gap-3 rounded-[1.25rem] px-4 py-4 text-sm leading-7 text-[var(--foreground)]"
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

      <section className="py-16">
        <ArchitectureDiagram />
      </section>
    </div>
  );
}
