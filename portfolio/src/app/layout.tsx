import type { Metadata } from "next";
import Link from "next/link";
import { IBM_Plex_Mono, Manrope } from "next/font/google";
import { ThemeToggle } from "@/components/theme-toggle";
import { ThemeProvider } from "./theme-provider";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
});

export const metadata: Metadata = {
  title: "Portfolio",
  description: "A clean portfolio built with Next.js, TypeScript, and Tailwind CSS.",
};

function Nav() {
  const links = [
    { href: "/", label: "Home" },
    { href: "/projects", label: "Projects" },
    { href: "/playground", label: "Playground" },
    { href: "/leaderboard", label: "Leaderboard" },
    { href: "/metrics", label: "Metrics" },
    { href: "/compare", label: "Comparison" },
    { href: "/auth", label: "Auth" },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[var(--surface)]/92 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-2.5 text-sm font-semibold tracking-[0.24em] text-[var(--foreground)] transition-opacity duration-200 ease-in-out hover:opacity-70"
        >
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--foreground)] text-[11px] font-bold text-[var(--bg)]">P</span>
          PORTFOLIO
        </Link>
        <div className="flex items-center gap-2 sm:gap-3">
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
                      className="button-base button-ghost w-full justify-start rounded-[0.9rem] px-3 py-2 text-left"
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
                  className="button-base button-ghost button-sm button-pill"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          <ThemeToggle className="h-9 w-9" />
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-[var(--line)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-10 text-sm text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p className="font-medium">&copy; {new Date().getFullYear()} Portfolio — GenAI Systems Lab</p>
        <p className="text-xs tracking-wide">Next.js 16 · TypeScript · Tailwind CSS v4</p>
      </div>
    </footer>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${manrope.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full overflow-x-hidden bg-[var(--bg)] font-sans text-[var(--text)]">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <div className="bg-orb bg-orb-left" aria-hidden />
          <div className="bg-orb bg-orb-right" aria-hidden />
          <div className="flex min-h-full flex-col">
            <Nav />
            <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-0 sm:px-6 lg:px-8">
              {children}
            </main>
            <Footer />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
