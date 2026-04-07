"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const primaryLinks = [
  { href: "/", label: "Home" },
  { href: "/projects", label: "Projects" },
  { href: "/playground", label: "Playground" },
];

const secondaryLinks = [
  { href: "/about", label: "About" },
  { href: "/metrics", label: "Metrics" },
  { href: "/compare", label: "Compare frameworks" },
  { href: "/architecture", label: "Architecture" },
];

const authLink = { href: "/auth", label: "Sign in" };

const allLinks = [...primaryLinks, ...secondaryLinks, authLink];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavLinks() {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile menu — all links flat */}
      <details className="relative sm:hidden">
        <summary className="button-base button-ghost button-sm button-pill cursor-pointer list-none text-sm font-medium text-[var(--muted)] marker:hidden">
          Menu
        </summary>
        <div className="absolute right-0 top-full mt-3 w-56 rounded-[1.25rem] border border-[var(--line)] bg-[var(--card-strong)] p-2 shadow-[var(--chart-tooltip-shadow)]">
          <ul className="grid gap-1 text-sm font-medium text-[var(--muted)]">
            {allLinks.map((link) => (
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

      {/* Desktop nav — primary links + More dropdown + Sign in */}
      <ul className="hidden items-center gap-1 text-sm font-medium text-[var(--muted)] sm:flex">
        {primaryLinks.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={`button-base button-ghost button-sm button-pill${isActive(pathname, link.href) ? " text-[var(--foreground)] bg-[var(--surface-soft)] border-[var(--line)]" : ""}`}
            >
              {link.label}
            </Link>
          </li>
        ))}

        {/* More dropdown */}
        <li className="relative">
          <details className="group">
            <summary
              className={`button-base button-ghost button-sm button-pill cursor-pointer list-none marker:hidden${
                secondaryLinks.some((l) => isActive(pathname, l.href))
                  ? " text-[var(--foreground)] bg-[var(--surface-soft)] border-[var(--line)]"
                  : ""
              }`}
            >
              More
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="ml-1 h-3 w-3 transition-transform duration-150 group-open:rotate-180">
                <path fillRule="evenodd" d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
              </svg>
            </summary>
            <div className="absolute right-0 top-full mt-2 w-52 rounded-[1.25rem] border border-[var(--line)] bg-[var(--card-strong)] p-2 shadow-[var(--chart-tooltip-shadow)]">
              <ul className="grid gap-1 text-sm font-medium text-[var(--muted)]">
                {secondaryLinks.map((link) => (
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
        </li>

        <li>
          <Link
            href={authLink.href}
            className={`button-base button-ghost button-sm button-pill${isActive(pathname, authLink.href) ? " text-[var(--foreground)] bg-[var(--surface-soft)] border-[var(--line)]" : ""}`}
          >
            {authLink.label}
          </Link>
        </li>
      </ul>
    </>
  );
}
