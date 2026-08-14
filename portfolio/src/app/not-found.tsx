import Link from "next/link";

export default function NotFound() {
  return <main className="mx-auto max-w-3xl p-8"><h1 className="text-3xl font-semibold">Page not found</h1><p className="mt-3">That page does not exist.</p><Link className="mt-6 inline-block underline" href="/">Return home</Link></main>;
}
