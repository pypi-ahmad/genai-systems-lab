# Architecture

## Overview

The Content Creation Pipeline is a CrewAI sequential crew where four specialized agents collaborate to transform a topic into publish-ready, SEO-optimized content. Each agent receives the output of the previous agent, refines it further, and passes a higher-quality artifact downstream. CrewAI manages agent orchestration, task delegation, and output chaining — there is no custom scheduler.

Primary flow:

```
Researcher → Writer → Editor → SEO Expert
```

## Agents

Each agent is defined with a role, goal, and backstory. CrewAI uses these to shape the LLM system prompt automatically.

### Researcher

Gathers background information, key facts, statistics, and source material on the given topic.

- **Role:** Senior Research Analyst
- **Goal:** Produce a comprehensive research brief with verified facts, data points, and source references that the writer can build on.
- **Model:** `gemini-3.1-pro-preview` — deep reasoning needed to identify credible sources, cross-reference claims, and prioritize the most relevant information.
- **Output:** A structured research brief (key findings, statistics, quotes, source list).

### Writer

Transforms the research brief into a well-structured first draft.

- **Role:** Content Writer
- **Goal:** Create an engaging, informative article that covers all key points from the research brief with clear structure and compelling narrative.
- **Model:** `gemini-3.1-pro-preview` — long-form generation with strong coherence requires the full reasoning model.
- **Output:** A complete article draft in Markdown (title, introduction, body sections, conclusion).

### Editor

Refines the draft for clarity, tone, grammar, and factual consistency against the research brief.

- **Role:** Senior Editor
- **Goal:** Polish the draft into publication-quality content — fix structural issues, tighten prose, ensure factual accuracy, and maintain consistent tone throughout.
- **Model:** `gemini-3-flash-preview` — editing is a targeted refinement task; speed matters more than deep generation.
- **Output:** A polished article with all edits applied inline.

### SEO Expert

Optimizes the final content for search engine visibility without degrading readability.

- **Role:** SEO Specialist
- **Goal:** Optimize headings, meta description, keyword density, internal linking suggestions, and readability score while preserving the editorial quality.
- **Model:** `gemini-3-flash-preview` — keyword analysis and structural tweaks are pattern-matching tasks that benefit from low latency.
- **Output:** The final optimized article plus an SEO metadata block (title tag, meta description, target keywords, readability score).

## Task Chain

Each CrewAI `Task` is bound to one agent and receives context from preceding tasks automatically.

| Step | Task | Agent | Reads | Produces |
|------|------|-------|-------|----------|
| 1 | Research the topic | Researcher | User topic/prompt | Research brief |
| 2 | Write first draft | Writer | Research brief | Article draft |
| 3 | Edit and polish | Editor | Article draft + Research brief | Polished article |
| 4 | SEO optimization | SEO Expert | Polished article | Final article + SEO metadata |

### Why sequential

- Each step has a hard dependency on the previous output. There is no parallelism to exploit.
- The linear chain makes debugging simple — any quality issue traces back to exactly one agent.
- CrewAI's `Process.sequential` handles the output-forwarding automatically.

## Crew Construction

```python
from crewai import Agent, Task, Crew, Process

# Agents
researcher = Agent(role="Senior Research Analyst", ...)
writer = Agent(role="Content Writer", ...)
editor = Agent(role="Senior Editor", ...)
seo_expert = Agent(role="SEO Specialist", ...)

# Tasks (sequential — each receives previous context)
research_task = Task(description="...", agent=researcher, expected_output="Research brief")
writing_task = Task(description="...", agent=writer, expected_output="Article draft")
editing_task = Task(description="...", agent=editor, expected_output="Polished article")
seo_task = Task(description="...", agent=seo_expert, expected_output="SEO-optimized article + metadata")

crew = Crew(
    agents=[researcher, writer, editor, seo_expert],
    tasks=[research_task, writing_task, editing_task, seo_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff(inputs={"topic": "How RAG is transforming enterprise search"})
```

## Model Usage

| Model | Agents | Rationale |
|-------|--------|-----------|
| `gemini-3.1-pro-preview` | Researcher, Writer | Research synthesis and long-form drafting require strong reasoning and coherence |
| `gemini-3-flash-preview` | Editor, SEO Expert | Refinement and optimization are targeted tasks where speed and cost efficiency matter |

### Cost and latency considerations

- The Researcher and Writer are the most token-intensive agents — they run once each and produce the bulk of new content.
- The Editor and SEO Expert consume fewer tokens (they refine existing text) and use the cheaper, faster model.
- Total pipeline cost scales linearly with content length. For a typical 1500-word article, expect 4 LLM calls total.

## Key Design Principles

1. **Progressive refinement.** Each agent builds on the previous output. Raw research becomes a draft, a draft becomes polished prose, polished prose becomes optimized content.
2. **Single responsibility.** Agents do one thing well. The writer never worries about SEO; the editor never does original research.
3. **Deterministic flow.** No conditional branching or loops. The pipeline always runs all four steps in order, producing predictable cost and latency.
4. **Graceful output.** If any agent produces weaker output, downstream agents compensate — the editor catches writing issues, the SEO expert fixes structural gaps.

## File Structure

```
app/
├── __init__.py
├── main.py          # Runtime entry point — exposes run(input, api_key)
├── crew.py          # Crew assembly — wires agents + tasks, returns Crew
├── agents.py        # Agent definitions (role, goal, backstory, model)
└── tasks.py         # Task definitions (description, expected_output, agent binding)
```
