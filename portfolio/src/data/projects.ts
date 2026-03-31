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

interface RawProjectDetail extends Omit<ProjectDetail, "name"> {
  title: string;
}

const rawProjectDetails: RawProjectDetail[] = [
  // ── GenAI ──────────────────────────────────────────────
  {
    slug: "genai-research-system",
    title: "Multi-Agent Research System",
    category: "GenAI",
    description:
      "Decomposes research queries into tasks, gathers findings, critiques drafts, and produces multi-format outputs with quality metrics.",
    tags: ["Research", "Multi-Agent", "Evaluation"],
    highlights: [
      "Iterative revision loop with quality gates",
      "Per-node instrumentation and trace reporting",
      "Multi-format output generation",
    ],
    architecture:
      "A LangGraph state machine routes through Planner → Researcher → Critic → Writer → Editor → Formatter nodes. The Critic node triggers conditional revision loops with a bounded retry count. Each node is instrumented for latency and token tracking. The service layer exposes the graph via FastAPI and collects quality, originality, and format-coverage metrics.",
    features: [
      "Multi-step research planning with task decomposition",
      "Critic-driven revision loop with quality gates",
      "Originality and editorial checks before output",
      "Multi-format generation (report, blog, social)",
      "Per-node execution trace and latency metrics",
    ],
    exampleInput: '{"input": "Compare transformer architectures for code generation"}',
    exampleOutput: '{"report": "## Key Findings\\n1. Decoder-only models dominate...", "quality_score": 0.87, "formats": ["report", "blog"]}',
    apiEndpoint: "/multi-agent-research/run",
    demo: {
      enabled: true,
      title: "Run live research query",
      description: "Edit the request body and send it to the FastAPI backend for this system.",
      ctaLabel: "Run Research Demo",
    },
    graph: {
      nodes: [
        { id: "planner", label: "Planner" },
        { id: "researcher", label: "Researcher" },
        { id: "critic", label: "Critic" },
        { id: "writer", label: "Writer" },
        { id: "editor", label: "Editor" },
        { id: "formatter", label: "Formatter" },
      ],
      edges: [
        { from: "planner", to: "researcher" },
        { from: "researcher", to: "critic" },
        { from: "critic", to: "writer", label: "pass" },
        { from: "critic", to: "researcher", label: "revise" },
        { from: "writer", to: "editor" },
        { from: "editor", to: "formatter" },
      ],
    },
  },
  {
    slug: "genai-nl2sql-agent",
    title: "NL2SQL Agent",
    category: "GenAI",
    description:
      "Translates natural language questions into safe DuckDB queries, validates the SQL, executes it, and summarizes the result.",
    tags: ["NL2SQL", "DuckDB", "Analytics"],
    highlights: [
      "Schema-grounded SQL generation",
      "Read-only validation layer",
      "Natural language result summaries",
    ],
    architecture:
      "The pipeline flows through Schema Loader → SQL Generator → Validator → DuckDB Executor → Summarizer. The Schema Loader introspects the live database to ground generation. The Validator rejects mutating statements before any query runs. On failure, the agent retries with error context fed back to the generator.",
    features: [
      "Schema-grounded SQL generation from natural language",
      "Read-only validation blocking mutating statements",
      "DuckDB execution with structured result tables",
      "Automatic retry with error-context feedback",
      "Natural language summary from returned rows",
    ],
    exampleInput: '{"input": "top customers by revenue"}',
    exampleOutput: '{"sql": "SELECT customer, SUM(revenue) AS total FROM sales GROUP BY customer ORDER BY total DESC LIMIT 10", "summary": "Acme Corp leads with $2.4M..."}',
    apiEndpoint: "/nl2sql-agent/run",
    graph: {
      nodes: [
        { id: "schema", label: "Schema Loader" },
        { id: "generator", label: "SQL Generator" },
        { id: "validator", label: "Validator" },
        { id: "executor", label: "DuckDB Executor" },
        { id: "summarizer", label: "Summarizer" },
      ],
      edges: [
        { from: "schema", to: "generator" },
        { from: "generator", to: "validator" },
        { from: "validator", to: "executor", label: "valid" },
        { from: "validator", to: "generator", label: "retry" },
        { from: "executor", to: "summarizer" },
      ],
    },
  },
  {
    slug: "genai-clinical-assistant",
    title: "Clinical Decision Support",
    category: "GenAI",
    description:
      "Extracts patient details, retrieves conditions from a knowledge base, applies LLM reasoning, and formats a structured clinical summary.",
    tags: ["Healthcare", "Decision Support", "RAG"],
    highlights: [
      "Structured clinical reasoning pipeline",
      "Deterministic confidence scoring",
      "Knowledge-base-grounded retrieval",
    ],
    architecture:
      "Patient data enters an Extractor that normalizes demographics, symptoms, and history. A Retriever searches an embedded medical knowledge base for matching conditions. The Reasoner applies LLM-based differential diagnosis with deterministic confidence scoring. The Formatter outputs a structured clinical summary with flagged risks.",
    features: [
      "Patient data extraction and normalization",
      "Knowledge-base retrieval for condition matching",
      "LLM-based differential diagnosis",
      "Deterministic confidence score assignment",
      "Structured summary with risk flags",
    ],
    exampleInput: '{"input": "45-year-old male, chest pain radiating to left arm, history of hypertension"}',
    exampleOutput: '{"differentials": [{"condition": "Acute coronary syndrome", "confidence": 0.82}], "risk_flags": ["cardiac"], "summary": "High-priority cardiac workup recommended..."}',
    apiEndpoint: "/clinical-assistant/run",
    graph: {
      nodes: [
        { id: "extractor", label: "Extractor" },
        { id: "retriever", label: "Retriever" },
        { id: "reasoner", label: "Reasoner" },
        { id: "formatter", label: "Formatter" },
      ],
      edges: [
        { from: "extractor", to: "retriever" },
        { from: "retriever", to: "reasoner" },
        { from: "reasoner", to: "formatter" },
      ],
    },
  },
  {
    slug: "genai-browser-agent",
    title: "Autonomous Browser Agent",
    category: "GenAI",
    description:
      "Observes web pages, plans the next action, executes browser interactions via Playwright, and loops until the task is complete.",
    tags: ["Browser", "Automation", "Playwright"],
    highlights: [
      "Observe-plan-act loop architecture",
      "Run memory to prevent blind repetition",
      "Screenshot-based observation path",
    ],
    architecture:
      "An observe-plan-act loop drives the agent. The Perception module builds a text or screenshot-based page observation. The Planner selects the next structured action (click, type, scroll, navigate). The Action Executor dispatches through Playwright. Run Memory records each step to avoid repetition. The loop terminates on goal completion or step budget exhaustion.",
    features: [
      "Goal-driven browser automation",
      "Text and vision-based page observation",
      "Structured action selection from page state",
      "Playwright-backed reliable execution",
      "Step memory preventing blind loops",
    ],
    exampleInput: '{"input": "Search for recent AI papers on arXiv"}',
    exampleOutput: '{"steps": 7, "status": "completed", "final_url": "https://arxiv.org/search/?query=AI", "summary": "Found 10 recent papers on transformer efficiency..."}',
    apiEndpoint: "/browser-agent/run",
    graph: {
      nodes: [
        { id: "perception", label: "Perception" },
        { id: "planner", label: "Planner" },
        { id: "executor", label: "Action Executor" },
        { id: "memory", label: "Run Memory" },
      ],
      edges: [
        { from: "perception", to: "planner" },
        { from: "planner", to: "executor" },
        { from: "executor", to: "memory" },
        { from: "memory", to: "perception", label: "loop" },
      ],
    },
  },
  {
    slug: "genai-financial-analyst",
    title: "Financial Analyst Agent",
    category: "GenAI",
    description:
      "Transforms CSV data into metrics, trend analysis, optional forecasts, and a structured report combining deterministic computation with LLM interpretation.",
    tags: ["Finance", "Analysis", "Reporting"],
    highlights: [
      "Deterministic metric computation",
      "LLM-backed trend interpretation",
      "Structured report generation",
    ],
    architecture:
      "CSV data flows through a Metric Engine that computes deterministic financial ratios and aggregates. A Trend Analyzer identifies patterns and anomalies. An optional Forecaster projects future values. The Report Writer combines computed metrics with LLM-generated narrative interpretation into a structured output.",
    features: [
      "Deterministic financial metric computation",
      "Automated trend and anomaly detection",
      "Optional time-series forecasting",
      "LLM-generated narrative interpretation",
      "Structured report with tables and summaries",
    ],
    exampleInput: '{"input": "Analyze Q4 revenue trends", "file_path": "data/financials.csv"}',
    exampleOutput: '{"metrics": {"revenue_growth": "12.3%", "margin": "34.1%"}, "trends": ["Accelerating growth in APAC"], "report": "## Q4 Analysis\\nRevenue grew 12.3%..."}',
    apiEndpoint: "/financial-analyst/run",
    graph: {
      nodes: [
        { id: "metrics", label: "Metric Engine" },
        { id: "trends", label: "Trend Analyzer" },
        { id: "forecaster", label: "Forecaster" },
        { id: "writer", label: "Report Writer" },
      ],
      edges: [
        { from: "metrics", to: "trends" },
        { from: "trends", to: "forecaster" },
        { from: "forecaster", to: "writer" },
      ],
    },
  },
  {
    slug: "genai-code-copilot",
    title: "Codebase Copilot",
    category: "GenAI",
    description:
      "Indexes local source files, builds retrieval-friendly code chunks, and generates grounded answers about the codebase with traceability.",
    tags: ["Code", "RAG", "Developer Tools"],
    highlights: [
      "Repository-aware context retrieval",
      "Traceable source references",
      "Multi-language support",
    ],
    architecture:
      "An Indexer walks the repository and splits files into retrieval-friendly code chunks with metadata. A Vector Store holds embeddings for similarity search. On query, the Retriever fetches relevant chunks and the Generator produces a grounded answer with file-path references back to the source.",
    features: [
      "Automatic repository indexing and chunking",
      "Vector-based code similarity search",
      "Grounded answers with source file references",
      "Multi-language support (Python, TypeScript, etc.)",
      "Incremental re-indexing on file changes",
    ],
    exampleInput: '{"input": "How does the retry logic work in the executor?"}',
    exampleOutput: '{"answer": "The executor retries up to 3 times with exponential backoff...", "sources": ["src/agents/executor.py:L45-L67"]}',
    apiEndpoint: "/code-copilot/run",
    graph: {
      nodes: [
        { id: "indexer", label: "Indexer" },
        { id: "store", label: "Vector Store" },
        { id: "retriever", label: "Retriever" },
        { id: "generator", label: "Generator" },
      ],
      edges: [
        { from: "indexer", to: "store" },
        { from: "store", to: "retriever" },
        { from: "retriever", to: "generator" },
      ],
    },
  },
  {
    slug: "genai-doc-intelligence",
    title: "Document Intelligence",
    category: "GenAI",
    description:
      "Ingests documents, chunks and embeds them, retrieves grounded context, answers questions with source references, and extracts structured data.",
    tags: ["Documents", "RAG", "Extraction"],
    highlights: [
      "Chunk-and-embed ingestion pipeline",
      "Source-referenced QA",
      "Structured information extraction",
    ],
    architecture:
      "Documents are ingested through a chunking pipeline that splits by section boundaries. Chunks are embedded and stored in a vector index. The QA path retrieves relevant chunks and generates answers with source citations. A parallel Extraction path pulls structured fields (dates, entities, amounts) from individual documents.",
    features: [
      "Section-aware document chunking",
      "Hybrid vector retrieval with reranking",
      "Source-cited question answering",
      "Structured field extraction (entities, dates, amounts)",
      "Batch ingestion for document collections",
    ],
    exampleInput: '{"input": "What are the key terms in the partnership agreement?"}',
    exampleOutput: '{"answer": "The agreement specifies a 3-year term with auto-renewal...", "sources": ["partnership_v2.pdf, Section 4"], "extracted": {"term": "3 years", "parties": ["Acme Corp", "Beta Inc"]}}',
    apiEndpoint: "/doc-intelligence/run",
    graph: {
      nodes: [
        { id: "chunker", label: "Chunker" },
        { id: "embedder", label: "Embedder" },
        { id: "retriever", label: "Retriever" },
        { id: "qa", label: "QA Generator" },
        { id: "extractor", label: "Extractor" },
      ],
      edges: [
        { from: "chunker", to: "embedder" },
        { from: "embedder", to: "retriever" },
        { from: "retriever", to: "qa" },
        { from: "retriever", to: "extractor" },
      ],
    },
  },
  {
    slug: "genai-knowledge-os",
    title: "Knowledge OS",
    category: "GenAI",
    description:
      "Ingests local notes, stores vectorized chunks, retrieves relevant context, summarizes content, and generates cross-document insights.",
    tags: ["Knowledge", "Vector Search", "Memory"],
    highlights: [
      "Personal knowledge graph",
      "Cross-document insight generation",
      "Optional memory persistence",
    ],
    architecture:
      "Notes are ingested, chunked, and embedded into a persistent vector store. A Retriever surfaces relevant chunks for any query. A Summarizer condenses retrieved content. An Insight Generator identifies connections across documents and produces cross-reference memos. Optional memory persistence retains context across sessions.",
    features: [
      "Personal note ingestion and vectorization",
      "Semantic search across all stored knowledge",
      "Automatic content summarization",
      "Cross-document insight and link discovery",
      "Persistent memory across sessions",
    ],
    exampleInput: '{"input": "What do my notes say about attention mechanisms?"}',
    exampleOutput: '{"summary": "Your notes reference attention in 4 documents...", "insights": ["Connection found between self-attention notes and efficiency paper highlights"], "sources": ["transformers.md", "efficiency-review.md"]}',
    apiEndpoint: "/knowledge-os/run",
    graph: {
      nodes: [
        { id: "ingest", label: "Ingestor" },
        { id: "store", label: "Vector Store" },
        { id: "retriever", label: "Retriever" },
        { id: "summarizer", label: "Summarizer" },
        { id: "insights", label: "Insight Generator" },
      ],
      edges: [
        { from: "ingest", to: "store" },
        { from: "store", to: "retriever" },
        { from: "retriever", to: "summarizer" },
        { from: "retriever", to: "insights" },
      ],
    },
  },
  {
    slug: "genai-interviewer",
    title: "AI Interviewer",
    category: "GenAI",
    description:
      "Generates adaptive interview questions, evaluates answers, adjusts difficulty over time, and returns structured feedback.",
    tags: ["Interview", "Adaptive", "Assessment"],
    highlights: [
      "Difficulty-adaptive question generation",
      "Structured answer evaluation",
      "Iterative interview loop",
    ],
    architecture:
      "The system runs an iterative loop: a Question Generator produces a question at the current difficulty level, the candidate responds, an Evaluator scores the answer and adjusts difficulty, and the loop continues until the session budget is reached. A Feedback Compiler produces a final structured assessment.",
    features: [
      "Adaptive difficulty scaling based on performance",
      "Multi-topic technical question generation",
      "Structured scoring rubric per answer",
      "Session-level performance trend tracking",
      "Final assessment report with strengths and gaps",
    ],
    exampleInput: '{"input": "Senior backend engineer with Python and distributed systems experience"}',
    exampleOutput: '{"questions_asked": 8, "avg_score": 0.74, "difficulty_reached": "hard", "assessment": "Strong on system design, gaps in concurrency patterns..."}',
    apiEndpoint: "/interviewer/run",
    graph: {
      nodes: [
        { id: "generator", label: "Question Generator" },
        { id: "evaluator", label: "Evaluator" },
        { id: "adjuster", label: "Difficulty Adjuster" },
        { id: "compiler", label: "Feedback Compiler" },
      ],
      edges: [
        { from: "generator", to: "evaluator" },
        { from: "evaluator", to: "adjuster" },
        { from: "adjuster", to: "generator", label: "next" },
        { from: "adjuster", to: "compiler", label: "done" },
      ],
    },
  },
  {
    slug: "genai-ui-builder",
    title: "Generative UI Builder",
    category: "GenAI",
    description:
      "Converts natural language descriptions into structured UI specs, validates them, generates React code, and optionally repairs invalid outputs.",
    tags: ["UI", "Code Generation", "React"],
    highlights: [
      "Prompt-to-React component pipeline",
      "Intermediate spec validation",
      "Self-repair for invalid outputs",
    ],
    architecture:
      "A Spec Generator converts the prompt into a constrained JSON UI specification. A Validator checks the spec against layout and component rules. The Code Generator produces a React component from the validated spec. If the output fails syntax checks, a Repair step feeds errors back to the generator for a corrective pass.",
    features: [
      "Natural language to structured UI spec conversion",
      "Rule-based spec validation before code generation",
      "React/TypeScript component output",
      "Automatic self-repair for invalid code",
      "Preview-ready component export",
    ],
    exampleInput: '{"input": "A dashboard card showing revenue, users, and a line chart"}',
    exampleOutput: '{"spec": {"layout": "card", "children": ["stat:revenue", "stat:users", "chart:line"]}, "code": "export function DashboardCard() { ... }", "valid": true}',
    apiEndpoint: "/ui-builder/run",
    graph: {
      nodes: [
        { id: "spec", label: "Spec Generator" },
        { id: "validator", label: "Validator" },
        { id: "codegen", label: "Code Generator" },
        { id: "repair", label: "Repair" },
      ],
      edges: [
        { from: "spec", to: "validator" },
        { from: "validator", to: "codegen", label: "valid" },
        { from: "codegen", to: "repair", label: "error" },
        { from: "repair", to: "validator", label: "retry" },
      ],
    },
  },

  // ── LangGraph ──────────────────────────────────────────
  {
    slug: "lg-data-agent",
    title: "Data Analysis Agent",
    category: "LangGraph",
    description:
      "Plans tabular operations, executes them deterministically, interprets results, and loops through evaluation until the analysis is sufficient.",
    tags: ["Data", "Tabular", "Evaluation Loop"],
    highlights: [
      "Structured data reasoning with retries",
      "Deterministic tabular execution",
      "Evaluator-gated iteration",
    ],
    architecture:
      "A LangGraph state machine connects Planner → Executor → Interpreter → Evaluator nodes. The Planner selects tabular operations (filter, group, aggregate). The Executor runs them deterministically. The Interpreter generates an explanation. The Evaluator decides whether the analysis is sufficient or triggers another iteration.",
    features: [
      "Structured operation planning over tabular data",
      "Deterministic pandas-based execution",
      "LLM-powered result interpretation",
      "Evaluator-gated iteration loop",
      "Controlled retry budget",
    ],
    exampleInput: '{"input": "What is the average order value by region?"}',
    exampleOutput: '{"result": {"APAC": 142.50, "EMEA": 128.30, "NA": 156.80}, "interpretation": "North America leads with $156.80 AOV...", "iterations": 1}',
    apiEndpoint: "/data-agent/run",
    graph: {
      nodes: [
        { id: "planner", label: "Planner" },
        { id: "executor", label: "Executor" },
        { id: "interpreter", label: "Interpreter" },
        { id: "evaluator", label: "Evaluator" },
      ],
      edges: [
        { from: "planner", to: "executor" },
        { from: "executor", to: "interpreter" },
        { from: "interpreter", to: "evaluator" },
        { from: "evaluator", to: "planner", label: "retry" },
      ],
    },
  },
  {
    slug: "lg-debugging-agent",
    title: "Debugging Agent",
    category: "LangGraph",
    description:
      "Analyzes faulty code, proposes a fix, runs tests, and loops through evaluation until the issue is resolved or the retry budget is exhausted.",
    tags: ["Debugging", "Testing", "Iterative"],
    highlights: [
      "Graph-controlled fix-test-evaluate loop",
      "Bounded retry budget",
      "Sandbox-based test execution",
    ],
    architecture:
      "The LangGraph loop connects Analyzer → Fixer → Tester → Evaluator. The Analyzer identifies the root cause. The Fixer generates a patch. The Tester runs validation in a sandboxed environment. The Evaluator checks pass/fail and routes back to the Fixer or exits. A bounded retry budget prevents infinite loops.",
    features: [
      "Automated root cause analysis",
      "LLM-generated code patches",
      "Sandbox test execution",
      "Evaluator-controlled fix loop",
      "Bounded retry budget (max 3 attempts)",
    ],
    exampleInput: '{"input": "Function crashes on empty input and should return an empty list"}',
    exampleOutput: '{"fixed": true, "patch": "def process(items):\\n    if not items:\\n        return []\\n    ...", "attempts": 2, "tests_passed": 4}',
    apiEndpoint: "/debugging-agent/run",
    graph: {
      nodes: [
        { id: "analyzer", label: "Analyzer" },
        { id: "fixer", label: "Fixer" },
        { id: "tester", label: "Tester" },
        { id: "evaluator", label: "Evaluator" },
      ],
      edges: [
        { from: "analyzer", to: "fixer" },
        { from: "fixer", to: "tester" },
        { from: "tester", to: "evaluator" },
        { from: "evaluator", to: "fixer", label: "retry" },
      ],
    },
  },
  {
    slug: "lg-research-agent",
    title: "Research Agent",
    category: "LangGraph",
    description:
      "A graph-based research scaffold for expanding planning, retrieval, and reporting logic into a full iterative research workflow.",
    tags: ["Research", "Scaffold", "Planning"],
    highlights: [
      "Extensible graph-based architecture",
      "Planning and retrieval node structure",
      "Designed for iterative expansion",
    ],
    architecture:
      "A minimal LangGraph scaffold with Planner → Retriever → Reporter nodes. The Planner decomposes the query into sub-tasks. The Retriever gathers information per task. The Reporter synthesizes findings. The architecture is designed to slot in additional nodes (critic, reviser) as the workflow matures.",
    features: [
      "Query decomposition into research sub-tasks",
      "Per-task information retrieval",
      "Finding synthesis and report generation",
      "Extensible node architecture for future expansion",
      "Clean separation between planning and execution",
    ],
    exampleInput: '{"input": "Survey recent advances in mixture-of-experts models"}',
    exampleOutput: '{"plan": ["MoE architectures", "routing strategies", "scaling results"], "report": "## Survey\\nMixture-of-experts models have evolved...", "sources": 5}',
    apiEndpoint: "/research-agent/run",
    graph: {
      nodes: [
        { id: "planner", label: "Planner" },
        { id: "retriever", label: "Retriever" },
        { id: "reporter", label: "Reporter" },
      ],
      edges: [
        { from: "planner", to: "retriever" },
        { from: "retriever", to: "reporter" },
      ],
    },
  },
  {
    slug: "lg-support-agent",
    title: "Support Agent",
    category: "LangGraph",
    description:
      "Classifies inbound requests, retrieves relevant context, generates a response, and decides whether to escalate.",
    tags: ["Support", "Classification", "Routing"],
    highlights: [
      "Intent classification node",
      "Context-aware response generation",
      "Escalation routing logic",
    ],
    architecture:
      "The LangGraph flow runs Classifier → Retriever → Responder → Escalation Router. The Classifier identifies intent and urgency. The Retriever pulls relevant knowledge-base articles. The Responder drafts a reply. The Router decides if the case needs human escalation based on confidence and complexity thresholds.",
    features: [
      "Intent and urgency classification",
      "Knowledge-base article retrieval",
      "Context-grounded response generation",
      "Confidence-based escalation routing",
      "Structured case metadata output",
    ],
    exampleInput: '{"input": "My API key stopped working after I rotated it yesterday"}',
    exampleOutput: '{"intent": "authentication_issue", "response": "After key rotation, the new key may take up to 5 minutes to propagate...", "escalate": false, "confidence": 0.91}',
    apiEndpoint: "/support-agent/run",
    graph: {
      nodes: [
        { id: "classifier", label: "Classifier" },
        { id: "retriever", label: "Retriever" },
        { id: "responder", label: "Responder" },
        { id: "router", label: "Escalation Router" },
      ],
      edges: [
        { from: "classifier", to: "retriever" },
        { from: "retriever", to: "responder" },
        { from: "responder", to: "router" },
      ],
    },
  },
  {
    slug: "lg-workflow-agent",
    title: "Workflow Agent",
    category: "LangGraph",
    description:
      "Plans multi-step tasks, executes with checkpoints, validates intermediate progress, and supports controlled continuation across steps.",
    tags: ["Workflow", "Checkpoints", "Stateful"],
    highlights: [
      "Checkpoint-aware execution",
      "Resume support for interrupted runs",
      "Step-level validation",
    ],
    architecture:
      "A stateful LangGraph workflow connects Planner → Executor → Validator → Checkpoint Manager. The Planner breaks the task into ordered steps. The Executor runs each step with state updates. The Validator checks progress per step. The Checkpoint Manager persists state so interrupted runs can resume from the last successful step.",
    features: [
      "Multi-step task decomposition",
      "Checkpoint persistence for durability",
      "Step-level validation and progress tracking",
      "Resume from last successful checkpoint",
      "Configurable step timeout and retry policy",
    ],
    exampleInput: '{"input": "Run a multi-step onboarding workflow for a new enterprise customer"}',
    exampleOutput: '{"steps_completed": 5, "steps_total": 5, "status": "completed", "checkpoints": ["account_created", "team_invited", "integrations_configured", "training_scheduled", "handoff_complete"]}',
    apiEndpoint: "/workflow-agent/run",
    graph: {
      nodes: [
        { id: "planner", label: "Planner" },
        { id: "executor", label: "Executor" },
        { id: "validator", label: "Validator" },
        { id: "checkpoint", label: "Checkpoint Mgr" },
      ],
      edges: [
        { from: "planner", to: "executor" },
        { from: "executor", to: "validator" },
        { from: "validator", to: "checkpoint" },
        { from: "checkpoint", to: "executor", label: "next step" },
      ],
    },
  },

  // ── CrewAI ─────────────────────────────────────────────
  {
    slug: "crew-content-pipeline",
    title: "Content Pipeline",
    category: "CrewAI",
    description:
      "Moves a topic through research, drafting, editing, and SEO optimization with clear stage-by-stage handoffs between specialized agents.",
    tags: ["Content", "SEO", "Marketing"],
    highlights: [
      "Research-to-publish agent chain",
      "SEO optimization stage",
      "Structured editorial handoffs",
    ],
    architecture:
      "A sequential CrewAI process chains Researcher → Writer → Editor → SEO Optimizer agents. The Researcher gathers background material. The Writer produces a draft. The Editor refines tone and structure. The SEO Optimizer adds keywords, meta descriptions, and heading improvements. Each agent's output feeds directly into the next.",
    features: [
      "Topic research with source gathering",
      "Structured draft generation",
      "Editorial refinement for tone and clarity",
      "SEO keyword and metadata optimization",
      "Stage-by-stage handoff traceability",
    ],
    exampleInput: '{"input": "Write a blog post about LLM evaluation best practices"}',
    exampleOutput: '{"title": "LLM Evaluation Best Practices", "draft": "## Introduction\\nEvaluating LLMs requires...", "seo": {"keywords": ["LLM evaluation", "benchmarks"], "meta": "A guide to evaluating LLMs..."}}',
    apiEndpoint: "/content-pipeline/run",
    graph: {
      nodes: [
        { id: "researcher", label: "Researcher" },
        { id: "writer", label: "Writer" },
        { id: "editor", label: "Editor" },
        { id: "seo", label: "SEO Optimizer" },
      ],
      edges: [
        { from: "researcher", to: "writer" },
        { from: "writer", to: "editor" },
        { from: "editor", to: "seo" },
      ],
    },
  },
  {
    slug: "crew-hiring-system",
    title: "Hiring Decision Crew",
    category: "CrewAI",
    description:
      "Evaluates candidates through screening, technical assessment, behavioral assessment, decision synthesis, and bias review.",
    tags: ["Hiring", "Assessment", "Bias Audit"],
    highlights: [
      "Five-stage candidate review pipeline",
      "Separate technical and behavioral evaluation",
      "Bias audit before final recommendation",
    ],
    architecture:
      "A five-agent sequential crew: Screener → Technical Interviewer → Behavioral Interviewer → Hiring Manager → Bias Auditor. Each agent appends a structured assessment. The Hiring Manager synthesizes all inputs into a recommendation. The Bias Auditor reviews the full chain for consistency and fairness issues.",
    features: [
      "Resume screening with criteria extraction",
      "Technical skill assessment",
      "Behavioral and culture-fit evaluation",
      "Decision synthesis from multiple perspectives",
      "Bias audit with flagged concerns",
    ],
    exampleInput: '{"input": "Senior backend engineer with Python, FastAPI, and distributed systems experience"}',
    exampleOutput: '{"recommendation": "strong_hire", "scores": {"technical": 0.88, "behavioral": 0.79}, "bias_flags": [], "summary": "Strong technical fit with solid communication..."}',
    apiEndpoint: "/hiring-crew/run",
    graph: {
      nodes: [
        { id: "screener", label: "Screener" },
        { id: "tech", label: "Technical Interviewer" },
        { id: "behavioral", label: "Behavioral Interviewer" },
        { id: "manager", label: "Hiring Manager" },
        { id: "auditor", label: "Bias Auditor" },
      ],
      edges: [
        { from: "screener", to: "tech" },
        { from: "tech", to: "behavioral" },
        { from: "behavioral", to: "manager" },
        { from: "manager", to: "auditor" },
      ],
    },
  },
  {
    slug: "crew-investment-analyst",
    title: "Investment Analyst Crew",
    category: "CrewAI",
    description:
      "Evaluates investment opportunities through market analysis, financial reasoning, risk review, strategic positioning, and adversarial challenge.",
    tags: ["Investment", "Risk", "Analysis"],
    highlights: [
      "Multi-perspective investment analysis",
      "Red-team adversarial review",
      "Structured memo generation",
    ],
    architecture:
      "A sequential CrewAI crew: Market Analyst → Financial Analyst → Risk Analyst → Strategist → Red Team Reviewer. Each agent builds on the previous context. The Red Team Reviewer adversarially challenges the thesis to ensure the final investment memo reflects both upside and downside reasoning.",
    features: [
      "Market landscape and competitor analysis",
      "Financial ratio and valuation assessment",
      "Dedicated risk review with mitigation suggestions",
      "Strategic positioning evaluation",
      "Adversarial red-team challenge step",
    ],
    exampleInput: '{"input": "Evaluate a Series B investment in an AI compliance automation startup"}',
    exampleOutput: '{"recommendation": "conditional_invest", "thesis": "Strong TAM with regulatory tailwinds...", "risks": ["Customer concentration", "Regulatory uncertainty"], "memo": "## Investment Memo\\n..."}',
    apiEndpoint: "/investment-crew/run",
    graph: {
      nodes: [
        { id: "market", label: "Market Analyst" },
        { id: "financial", label: "Financial Analyst" },
        { id: "risk", label: "Risk Analyst" },
        { id: "strategist", label: "Strategist" },
        { id: "redteam", label: "Red Team" },
      ],
      edges: [
        { from: "market", to: "financial" },
        { from: "financial", to: "risk" },
        { from: "risk", to: "strategist" },
        { from: "strategist", to: "redteam" },
      ],
    },
  },
  {
    slug: "crew-product-launch",
    title: "Product Launch Crew",
    category: "CrewAI",
    description:
      "Coordinates research, positioning, messaging, channel planning, and launch execution recommendations into a cohesive go-to-market plan.",
    tags: ["Product", "Go-to-Market", "Strategy"],
    highlights: [
      "End-to-end launch planning",
      "Channel-specific recommendations",
      "Coordinated agent workflow",
    ],
    architecture:
      "A sequential CrewAI crew: Market Researcher → Positioning Strategist → Messaging Writer → Channel Planner → Launch Coordinator. Each agent refines the go-to-market plan. The Launch Coordinator synthesizes all inputs into a timeline with milestones and channel-specific action items.",
    features: [
      "Market research and competitive landscape",
      "Product positioning and differentiation",
      "Messaging framework for target personas",
      "Channel-specific launch recommendations",
      "Coordinated timeline with milestones",
    ],
    exampleInput: '{"input": "Plan the launch of an AI-powered code review tool for enterprise teams"}',
    exampleOutput: '{"positioning": "AI code review for enterprise security and velocity", "channels": ["DevRel", "LinkedIn", "Product Hunt"], "timeline": "6-week phased rollout", "plan": "## Launch Plan\\n..."}',
    apiEndpoint: "/product-launch/run",
    graph: {
      nodes: [
        { id: "researcher", label: "Market Researcher" },
        { id: "positioning", label: "Positioning Strategist" },
        { id: "messaging", label: "Messaging Writer" },
        { id: "channel", label: "Channel Planner" },
        { id: "coordinator", label: "Launch Coordinator" },
      ],
      edges: [
        { from: "researcher", to: "positioning" },
        { from: "positioning", to: "messaging" },
        { from: "messaging", to: "channel" },
        { from: "channel", to: "coordinator" },
      ],
    },
  },
  {
    slug: "crew-startup-simulator",
    title: "Startup Simulator",
    category: "CrewAI",
    description:
      "Multiple functional leaders propose, select, and refine a business idea before reviewing the product, architecture, and execution plan.",
    tags: ["Startup", "Simulation", "Strategy"],
    highlights: [
      "Cross-functional decision simulation",
      "Idea selection and refinement loop",
      "Architecture and execution review",
    ],
    architecture:
      "A CrewAI crew of functional leaders: CEO → CTO → CMO → CFO → Advisor. The CEO proposes a business idea. The CTO reviews technical feasibility and architecture. The CMO evaluates market fit. The CFO models financials. The Advisor challenges the plan and suggests refinements. The crew iterates until a cohesive plan emerges.",
    features: [
      "Multi-role business idea generation",
      "Technical feasibility and architecture review",
      "Market fit evaluation",
      "Financial modeling and unit economics",
      "Advisory challenge and refinement loop",
    ],
    exampleInput: '{"input": "Simulate a startup building an AI-powered legal document assistant"}',
    exampleOutput: '{"idea": "AI legal doc assistant for SMBs", "architecture": "RAG pipeline + template engine", "market": "TAM $4.2B", "financials": {"cac": "$120", "ltv": "$1,800"}, "plan": "## Startup Plan\\n..."}',
    apiEndpoint: "/startup-simulator/run",
    graph: {
      nodes: [
        { id: "ceo", label: "CEO" },
        { id: "cto", label: "CTO" },
        { id: "cmo", label: "CMO" },
        { id: "cfo", label: "CFO" },
        { id: "advisor", label: "Advisor" },
      ],
      edges: [
        { from: "ceo", to: "cto" },
        { from: "cto", to: "cmo" },
        { from: "cmo", to: "cfo" },
        { from: "cfo", to: "advisor" },
        { from: "advisor", to: "ceo", label: "refine" },
      ],
    },
  },
];

export const projectDetails: ProjectDetail[] = rawProjectDetails.map(
  ({ title, ...project }) => ({
    ...project,
    name: title,
  }),
);

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

export function getProjectsByCategory(category: Category): Project[] {
  return projects.filter((p) => p.category === category);
}
