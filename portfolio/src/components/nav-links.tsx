"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/projects", label: "Projects" },
  { href: "/playground", label: "Playground" },
  { href: "/metrics", label: "Metrics" },
  { href: "/compare", label: "LangGraph vs CrewAI" },
  { href: "/architecture", label: "Architecture" },
  { href: "/auth", label: "Auth" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavLinks() {
  const pathname = usePathname();

  return (
    <>
      <details className="relative sm:hidden">
        <summary className="button-base button-ghost button-sm button-pill cursor-pointer list-none text-sm font-medium text-[var(--muted)] marker:hidden">
          Menu
        </summary>
        <div className="absolute right-0 top-full mt-3 w-56 rounded-[1.25rem] border border-[var(--line)] bg-[var(--card-strong)] p-2 shadow-[var(--chart-tooltip-shadow)]">
          <ul className="grid gap-1 text-sm font-medium text-[var(--muted)]">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`button-base button-ghost w-full justify-start rounded-[0.9rem] px-3 py-2 text-left${isActive(pathname, link.href) ? " text-[var(--foreground)] bg-[var(--surface-soft)]" : ""}`}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </details>
      <ul className="hidden items-center gap-1 text-sm font-medium text-[var(--muted)] sm:flex">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={`button-base button-ghost button-sm button-pill${isActive(pathname, link.href) ? " text-[var(--foreground)] bg-[var(--surface-soft)] border-[var(--line)]" : ""}`}
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
