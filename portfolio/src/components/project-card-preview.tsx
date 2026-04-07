"use client";

import { useState, useRef, type ReactNode } from "react";
import Link from "next/link";

interface ProjectCardPreviewProps {
  slug: string;
  name: string;
  description: string;
  children: ReactNode;
}

export function ProjectCardPreview({ slug, name, description, children }: ProjectCardPreviewProps) {
  const [show, setShow] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setShow(true), 400);
  };

  const handleLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setShow(false);
  };

  return (
    <div className="relative" onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      {children}
      {show && (
        <div className="absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-4 shadow-lg">
          <p className="text-sm font-semibold text-[var(--foreground)]">{name}</p>
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-[var(--muted)]">{description}</p>
          <div className="mt-3 flex gap-2">
            <Link
              href={`/playground?project=${slug}`}
              className="button-base button-primary button-sm button-pill"
            >
              Try it
            </Link>
            <Link
              href={`/projects/${slug}`}
              className="button-base button-secondary button-sm button-pill"
            >
              Details
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
