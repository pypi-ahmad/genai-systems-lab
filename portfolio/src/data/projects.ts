import projectCatalog from "./project-catalog.json";

export type Category = "GenAI" | "LangGraph" | "CrewAI";

export interface GraphNode {
  id: string;
  label: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
}

export interface Project {
  name: string;
  slug: string;
  category: Category;
  description: string;
}

export interface ProjectDemoConfig {
  enabled?: boolean;
  title?: string;
  description?: string;
  ctaLabel?: string;
}

export interface ProjectDetail extends Project {
  tags: string[];
  highlights: string[];
  architecture: string;
  features: string[];
  exampleInput: string;
  exampleOutput: string;
  apiEndpoint: string;
  demo?: ProjectDemoConfig;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
}

export const projectDetails = projectCatalog as ProjectDetail[];

export const projects: Project[] = projectDetails.map(
  ({ name, slug, category, description }) => ({
    name,
    slug,
    category,
    description,
  }),
);

export function getProject(slug: string): ProjectDetail | undefined {
  return projectDetails.find((project) => project.slug === slug);
}
