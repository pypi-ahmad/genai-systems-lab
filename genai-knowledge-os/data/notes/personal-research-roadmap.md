# Personal Research Roadmap 2026

Primary theme for the first half of 2026 is trustworthy agent systems. I want to compare three reliability levers across projects: better retrieval, stricter tool contracts, and evaluator-driven feedback loops. My working hypothesis is that lightweight evaluators plus richer context windows will outperform more complex planner logic for most internal automation tasks.

Topics to explore:

1. Hybrid retrieval that combines dense vectors, keyword scoring, and recency weighting.
2. Decision logs that explain why an agent chose a tool, source, or branch.
3. Small domain-specific datasets for testing finance, operations, and document QA workflows.
4. Memory systems that store durable insights instead of raw chat transcripts.

Open question: when should a knowledge graph sit beside a vector store? My current view is that graphs help when entity resolution and relationship traversal matter, especially for people, vendors, projects, and policy dependencies.