import type { MetadataRoute } from "next";
import { projectDetails } from "@/data/projects";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "http://localhost:3000";
  return ["", "/projects", "/playground", "/compare", "/model-compare", "/metrics", ...projectDetails.map(({ slug }) => `/projects/${slug}`)]
    .map((path) => ({ url: `${base}${path}`, lastModified: new Date() }));
}
