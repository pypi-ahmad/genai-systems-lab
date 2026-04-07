"use client";

import { useState, useRef } from "react";
import Link from "next/link";

type ProjectQuickPreviewProps = {
  slug: string;
  description: string;
  tags: string[];
  children: React.ReactNode;
};

export function ProjectQuickPreview({ slug, description, tags, children }: ProjectQuickPreviewProps) {
  const [open, setOpen] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  function show() {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = setTimeout(() => setOpen(true), 400);
  }

  function hide() {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = setTimeout(() => setOpen(false), 200);
  }

  return (
    <div className="relative" onMouseEnter={show} onMouseLeave={hide}>
      {children}
      {open && (
        <div
          className="absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-4 shadow-lg"
          onMouseEnter={() => { if (timeout.current) clearTimeout(timeout.current); }}
          onMouseLeave={hide}
        >
          <p className="line-clamp-3 text-sm leading-6 text-[var(--foreground)]">{description}</p>
          {tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {tags.slice(0, 4).map((tag) => (
                <span key={tag} className="surface-pill rounded-full px-2 py-0.5 text-[10px] text-[var(--muted)]">{tag}</span>
              ))}
            </div>
          )}
          <Link
            href={`/playground?project=${slug}`}
            className="button-base button-primary button-sm button-pill mt-3 w-full text-center"
          >
            Try it →
          </Link>
        </div>
      )}
    </div>
  );
}
