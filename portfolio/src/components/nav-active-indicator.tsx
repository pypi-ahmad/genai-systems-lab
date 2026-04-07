"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavActiveIndicator({
  href,
  label,
  className,
}: {
  href: string;
  label: string;
  className?: string;
}) {
  const pathname = usePathname();
  const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      aria-current={isActive ? "page" : undefined}
      className={`button-base button-ghost button-sm button-pill ${
        isActive
          ? "bg-[var(--accent-soft)] text-[var(--foreground)]"
          : ""
      } ${className ?? ""}`}
    >
      {label}
    </Link>
  );
}
