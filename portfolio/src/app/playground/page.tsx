import type { Metadata } from "next";
import PlaygroundClient from "./playground-client";

export const metadata: Metadata = {
  title: "Playground — Portfolio",
  description: "Run any project interactively from the browser.",
};

export default function PlaygroundPage() {
  return (
    <section className="py-16">
      <PlaygroundClient />
    </section>
  );
}
