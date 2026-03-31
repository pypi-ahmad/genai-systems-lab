import type { Metadata } from "next";
import AuthClient from "./auth-client";

export const metadata: Metadata = {
  title: "Auth — Portfolio",
  description: "Sign up or log in to save and replay project runs.",
};

export default function AuthPage() {
  return (
    <section className="py-16">
      <AuthClient />
    </section>
  );
}