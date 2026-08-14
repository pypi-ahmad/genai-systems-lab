"use client";

export default function GlobalError({ reset }: { reset: () => void }) {
  return <html><body><main style={{ padding: 32 }}><h1>Something went wrong</h1><p>The page could not be rendered.</p><button onClick={reset}>Try again</button></main></body></html>;
}
