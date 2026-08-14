# Graph Report - genai-systems-lab  (2026-08-14)

## Corpus Check
- 994 files · ~1,366,389 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3165 nodes · 5821 edges · 259 communities (197 shown, 62 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 463 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f192a274`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LLM Provider Runtime
- Startup Simulator Crew
- Playground State Utilities
- Shared API Schemas
- Persistence Models
- Data Agent Workflow
- Model Instrumentation Dependencies
- BYOK Project Entrypoints
- API Response Models
- Portfolio API Client
- Shared API Tests
- Knowledge OS Storage
- Code Copilot Indexing
- Playground Project UI
- Frontend Package Dependencies
- Auth Persistence Services
- Project Catalog Tests
- Support Agent Workflow
- Interview Session Runtime
- Data Analyst Workflow
- Timeline Comparison UI
- Evaluation Runtime
- Runtime Configuration Jobs
- Cross Project Documentation
- Browser Agent Runtime
- Debugging Agent Workflow
- UA Architecture Analysis
- Structured Logging
- Hiring Crew Tasks
- TypeScript Configuration
- Document Intelligence Runtime
- Portfolio App Shell
- Metrics Dashboard
- Financial Analyst Runtime
- Frontend Authentication
- Shared Cache Layer
- Research System Graph
- Project Catalog UI
- Workflow Agent Graph
- Shared Project Runner
- JWT Authentication Tests
- Dataframe Core Tests
- Code Execution Tests
- Graph Visualization UI
- Langfuse Observability
- Investment Crew
- Content Pipeline Crew
- Product Launch Crew
- Runner Cache Tests
- OpenTelemetry Instrumentation
- CI Security Tests
- Promptfoo RAG Providers
- NL2SQL Execution
- Research Orchestration
- UI Builder Runtime
- Evaluation Metrics
- Interview Voice IO
- UI Code Generation
- Session Memory
- LLM Telemetry Tests
- Clinical Planning
- Clinical Assistant Runtime
- Document Retrieval
- Research Evaluation
- Plan Parsing Tests
- Confidence Scoring
- Shared Utilities
- Docker Security Tests
- UI Preview Server
- Run Detail UI
- Data Visualization
- Agent Graph UI
- Code Embeddings
- Clinical Retrieval
- NL2SQL Agent Runtime
- Research Service API
- Project Contract Tests
- Portfolio Marketing Pages
- UA Batch Analysis
- Architecture Documentation
- Knowledge Retrieval
- Analyst Executor Agent
- Dataframe Loading Tests
- Run Explanation
- SQLite Pragma Tests
- Analyst FastAPI
- Knowledge Graph Store
- Auth Hardening Tests
- UA Assigned Analysis
- Research Clients
- Observability Performance Tests
- UA Layer Assignment
- Analyst Settings
- Workflow Analysis Tool
- Parallel Critic Node
- Parallel Researcher Node
- UI Builder Documentation
- Portfolio Architecture UI
- UA Batch Complexity
- NL2SQL Documentation
- Benchmark Datasets
- Content Crew Documentation
- Document Corpus Samples
- Evaluation Runner
- NL2SQL Security Tests
- Copilot Context Assembly
- Document Chunking
- Document Embeddings
- Data Agent Charts
- Database Initialization
- Production Stack Security
- Financial Analysis Docs
- Research Writer Node
- Research Planner
- Research Revision Docs
- Next Security Configuration
- Crew Comparison Docs
- Copilot QA Agent
- Grounded Document QA
- Interview Evaluation Docs
- Workflow File Tool
- RAG Evaluation Docs
- Incident Corpus Samples
- Security Policy Corpus
- Data Agent Docs
- Support Agent Docs
- Workflow Agent Docs
- SQLite Data Directory
- Copilot Retrieval Docs
- Financial Metrics Docs
- Interview Session Docs
- Knowledge Search Docs
- NL2SQL Package
- Research Package
- Research System Docs
- Analyst Agent Package
- Analyst API Package
- Analyst Config Package
- Analyst Graph Package
- Analyst Source Package
- Analyst LLM Package
- Analyst Schema Package
- Analyst Tools Package
- ESLint Configuration
- PostCSS Configuration
- UA Inline Validation
- UA Tour Analysis
- Agent Evaluation Dataset
- Red Team Dataset
- Community Conduct
- Codex Task Review
- Product Launch Docs
- Browser Agent Docs
- Clinical Assistant Docs
- Copilot Documentation
- Document Architecture Docs
- Document Intelligence Docs
- Document Intelligence Tasks
- Financial Architecture Docs
- Financial Analyst Readme
- Financial Pipeline Docs
- Financial Analyst Tasks
- Interviewer Architecture Docs
- Adaptive Interview Loop
- Interviewer Documentation
- Interviewer Tasks
- Answer Evaluation Docs
- Knowledge Architecture Docs
- AI Ops Retrospective
- Research Roadmap
- Vendor Evaluation
- Northstar Search
- Learning Log
- Knowledge OS Readme
- Knowledge OS Documentation
- Knowledge OS Tasks
- Memory Storage Docs
- Debugging Workflow Docs
- Debugging Agent Tasks
- Project Configuration
- Playground Usage Guide
- analyze-my-batches.mjs
- dependencies.py
- eval_runner.py
- BenchmarkSuite
- ua-assign-layers.js
- Changelog
- knowledge_base.py
- Tasks
- VectorStore
- Architecture
- Tasks
- Debugging Agent
- _ContextFilter
- otel.py
- project_catalog.py
- test_dependency_security_contract.py
- generate-group2.mjs
- Tasks
- Tasks
- retriever.py
- fixer_node
- run
- assemble-scan-result.cjs
- ua-assemble-final.cjs
- Investment Analysis Crew
- get_logger
- Observe Plan Act Loop
- Research Graph
- Peer Review Round
- Production Design Notes
- retrieve
- sql_generator.py
- Product Launch Strategy Crew
- Agents
- ua-build-fingerprint-input.cjs
- ua-tour-analyze.js
- ResearchState
- ua-fix-invalid-nodes.cjs
- ua-write-meta.cjs
- architecture.md
- tasks.md
- ua-arch-analyze.js
- ua-inline-validate.cjs
- ua-tour-prepare.js

## God Nodes (most connected - your core abstractions)
1. `set_byok_api_key()` - 53 edges
2. `reset_byok_api_key()` - 53 edges
3. `create_app()` - 52 edges
4. `generate_text()` - 46 edges
5. `generate_structured()` - 38 edges
6. `LLMGenerationError` - 34 edges
7. `_get_client()` - 28 edges
8. `run_project()` - 26 edges
9. `generate_structured()` - 26 edges
10. `emit_step()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Retrieval Quality` --semantically_similar_to--> `Retriever`  [INFERRED] [semantically similar]
  genai-knowledge-os/data/notes/ai-ops-retrospective.md → genai-code-copilot/architecture.md
- `Investment Analysis Crew` --semantically_similar_to--> `Product Launch Strategy Crew`  [INFERRED] [semantically similar]
  crew-investment-analyst/architecture.md → crew-product-launch/architecture.md
- `Product Launch Strategy Crew` --semantically_similar_to--> `Startup Team Simulator`  [INFERRED] [semantically similar]
  crew-product-launch/architecture.md → crew-startup-simulator/architecture.md
- `Bring Your Own Key` --semantically_similar_to--> `BYOK handling`  [INFERRED] [semantically similar]
  README.md → SECURITY.md
- `Hybrid Retrieval` --semantically_similar_to--> `Retriever`  [INFERRED] [semantically similar]
  genai-knowledge-os/data/notes/personal-research-roadmap.md → genai-code-copilot/architecture.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Content Pipeline Refinement Flow** — crew_content_pipeline_architecture_researcher, crew_content_pipeline_architecture_writer, crew_content_pipeline_architecture_editor, crew_content_pipeline_architecture_seo_expert [EXTRACTED 1.00]
- **Sequential Crew Designs** — crew_hiring_system_architecture_hiring_decision_crew, crew_investment_analyst_architecture_investment_analysis_crew, crew_product_launch_architecture_product_launch_crew, crew_startup_simulator_architecture_startup_team_simulator [INFERRED 0.95]
- **Structured Output Contracts** — crew_hiring_system_tasks_json_schemas, crew_product_launch_tasks_structured_strategy_schemas, crew_startup_simulator_architecture_peer_review_round [INFERRED 0.85]
- **Traceable AI Workflows** — genai_browser_agent_architecture_browser_memory, genai_code_copilot_architecture_traceable_chunk_metadata, genai_clinical_assistant_tasks_clinical_guideline_retrieval [INFERRED 0.75]
- **Financial Analysis Pipeline** — genai_financial_analyst_architecture_data_loader, genai_financial_analyst_architecture_metrics_engine, genai_financial_analyst_architecture_analyzer, genai_financial_analyst_architecture_reporter [EXTRACTED 1.00]
- **Personal Knowledge OS Processing Pipeline** — genai_knowledge_os_architecture_ingestion_pipeline, genai_code_copilot_architecture_vector_store, genai_code_copilot_architecture_retriever, genai_knowledge_os_architecture_summarizer, genai_knowledge_os_architecture_insight_engine [EXTRACTED 1.00]
- **NL2SQL Safe Query Pipeline** — genai_nl2sql_agent_architecture_schema_loader, genai_nl2sql_agent_architecture_sql_generator, genai_nl2sql_agent_architecture_sql_validator, genai_nl2sql_agent_architecture_query_executor, genai_nl2sql_agent_architecture_result_summarizer [EXTRACTED 1.00]
- **Research Revision Workflow** — genai_research_system_architecture_planner, genai_research_system_architecture_researcher, genai_research_system_architecture_critic, genai_research_system_architecture_writer [EXTRACTED 1.00]
- **Compose Persistence and Queue Services** — docker_compose_production_stack, docker_compose_postgresql, docker_compose_redis_rq_worker [EXTRACTED 1.00]

## Communities (259 total, 62 thin omitted)

### Community 0 - "LLM Provider Runtime"
Cohesion: 0.13
Nodes (48): get_effective_api_key(), get_request_effort(), Return the request-scoped reasoning effort override, if present., Return the per-request BYOK key from the ``x-api-key`` header.      Raises ``R, ollama_base_url(), LLMGenerationError, RuntimeError, Raised when a provider request fails. (+40 more)

### Community 1 - "Startup Simulator Crew"
Cohesion: 0.06
Nodes (51): build_ceo(), build_cto(), build_engineer(), build_product_manager(), Agent, Agent definitions for the Startup Team Simulator., build_crew(), Crew (+43 more)

### Community 2 - "Playground State Utilities"
Cohesion: 0.11
Nodes (36): ErrorDisplay(), PlaygroundConversationPanel(), PlaygroundConversationPanelProps, PlaygroundGraphPanel(), PlaygroundGraphPanelProps, ChevronIcon(), assistantCardTone(), assistantStateTitle() (+28 more)

### Community 3 - "Shared API Schemas"
Cohesion: 0.07
Nodes (60): create_app(), Create a pre-configured FastAPI instance.      Projects create their own ``Fas, AuthConfigResponse, AuthRequest, AuthResponse, AuthUserResponse, BaseRequest, BaseResponse (+52 more)

### Community 4 - "Persistence Models"
Cohesion: 0.08
Nodes (37): BaseHTTPMiddleware, DeclarativeBase, BYOKMiddleware, ErrorHandlingMiddleware, InputValidationMiddleware, _MetricsStore, Request, Log every incoming request and its response status. (+29 more)

### Community 5 - "Data Agent Workflow"
Cohesion: 0.07
Nodes (45): get_metadata(), load_data(), _load_sample(), DataFrame, Load a dataset from file or return built-in sample data., Return column names, dtypes, shape, and a small sample (max 3 rows)., build_graph(), LangGraph workflow: planner → executor → analyzer → evaluator (with retry loop). (+37 more)

### Community 6 - "Model Instrumentation Dependencies"
Cohesion: 0.14
Nodes (17): build_graph(), critic_node(), ResearchState, planner_node(), ResearchState, ResearchState, researcher_node(), ResearchState (+9 more)

### Community 7 - "BYOK Project Entrypoints"
Cohesion: 0.08
Nodes (33): Execution entry point for the Content Creation Pipeline., Run the content creation pipeline and return structured output., run(), _parse_json(), Execution entry point for the Hiring Decision Crew., Run candidate evaluation on resume text and return structured output., run(), _parse_json() (+25 more)

### Community 8 - "API Response Models"
Cohesion: 0.07
Nodes (45): datetime, MemoryEntryPayload, MetricsResponse, ProviderId, Response, _append_execution_trace(), _append_fallback_memory_entries(), _append_fallback_timeline_entries() (+37 more)

### Community 9 - "Portfolio API Client"
Cohesion: 0.07
Nodes (39): AuthClient(), Mode, metadata, loadMetrics(), ProjectRunBadge(), apiBaseCandidates(), apiFetch(), AuthConfigResponse (+31 more)

### Community 10 - "Shared API Tests"
Cohesion: 0.10
Nodes (44): RunResult, TestClient, client(), _extract_done_event(), MonkeyPatch, The SSE stream must not pretend to stream tokens.      Earlier revisions slice, Leaderboard feature was removed entirely — no dedicated route should exist., Streamlit UI surface was removed — no route prefix should exist. (+36 more)

### Community 11 - "Knowledge OS Storage"
Cohesion: 0.22
Nodes (6): batch_embeddings(), _embed_batch(), generate_embedding(), Exception, _should_retry(), KnowledgeMemory

### Community 12 - "Code Copilot Indexing"
Cohesion: 0.08
Nodes (50): AST, EmbedContentResponse, _embed_batch(), EmbeddingGenerationError, _extract_embedding_values(), generate_embedding(), generate_embeddings_batch(), _normalize_text() (+42 more)

### Community 13 - "Playground Project UI"
Cohesion: 0.09
Nodes (47): ModelComparePage(), PlaygroundClient(), ConfirmRequest, PlaygroundSidebar(), PlaygroundSidebarProps, sortedProjects(), useConfirmModal(), buildReplayLogLines() (+39 more)

### Community 14 - "Frontend Package Dependencies"
Cohesion: 0.05
Nodes (39): eslint, eslint-config-next, next, next-themes, dependencies, next, next-themes, react (+31 more)

### Community 15 - "Auth Persistence Services"
Cohesion: 0.08
Nodes (34): FastAPI, HTTPAuthorizationCredentials, _allowed_jwt_algorithms(), authenticate_user(), _b64url_decode(), _b64url_encode(), create_user(), _deserialize_memory_entries() (+26 more)

### Community 16 - "Project Catalog Tests"
Cohesion: 0.12
Nodes (29): _discover_projects(), Return a list of runnable projects (folders containing app/main.py)., list_available(), _project_aliases(), Return projects that may be executed through the shared runner., Resolve canonical and legacy project names to a runnable project folder., Derive API-name → folder-slug mapping from the catalog plus legacy route aliases, resolve_project_name() (+21 more)

### Community 17 - "Support Agent Workflow"
Cohesion: 0.13
Nodes (19): build_graph(), _route_after_evaluator(), _build_prompt(), classifier_node(), _format_history(), _build_prompt(), escalation_node(), _format_history() (+11 more)

### Community 18 - "Interview Session Runtime"
Cohesion: 0.08
Nodes (23): adjust_difficulty(), Adjust interview difficulty based on candidate performance., generate_feedback(), Generate candidate-facing feedback using Gemini., _get_answer_text(), _get_logger(), _load_voice(), _present_text() (+15 more)

### Community 19 - "Data Analyst Workflow"
Cohesion: 0.05
Nodes (43): execute_plan(), _extract_code(), Executor agent node — converts the analysis plan into runnable code and executes, Strip markdown fences if present and return clean Python code., Convert the analysis plan into Python code, execute it, and capture results., _parse_plan(), plan_analysis(), Planner agent node — creates a structured, executable analysis plan.  The plan (+35 more)

### Community 20 - "Timeline Comparison UI"
Cohesion: 0.11
Nodes (21): DismissibleTip(), entryBadgeTone(), entryIconTone(), entryTypeLabel(), joinClasses(), MemoryEntryType, MemoryPanel(), MemoryPanelProps (+13 more)

### Community 21 - "Evaluation Runtime"
Cohesion: 0.14
Nodes (13): _contains_all(), _contains_any(), _is_valid_json(), list_projects(), _matches(), _min_length(), Benchmark datasets and runner for all 20 projects.  Each project has a list of, True if *output* contains at least one of *terms* (case-insensitive). (+5 more)

### Community 22 - "Runtime Configuration Jobs"
Cohesion: 0.07
Nodes (57): call_api(), _ensure_indexed(), _index_state(), _normalize_chunks(), Any, call_api(), _ensure_indexed(), _index_state() (+49 more)

### Community 23 - "Cross Project Documentation"
Cohesion: 0.25
Nodes (8): Investment Recommendation, Market Financial Risk Analysis, Clinical Assistant Pipeline, Clinical Guideline Retrieval, Clinical Risk Scoring, Code Retrieval Pipeline, Codebase Copilot, Code Copilot Implementation Checklist

### Community 24 - "Browser Agent Runtime"
Cohesion: 0.10
Nodes (11): execute(), run_agent(), BrowserController, BrowserMemory, _clean(), get_observation(), _get_text_observation(), _get_vision_observation() (+3 more)

### Community 25 - "Debugging Agent Workflow"
Cohesion: 0.12
Nodes (21): build_graph(), route_after_evaluator(), analyzer_node(), _build_prompt(), _build_prompt(), _extract_code(), test_generator_node(), evaluator_node() (+13 more)

### Community 26 - "UA Architecture Analysis"
Cohesion: 0.06
Nodes (28): allEdges, byId, cross, crossCategoryEdges, dataPipeline, dependencyDirection, directoryGroups, docCoverage (+20 more)

### Community 27 - "Structured Logging"
Cohesion: 0.24
Nodes (10): Shared structured logging., LatencyTimer, log_context(), new_request_id(), Any, Token, Centralised structured logging with request and project context.  Features --, Convenience context-manager that records elapsed ms into log context.      Usa (+2 more)

### Community 28 - "Hiring Crew Tasks"
Cohesion: 0.14
Nodes (27): build_behavioral_interviewer(), build_bias_auditor(), build_comparative_analyst(), build_hiring_manager(), build_resume_screener(), build_technical_interviewer(), Agent, Agent definitions for the Hiring Decision Crew. (+19 more)

### Community 29 - "TypeScript Configuration"
Cohesion: 0.07
Nodes (29): compilerOptions, allowJs, baseUrl, esModuleInterop, incremental, isolatedModules, jsx, lib (+21 more)

### Community 30 - "Document Intelligence Runtime"
Cohesion: 0.09
Nodes (20): Run codebase Q&A and return structured output.  	Input format: ``<codebase_pat, run(), attach_citations(), query(), Run a document query and return structured output., run(), Execution entry point for the AI Interviewer., Run a non-interactive interview session and return structured output.      The (+12 more)

### Community 31 - "Portfolio App Shell"
Cohesion: 0.09
Nodes (17): manrope, metadata, plexMono, metadata, ThemeProvider(), HelpReset(), SUPPRESS_KEYS, allLinks (+9 more)

### Community 32 - "Metrics Dashboard"
Cohesion: 0.11
Nodes (25): average(), bucketLabels(), buildChartSeries(), buildTrendSummary(), ChartPoint, describeLatencyDelta(), describePointDelta(), downloadBlob() (+17 more)

### Community 33 - "Financial Analyst Runtime"
Cohesion: 0.18
Nodes (8): load_data(), DataFrame, forecast(), DataFrame, Run financial analysis and return structured output.      Input format: ``<csv, run(), compute_metrics(), DataFrame

### Community 34 - "Frontend Authentication"
Cohesion: 0.33
Nodes (10): isRunMemoryEntry(), isRunTimelineEntry(), usePlaygroundAccount(), clearRunSession(), fetchHistory(), fetchRunSession(), clearAuthSession(), clearStoredSessionId() (+2 more)

### Community 35 - "Shared Cache Layer"
Cohesion: 0.12
Nodes (16): Cache, cached_embedding(), cached_llm_call(), get_embedding_cache(), get_llm_cache(), _hash_key(), Any, In-memory prompt-keyed cache for LLM responses and embeddings. (+8 more)

### Community 36 - "Research System Graph"
Cohesion: 0.16
Nodes (12): build_graph(), _instrument_node(), ResearchState, StateGraph, route_after_critic(), route_after_editor(), route_after_originality(), formatter_node() (+4 more)

### Community 37 - "Project Catalog UI"
Cohesion: 0.11
Nodes (14): comparisonRows, metadata, overviewCards, projectMap, repoExamples, groups, metadata, ProjectCardPreview() (+6 more)

### Community 38 - "Workflow Agent Graph"
Cohesion: 0.12
Nodes (17): build_graph(), _route_after_checkpoint(), checkpoint_node(), load_checkpoint(), Load a previously saved state from disk.      Returns ``None`` if the file doe, Persist current state to disk and advance to the next step.      If validation, _build_prompt(), executor_node() (+9 more)

### Community 39 - "Shared Project Runner"
Cohesion: 0.11
Nodes (25): ModuleNotFoundError, _clear_project_imports(), _ensure_import_paths(), _fire_and_forget_langfuse_flush(), _is_dev_mode(), _langfuse_flush_worker(), _load_main(), _optional_dependency_error() (+17 more)

### Community 40 - "JWT Authentication Tests"
Cohesion: 0.16
Nodes (27): AuthError, create_access_token(), decode_access_token(), get_current_user(), get_optional_current_user(), Exception, Session, Create a signed JWT for the authenticated user.      Uses PyJWT with a hardcod (+19 more)

### Community 41 - "Dataframe Core Tests"
Cohesion: 0.06
Nodes (23): get_basic_info(), get_summary_stats(), load_dataframe(), profile_dataset(), DataFrame, Path, DataFrame loading and profiling utilities.  Supports CSV and Excel files.  Pro, Generate a text profile of *df* (legacy helper).      Combines :func:`get_basi (+15 more)

### Community 42 - "Code Execution Tests"
Cohesion: 0.13
Nodes (34): get_effective_model(), get_request_provider(), Return the request-scoped provider override, if present., Return the request-scoped model override, or the provided fallback., gemini_embedding_model(), CompatClient, CompatEmbedContentResponse, CompatEmbedding (+26 more)

### Community 43 - "Graph Visualization UI"
Cohesion: 0.10
Nodes (28): categoryAccent, categoryDiagramAccent, formatJson(), generateMetadata(), ProjectDetailPage(), Props, AnimatedGraph(), AnimatedGraphProps (+20 more)

### Community 44 - "Langfuse Observability"
Cohesion: 0.23
Nodes (20): _score_langfuse_confidence(), Shared observability layer for production LLM monitoring.  Currently integrate, _base_url(), create_trace(), _credentials_present(), _ensure_client(), flush(), get_client() (+12 more)

### Community 45 - "Investment Crew"
Cohesion: 0.19
Nodes (18): build_financial_analyst(), build_market_analyst(), build_risk_analyst(), build_strategist(), Agent, Agent definitions for the Investment Analysis Crew., build_crew(), Crew (+10 more)

### Community 46 - "Content Pipeline Crew"
Cohesion: 0.18
Nodes (17): build_editor(), build_researcher(), build_seo_expert(), build_writer(), Agent, Agent definitions for the Content Creation Pipeline., build_crew(), Crew (+9 more)

### Community 47 - "Product Launch Crew"
Cohesion: 0.18
Nodes (17): build_customer_analyst(), build_market_researcher(), build_marketing_strategist(), build_product_strategist(), Agent, Agent definitions for the Product Launch Strategy Crew., build_crew(), Crew (+9 more)

### Community 48 - "Runner Cache Tests"
Cohesion: 0.15
Nodes (16): MonkeyPatch, Regression tests for ``shared.api.runner._MODULE_CACHE``.  The audit flagged `, Prod mode must never reload once a project has been imported., The cross-thread mutation guards must be actual locks, not no-ops., Concurrent ``_load_main`` calls must not raise and must leave a stable cache., Clear the module cache before and after each test for isolation., Pick a real project whose ``app/main.py`` imports cleanly in this env.      Ma, Two consecutive loads of the same project must reuse the cached module. (+8 more)

### Community 49 - "OpenTelemetry Instrumentation"
Cohesion: 0.22
Nodes (9): get_tracer(), _NoopSpan, _NoopTracer, Any, BaseException, Return an OTel ``Tracer`` (or a no-op stub)., Start a traced span.  Falls back to a no-op context when OTel is absent., Minimal stand-in when OTel is not installed. (+1 more)

### Community 50 - "CI Security Tests"
Cohesion: 0.11
Nodes (7): Regression tests for the CI security / dependency contract.  The audit flagged, ``langgraph-data-analyst/`` has its own requirements.txt — Dependabot     must, ``pip-audit`` must not be annotated with ``continue-on-error: true``., Trivy image scan must have ``exit-code: \"1\"`` so CVEs fail the job., test_ci_blocks_on_pip_audit_findings(), test_ci_blocks_on_trivy_findings(), test_dependabot_covers_standalone_analyst()

### Community 51 - "Promptfoo RAG Providers"
Cohesion: 0.06
Nodes (32): Architecture, Authentication & Sessions, CrewAI Teams (5), Design System, Development, Environment, Features, Full Usage Guide (+24 more)

### Community 52 - "NL2SQL Execution"
Cohesion: 0.15
Nodes (15): execute_sql(), DataFrame, SQL execution module., _create_tables(), get_connection(), get_schema_description(), _initialize_database(), DuckDBPyConnection (+7 more)

### Community 53 - "Research Orchestration"
Cohesion: 0.15
Nodes (15): _build_prompt(), critique(), Critique utilities for reviewing research outputs., Shared memory for the multi-agent research workflow., ResearchMemory, _build_context(), _needs_improvement(), _process_task() (+7 more)

### Community 54 - "UI Builder Runtime"
Cohesion: 0.17
Nodes (12): build(), Execution entry point for the Generative UI Builder., Run the full pipeline: generate spec, validate, generate code, fix if needed., Run the UI generation pipeline and return structured output., run(), generate_spec(), Generate a structured UI spec from a natural-language prompt., Convert a natural-language UI description into a validated JSON UI spec. (+4 more)

### Community 55 - "Evaluation Metrics"
Cohesion: 0.24
Nodes (9): Shared evaluation framework for LLM-powered projects., Any, Asyncio-based stress testing for throughput and error-rate analysis., Thin wrapper that calls ``run_stress_test`` from synchronous code.      Usage:, Aggregate output from a stress test run., Simulate *total* concurrent calls to *task_fn* and return metrics.      ``task, run_stress_test(), StressResult (+1 more)

### Community 56 - "Interview Voice IO"
Cohesion: 0.16
Nodes (17): _extract_audio_bytes(), _frames_to_wav(), listen(), _play_wav_bytes(), Voice I/O for the AI Interviewer using Gemini TTS/STT.  Requires optional depe, Record from microphone until silence, then transcribe with Gemini., Record audio chunks until sustained silence is detected., Convert recorded numpy frames to WAV bytes. (+9 more)

### Community 57 - "UI Code Generation"
Cohesion: 0.18
Nodes (16): _camel_to_kebab(), _collect_component_names(), generate_files(), generate_react_code(), Generate React component code from a validated UI spec., Convert a validated UI spec into a dict of {filename: content} pairs.      Alw, Render top-level shared styles as a CSS stylesheet string., Convert a validated UI spec into a single React component string.      Kept fo (+8 more)

### Community 58 - "Session Memory"
Cohesion: 0.24
Nodes (13): Any, _serialize_session_payload(), _build_interaction_entry(), build_session_prompt(), _dedupe_key(), deserialize_session_memory_entries(), _normalize_whitespace(), preview_session_memory_entries() (+5 more)

### Community 59 - "LLM Telemetry Tests"
Cohesion: 0.22
Nodes (19): calculate_model_cost(), estimate_model_cost(), begin_llm_run(), consume_llm_call_metadata(), consume_llm_run_usage(), Any, record_llm_call_metadata(), record_llm_run_call() (+11 more)

### Community 60 - "Clinical Planning"
Cohesion: 0.10
Nodes (25): extract_patient_info(), Extract structured patient information from free-text input., analyze_conditions(), _format_conditions(), _format_patient(), Analyze candidate conditions against patient info using LLM reasoning., extract_key_information(), extract() (+17 more)

### Community 61 - "Clinical Assistant Runtime"
Cohesion: 0.23
Nodes (10): _merge_reasoning_and_confidence(), Application entry point for the clinical decision support pipeline., Combine reasoning from the LLM with confidence from the deterministic scorer., Run the clinical decision support pipeline and return structured output., run(), assign_confidence(), _compute_confidence(), _label_from_confidence() (+2 more)

### Community 62 - "Document Retrieval"
Cohesion: 0.24
Nodes (3): _cosine_similarity(), ndarray, VectorStore

### Community 63 - "Research Evaluation"
Cohesion: 0.19
Nodes (14): aggregate_quality_metrics(), collect_research_metrics(), Any, _contains_keywords(), Any, Project-local evaluation runner for genai-research-system.  This module uses t, Run the project evaluation with an explicitly bound API key., Run the flagship research workflow and return the structured response. (+6 more)

### Community 64 - "Plan Parsing Tests"
Cohesion: 0.07
Nodes (29): 1. Task Input, 2. Browser Initialization, 3. Observation, 4. Planning, 5. Action Execution, 6. Memory Update, 7. Loop Continuation, 8. Result Extraction (+21 more)

### Community 65 - "Confidence Scoring"
Cohesion: 0.28
Nodes (15): _clamp01(), _collect_evaluator_candidates(), _compute_evaluator_score(), compute_run_confidence(), _extract_output_retries(), _extract_timeline_retries(), _has_meaningful_value(), _infer_retry_count() (+7 more)

### Community 66 - "Shared Utilities"
Cohesion: 0.15
Nodes (11): chunk_text(), Any, BaseException, Generic helper functions reusable across all projects., Split *text* into overlapping chunks of up to *max_chars* characters.      Tri, Decorator that retries a function with exponential backoff.      Usage::, Context-manager for timing blocks of code.      Usage::          with Timer(, retry() (+3 more)

### Community 67 - "Docker Security Tests"
Cohesion: 0.15
Nodes (10): _active_lines(), Regression tests for Dockerfile secret-handling and project-copy correctness., Every runnable project must land under ``/app/<slug>/``, not ``/app``., Strip comments and blank lines — we only care about live directives., Historical bug: ``COPY crew-*/ ./`` merges every project's files into /app., test_dockerfile_copies_each_project_into_its_own_subdir(), test_dockerfile_does_not_flatten_projects_via_globs(), test_dockerignore_excludes_env_files() (+2 more)

### Community 68 - "UI Preview Server"
Cohesion: 0.17
Nodes (12): build_preview_html(), _css_to_style_block(), _PreviewHandler, Local preview server for generated React components.  Uses Python's built-in h, Serves the preview HTML on GET /., Start a local HTTP server to preview the generated UI., Remove import/export statements for inline use., Indent CSS for embedding inside a <style> tag. (+4 more)

### Community 69 - "Run Detail UI"
Cohesion: 0.18
Nodes (10): formatTimestamp(), SharedRunPage(), clampConfidence(), ConfidenceIndicator(), ConfidenceIndicatorProps, confidenceTone(), fetchSharedRun(), RunMemoryEntry (+2 more)

### Community 70 - "Data Visualization"
Cohesion: 0.20
Nodes (13): apply_default_style(), _check_plot_code(), generate_plot(), generate_summary_charts(), DataFrame, Path, Visualization utilities for chart generation and figure management.  Provides, Persist every currently open *matplotlib* figure to disk.      Args: (+5 more)

### Community 71 - "Agent Graph UI"
Cohesion: 0.16
Nodes (13): AgentGraph(), AgentGraphProps, AgentGraphStep, agentGraphSteps, EDGE_STYLES, EDGES, EdgeVisualState, getEdgeVisualState() (+5 more)

### Community 72 - "Code Embeddings"
Cohesion: 0.08
Nodes (24): Agents, Architecture, Behavioral Interviewer, behavioral_task, Configuration, Cost and latency considerations, Crew Configuration, Data Flow (+16 more)

### Community 73 - "Clinical Retrieval"
Cohesion: 0.22
Nodes (11): get_all_conditions(), Return all conditions in the knowledge base., _build_embedding_index(), _cosine_similarity(), _embed_texts(), Embed a list of texts in a single API call., Embed patient symptoms and all condition symptoms in one batch API call., Score a condition by averaging the best similarity each patient symptom achieves (+3 more)

### Community 74 - "NL2SQL Agent Runtime"
Cohesion: 0.19
Nodes (10): _build_summary_prompt(), Any, DataFrame, Agent orchestration module., Run the NL-to-SQL pipeline, emitting real step events as each stage executes., run_agent(), _load_run_agent(), Application entry point.  Step events (``emit_step``) are now emitted from ins (+2 more)

### Community 75 - "Research Service API"
Cohesion: 0.23
Nodes (11): BaseModel, ResearchRunRequest, ResearchRunResponse, run_research(), Execution entry point for the multi-agent research workflow., Run the multi-agent research workflow and return structured output., run(), normalize_formats() (+3 more)

### Community 76 - "Project Contract Tests"
Cohesion: 0.21
Nodes (11): ModuleType, _all_projects(), _load_main_module(), Contract-level smoke tests for every runnable project.  Every project under th, ``run(input, api_key=..., [step_emitter=...], **)`` — exact runner contract., Contract: ``run`` should annotate a ``dict``/``dict[...]`` return type when anno, All project directories whose ``app/main.py`` file exists., Import ``<project>/app/main.py`` in isolation.      Clones the runner's loader (+3 more)

### Community 77 - "Portfolio Marketing Pages"
Cohesion: 0.19
Nodes (8): metadata, skills, capabilities, highlights, stats, Card(), CardProps, joinClasses()

### Community 78 - "UA Batch Analysis"
Cohesion: 0.21
Nodes (9): batches, complexity(), fnSummary(), idFor(), nodeForClass(), nodeForFunction(), root, typeFor() (+1 more)

### Community 79 - "Architecture Documentation"
Cohesion: 0.09
Nodes (22): Evaluation-First Design, LLM Wrapper, Shared Layer, System Architecture, PostgreSQL, Production Compose Stack, Redis RQ Worker, Dependency Update Automation (+14 more)

### Community 80 - "Knowledge Retrieval"
Cohesion: 0.05
Nodes (41): Architecture, Chunking System, Component Architecture, Context Builder, Core Features, Developer Question Answering, Embedding Generation, Embedding Generator (+33 more)

### Community 81 - "Analyst Executor Agent"
Cohesion: 0.16
Nodes (22): AnyObj, formatLogTimestamp(), inferLifecycleStep(), inferMemoryEntryType(), mapRunMemoryEntries(), matchesLifecycleKeyword(), memoryContentForStep(), projectApiName() (+14 more)

### Community 82 - "Dataframe Loading Tests"
Cohesion: 0.23
Nodes (21): GenerateContentConfig, GenerateContentResponse, LLMTimeoutError, Raised when a provider request exceeds the timeout budget., generate_structured(), generate_text(), generate_text_from_image(), _get_client() (+13 more)

### Community 83 - "Run Explanation"
Cohesion: 0.32
Nodes (11): build_run_explanation(), _format_input(), _format_memory(), _format_output(), _format_timeline(), Any, Helpers for generating explainability summaries for saved runs., Generate a concise structured explanation for one saved run.      User-control (+3 more)

### Community 84 - "SQLite Pragma Tests"
Cohesion: 0.35
Nodes (11): _make_file_engine(), Path, Regression tests for SQLite connection-level pragmas.  The audit flagged missi, Create a fresh file-backed SQLite engine wired to the same listener., End-to-end sanity: with FK enforcement ON, an invalid insert fails., test_busy_timeout_is_at_least_five_seconds(), test_foreign_key_violation_is_rejected(), test_foreign_keys_are_enforced() (+3 more)

### Community 85 - "Analyst FastAPI"
Cohesion: 0.33
Nodes (8): analyze(), AnalyzeRequest, AnalyzeResponse, BaseModel, FastAPI application for the LangGraph Data Analyst service., Run the LangGraph analysis workflow and return the final report., Invoke the LangGraph workflow. Runs synchronously inside the event loop., _run_workflow()

### Community 87 - "Auth Hardening Tests"
Cohesion: 0.38
Nodes (10): LogCaptureFixture, _load_jwt_secret(), MonkeyPatch, Tests for auth secret hardening — minimum length, prod enforcement, ephemeral fa, test_minimum_length_jwt_secret_is_accepted(), test_missing_secret_in_dev_logs_ephemeral_warning(), test_missing_secret_in_dev_returns_ephemeral(), test_missing_secret_in_prod_raises() (+2 more)

### Community 88 - "UA Assigned Analysis"
Cohesion: 0.22
Nodes (7): all, batches, classNode(), complexity(), functionNode(), root, ua

### Community 89 - "Research Clients"
Cohesion: 0.27
Nodes (9): _build_prompt(), create_plan(), _parse_tasks(), Planning utilities for research task generation., _build_prompt(), Research execution utilities., research_task(), _get_client() (+1 more)

### Community 90 - "Observability Performance Tests"
Cohesion: 0.27
Nodes (7): _Client, _Observation, Any, MonkeyPatch, Performance contracts for shared observability., Trace completion must leave network delivery to the runner worker., test_trace_context_does_not_flush_synchronously()

### Community 91 - "UA Layer Assignment"
Cohesion: 0.20
Nodes (8): byLayer, fileTypes, fs, graph, [graphPath, outputPath], ids, layers, result

### Community 92 - "Analyst Settings"
Cohesion: 0.22
Nodes (8): BaseSettings, ensure_directories(), Application configuration and structured logging setup.  All settings are load, Centralised application settings.      Values are read from environment variab, Configure application-wide logging with a structured formatter.      Idempoten, Create the upload and output directories if they don't yet exist., Settings, setup_logging()

### Community 93 - "Workflow Analysis Tool"
Cohesion: 0.61
Nodes (8): _average(), _group_by(), _min_max(), _numeric_values(), _parse_csv(), run(), _summarize(), _trends()

### Community 94 - "Parallel Critic Node"
Cohesion: 0.10
Nodes (19): Agents, Architecture, Cost and latency considerations, Crew Configuration, Data Flow, Error Handling, Extension Points, Financial Analyst (+11 more)

### Community 95 - "Parallel Researcher Node"
Cohesion: 0.10
Nodes (23): _format_condition_block(), format_output(), Format analyzed conditions into a human-readable clinical summary., answer_query(), _build_prompt(), analyze_metrics(), DataFrame, generate_report() (+15 more)

### Community 96 - "UI Builder Documentation"
Cohesion: 0.29
Nodes (8): Fixer Loop, JSON UI Spec, Structured UI Generation Pipeline, Generative UI Builder, Generative UI Builder Implementation Tasks, LangGraph Data Analyst, Validation Retry Loop, LangGraph Data Analyst Dependencies

### Community 97 - "Portfolio Architecture UI"
Cohesion: 0.36
Nodes (5): ArchitectureDiagram(), DiagramStep, stepIndex(), STEPS, metadata

### Community 98 - "UA Batch Complexity"
Cohesion: 0.39
Nodes (7): batches, complexity(), nodeFor(), summaryFor(), tagsFor(), typeFor(), ua

### Community 99 - "NL2SQL Documentation"
Cohesion: 0.14
Nodes (17): NL2SQL Security Boundary, Architecture, Core Components, End-to-End Flow, LLM Interface (Gemini), Observability, Overview, Production Notes (+9 more)

### Community 100 - "Benchmark Datasets"
Cohesion: 0.29
Nodes (7): Model Comparison Evaluation, Code Generation Prompt, Research Report Prompt, Summarization Prompt, Code Test Cases, Research Test Cases, Summarization Test Cases

### Community 101 - "Content Crew Documentation"
Cohesion: 0.09
Nodes (24): Agents, Architecture, Cost and latency considerations, Crew Construction, Editor, File Structure, Key Design Principles, Model Usage (+16 more)

### Community 102 - "Document Corpus Samples"
Cohesion: 0.29
Nodes (7): April Invoice INV-2026-0417, Meridian Retail Group, MSA-MRG-ODS-2026, Orion Data Systems, Master Services Agreement, Service Level Agreement, SOC 2 Type II Certification

### Community 103 - "Evaluation Runner"
Cohesion: 0.48
Nodes (6): _prepare_case(), Any, Shared evaluation helpers for task-level execution metrics., Run *task_fn* across a dataset and return structured metrics.      The dataset, _run_case(), run_evaluation()

### Community 105 - "Copilot Context Assembly"
Cohesion: 0.47
Nodes (5): build_context(), ContextChunk, _format_chunk(), _normalize_chunk_text(), TypedDict

### Community 106 - "Document Chunking"
Cohesion: 0.29
Nodes (8): chunk_document(), _chunk_sentences(), _is_heading(), _split_sections(), _split_sentences(), load_documents(), ingest(), VectorStore

### Community 107 - "Document Embeddings"
Cohesion: 0.53
Nodes (5): batch_embeddings(), _embed_batch(), generate_embedding(), Exception, _should_retry()

### Community 108 - "Data Agent Charts"
Cohesion: 0.47
Nodes (5): generate_chart(), _infer_chart_type(), DataFrame, Matplotlib chart generation from execution results., Generate a chart from execution_result and save to output_path.      Returns t

### Community 109 - "Database Initialization"
Cohesion: 0.33
Nodes (6): _ensure_run_column(), _ensure_run_json_column(), init_db(), Add a JSON-backed text column to ``runs`` for existing SQLite databases., Add a column to ``runs`` if it does not already exist., Create database tables on startup.

### Community 110 - "Production Stack Security"
Cohesion: 0.10
Nodes (19): Agents, Architecture, Cost and latency considerations, Crew Configuration, Customer Analyst, customer_task, Error Handling, gtm_task (+11 more)

### Community 111 - "Financial Analysis Docs"
Cohesion: 0.50
Nodes (5): Financial Analyzer, Data Loader, Forecaster, Metrics Engine, Financial Reporter

### Community 112 - "Research Writer Node"
Cohesion: 0.60
Nodes (4): _build_prompt(), ResearchState, _scenario_prompt(), writer_node()

### Community 113 - "Research Planner"
Cohesion: 0.20
Nodes (17): build_provider_catalog(), default_model(), _fetch_ollama_tags(), get_model_spec(), infer_provider(), list_ollama_models(), ModelSpec, ollama_embedding_model() (+9 more)

### Community 114 - "Research Revision Docs"
Cohesion: 0.09
Nodes (23): Architecture, Bounded Revision Loop, Conditional edge after critic, Configuration, Cost and latency considerations, critic, Edge map, Error handling (+15 more)

### Community 115 - "Next Security Configuration"
Cohesion: 0.40
Nodes (3): nextConfig, rawApiBase, securityHeaders

### Community 116 - "Crew Comparison Docs"
Cohesion: 0.50
Nodes (4): Hiring Decision Crew, Investment Analyst Crew, Startup Simulator, LangGraph vs CrewAI Implementation Comparison

### Community 118 - "Grounded Document QA"
Cohesion: 0.50
Nodes (4): Citation System, Document Ingestion Pipeline, Grounded Question Answering, Vector Retrieval

### Community 119 - "Interview Evaluation Docs"
Cohesion: 0.67
Nodes (4): Difficulty Manager, Answer Evaluator, Feedback Generator, Question Generator

### Community 120 - "Workflow File Tool"
Cohesion: 1.00
Nodes (3): _format_rows(), _read_csv(), run()

### Community 121 - "RAG Evaluation Docs"
Cohesion: 0.67
Nodes (3): Grounded Answer Prompt, RAG Pipeline Evaluation, RAG Retrieval Evaluation

### Community 122 - "Incident Corpus Samples"
Cohesion: 0.67
Nodes (3): Customer Insights API, Incident Report IR-2026-009, Gateway and Scoring Service Timeout Mismatch

### Community 123 - "Security Policy Corpus"
Cohesion: 0.67
Nodes (3): Production Database Export Approval, Remote Access Security Policy Update, Multi-factor Authentication

### Community 124 - "Data Agent Docs"
Cohesion: 0.67
Nodes (3): Data Agent Architecture, Data Agent, Data Agent Implementation Tasks

### Community 125 - "Support Agent Docs"
Cohesion: 0.67
Nodes (3): Support Workflow Architecture, Support Agent, Support Agent Implementation Tasks

### Community 126 - "Workflow Agent Docs"
Cohesion: 0.67
Nodes (3): Workflow Agent Architecture, Workflow Agent, Workflow Agent Implementation Tasks

### Community 127 - "SQLite Data Directory"
Cohesion: 0.67
Nodes (3): Path, Return a writable directory for the SQLite database.      On read-only filesys, _resolve_data_dir()

### Community 212 - "analyze-my-batches.mjs"
Cohesion: 0.16
Nodes (10): batchData, batches, complexity(), indices, makeSubnodes(), node(), qualifiedClasses(), qualifiedFunctions() (+2 more)

### Community 213 - "dependencies.py"
Cohesion: 0.22
Nodes (12): Settings, get_llm_client_dep(), get_logger_dep(), get_settings_dep(), _logger(), Any, FastAPI dependency providers for shared services., FastAPI dependency that loads and returns the shared settings singleton. (+4 more)

### Community 214 - "eval_runner.py"
Cohesion: 0.19
Nodes (11): Any, Project evaluation runner backed by shared benchmark datasets., Run the shared benchmark dataset for a project and return aggregate metrics., run_project_evaluation(), get_dataset(), Return the benchmark dataset for a project by folder name.      Raises ``KeyEr, latency_stats(), Reusable scoring metrics for evaluation and benchmarking. (+3 more)

### Community 215 - "BenchmarkSuite"
Cohesion: 0.18
Nodes (9): BenchmarkCase, BenchmarkResult, BenchmarkSuite, _no_error(), Any, True unless output looks like an error message., A single benchmark definition., Aggregated result for one benchmark case. (+1 more)

### Community 216 - "ua-assign-layers.js"
Cohesion: 0.17
Nodes (12): assigned, buckets, duplicate, expected, fs, group(), input, invented (+4 more)

### Community 217 - "Changelog"
Cohesion: 0.17
Nodes (11): [1.1.0] - 2026-08-14, [1.1.1] - 2026-08-14, [2026-06-13], Added, Added, Changed, Changelog, Fixed (+3 more)

### Community 218 - "knowledge_base.py"
Cohesion: 0.24
Nodes (11): _build_index(), _cosine_similarity(), _get_embed_fn(), _get_index(), Force a rebuild of the index on the next search (useful after set_embed_fn)., Return the top-k articles most similar to *query*.      If *intent* matches a, Return the embedding function.      Creates a fresh Gemini client per call fro, Override the embedding function (useful for testing). (+3 more)

### Community 219 - "Tasks"
Cohesion: 0.18
Nodes (10): 1. Setup Database (DuckDB), 2. Create Sample Dataset, 3. Implement Schema Extraction, 4. Build LLM Wrapper, 5. Implement SQL Generation, 6. Implement SQL Validation, 7. Implement Retry Mechanism, 8. Execute Queries (+2 more)

### Community 220 - "VectorStore"
Cohesion: 0.24
Nodes (3): _cosine_similarity(), ndarray, VectorStore

### Community 221 - "Architecture"
Cohesion: 0.22
Nodes (8): Architecture, Cost and latency considerations, Crew Configuration, Data Flow, Model Usage, Overview, Summary, Why sequential

### Community 222 - "Tasks"
Cohesion: 0.22
Nodes (8): 1 — Define State Schema, 2 — Implement Planner Node, 3 — Implement Researcher Node, 4 — Implement Critic Node, 5 — Implement Writer Node, 6 — Build Graph Transitions, 7 — Add Loop Logic, Tasks

### Community 223 - "Debugging Agent"
Cohesion: 0.22
Nodes (8): Architecture, Debugging Agent, Evaluation, Example Usage, Features, Overview, System Flow, Trusted local use

### Community 224 - "_ContextFilter"
Cohesion: 0.25
Nodes (7): LogRecord, _ContextFilter, _JSONFormatter, _otel_trace_context(), Emit one JSON object per log line — suitable for cloud log ingestion., Return ``(trace_id, span_id)`` from the current OTel context.      Falls back, Populate structured fields on every log record.

### Community 225 - "otel.py"
Cohesion: 0.28
Nodes (8): Optional OpenTelemetry bootstrap for the platform.  Activate by calling :func:, Flush pending spans and shut down the tracer provider., Return the OTel modules or ``None`` if not installed., Initialise OpenTelemetry tracing.      Returns *True* when OTel was successful, setup_otel(), shutdown(), _try_import(), _try_import_otlp()

### Community 226 - "project_catalog.py"
Cohesion: 0.33
Nodes (8): GraphEdge, GraphNode, _normalized_project_key(), ProjectCatalogEntry, ProjectDemoConfig, ProjectGraph, BaseModel, Shared project catalog loaded from the portfolio JSON manifest.

### Community 227 - "test_dependency_security_contract.py"
Cohesion: 0.28
Nodes (5): _active_requirements(), Path, Regression checks for the production dependency security boundary., test_production_requirements_use_patched_direct_dependencies(), test_standalone_api_uses_patched_starlette()

### Community 228 - "generate-group2.mjs"
Cohesion: 0.25
Nodes (5): assigned, idFor(), root, typeFor(), ua

### Community 229 - "Tasks"
Cohesion: 0.25
Nodes (8): architecture_task, Brainstorming Phase, Core Pipeline, execution_task, product_task, proposal_task (×3), selection_task, Tasks

### Community 230 - "Tasks"
Cohesion: 0.25
Nodes (7): Add Risk Scoring, Build Input Extractor, Build Reasoning Module, Create Medical Knowledge Base, Format Output, Implement Retrieval Logic, Tasks

### Community 231 - "retriever.py"
Cohesion: 0.43
Nodes (7): init_store(), _keyword_score(), _parse_rerank_score(), VectorStore, _rerank_score(), retrieve(), _tokenize()

### Community 232 - "fixer_node"
Cohesion: 0.39
Nodes (7): _apply_diff(), _build_prompt(), _extract_block(), fixer_node(), _make_diff(), Apply a unified diff to *original* and return the patched text.      Returns `, Generate a unified diff between *original* and *fixed*.

### Community 233 - "run"
Cohesion: 0.29
Nodes (6): Entry point for the Research Graph Agent., Run the research graph agent and return structured output., run(), initial_state(), TypedDict, ResearchState

### Community 234 - "assemble-scan-result.cjs"
Cohesion: 0.25
Nodes (7): frameworks, fs, imports, languages, output, paths, scan

### Community 235 - "ua-assemble-final.cjs"
Cohesion: 0.25
Nodes (7): assembled, [assembledPath, scanPath, layersPath, tourPath, commitHash], fs, graph, layersRaw, scan, tourRaw

### Community 236 - "Investment Analysis Crew"
Cohesion: 0.29
Nodes (7): Hiring Decision Crew, Resume Screening, Structured Hiring Decision, Hiring Crew Implementation Checklist, Hiring Evaluation JSON Schemas, Investment Analysis Crew, Investment Crew Implementation Checklist

### Community 237 - "get_logger"
Cohesion: 0.33
Nodes (7): Formatter, _build_formatter(), _configure_root_logger(), get_logger(), Logger, Return a named logger with shared structured output across modules.      Param, TextIO

### Community 238 - "Observe Plan Act Loop"
Cohesion: 0.29
Nodes (7): Autonomous Browser Agent, Browser Agent Memory, Observe Plan Act Loop, Browser Agent Implementation Checklist, Playwright Browser Controller, Traceable Chunk Metadata, Symbol Aware Chunking

### Community 239 - "Research Graph"
Cohesion: 0.29
Nodes (6): Example Usage, Features, Overview, Research Graph, Shared API, System Flow

### Community 240 - "Peer Review Round"
Cohesion: 0.33
Nodes (6): Delivery Evidence Gap, Harness Review, Brainstorming And CEO Selection, Peer Review Round, Startup Team Simulator, Startup Simulator Implementation Checklist

### Community 241 - "Production Design Notes"
Cohesion: 0.33
Nodes (6): Configuration, Error handling, Observability, Output structure, Production Design Notes, Testing

### Community 242 - "retrieve"
Cohesion: 0.53
Nodes (5): init_store(), _keyword_score(), VectorStore, retrieve(), _tokenize()

### Community 243 - "sql_generator.py"
Cohesion: 0.53
Nodes (5): _build_prompt(), _clean_sql(), generate_sql(), SQL generation module., _validate_generated_sql()

### Community 245 - "Product Launch Strategy Crew"
Cohesion: 0.40
Nodes (5): Go To Market Plan, Market Customer Positioning, Product Launch Strategy Crew, Product Launch Crew Implementation Checklist, Structured Strategy Schemas

### Community 246 - "Agents"
Cohesion: 0.40
Nodes (5): Agents, CEO, CTO, Engineer, Product Manager

### Community 247 - "ua-build-fingerprint-input.cjs"
Cohesion: 0.40
Nodes (4): fs, input, scan, [scanPath, outputPath, projectRoot, gitCommitHash]

### Community 249 - "ResearchState"
Cohesion: 0.67
Nodes (3): initial_state(), TypedDict, ResearchState

### Community 251 - "ua-fix-invalid-nodes.cjs"
Cohesion: 0.50
Nodes (3): fs, graph, removedIds

### Community 252 - "ua-write-meta.cjs"
Cohesion: 0.50
Nodes (3): fs, meta, [outputPath, gitCommitHash, analyzedFiles]

## Knowledge Gaps
- **537 isolated node(s):** `root`, `ua`, `all`, `batches`, `root` (+532 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **62 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `set_byok_api_key()` connect `BYOK Project Entrypoints` to `Financial Analyst Runtime`, `Model Instrumentation Dependencies`, `API Response Models`, `run`, `NL2SQL Agent Runtime`, `Research Service API`, `Runtime Configuration Jobs`, `UI Builder Runtime`, `Clinical Assistant Runtime`, `Document Intelligence Runtime`, `Research Evaluation`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `reset_byok_api_key()` connect `BYOK Project Entrypoints` to `Financial Analyst Runtime`, `Model Instrumentation Dependencies`, `API Response Models`, `run`, `NL2SQL Agent Runtime`, `Research Service API`, `Runtime Configuration Jobs`, `UI Builder Runtime`, `Clinical Assistant Runtime`, `Document Intelligence Runtime`, `Research Evaluation`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `run()` connect `BYOK Project Entrypoints` to `Data Agent Workflow`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `create_app()` (e.g. with `BYOKMiddleware` and `ErrorHandlingMiddleware`) actually correct?**
  _`create_app()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `root`, `ua`, `all` to the rest of the system?**
  _537 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LLM Provider Runtime` be split into smaller, more focused modules?**
  _Cohesion score 0.13095238095238096 - nodes in this community are weakly interconnected._
- **Should `Startup Simulator Crew` be split into smaller, more focused modules?**
  _Cohesion score 0.05879917184265011 - nodes in this community are weakly interconnected._