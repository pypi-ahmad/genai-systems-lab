# Graph Report - .  (2026-08-14)

## Corpus Check
- Large corpus: 689 files · ~787,093 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 2735 nodes · 5524 edges · 212 communities (157 shown, 55 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `set_byok_api_key()` - 51 edges
2. `reset_byok_api_key()` - 51 edges
3. `create_app()` - 47 edges
4. `generate_text()` - 46 edges
5. `generate_structured()` - 38 edges
6. `LLMGenerationError` - 33 edges
7. `_get_client()` - 28 edges
8. `run_project()` - 26 edges
9. `emit_step()` - 25 edges
10. `generate_structured()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Hiring Decision Crew` --semantically_similar_to--> `Investment Analysis Crew`  [INFERRED] [semantically similar]
  crew-hiring-system/architecture.md → crew-investment-analyst/architecture.md
- `Investment Analysis Crew` --semantically_similar_to--> `Product Launch Strategy Crew`  [INFERRED] [semantically similar]
  crew-investment-analyst/architecture.md → crew-product-launch/architecture.md
- `Clinical Risk Scoring` --semantically_similar_to--> `Market Financial Risk Analysis`  [INFERRED] [semantically similar]
  genai-clinical-assistant/tasks.md → crew-investment-analyst/architecture.md
- `Product Launch Strategy Crew` --semantically_similar_to--> `Startup Team Simulator`  [INFERRED] [semantically similar]
  crew-product-launch/architecture.md → crew-startup-simulator/architecture.md
- `Browser Agent Memory` --semantically_similar_to--> `Traceable Chunk Metadata`  [INFERRED] [semantically similar]
  genai-browser-agent/architecture.md → genai-code-copilot/architecture.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Content Pipeline Refinement Flow** — crew_content_pipeline_architecture_researcher, crew_content_pipeline_architecture_writer, crew_content_pipeline_architecture_editor, crew_content_pipeline_architecture_seo_expert [EXTRACTED 1.00]
- **Sequential Crew Designs** — crew_hiring_system_architecture_hiring_decision_crew, crew_investment_analyst_architecture_investment_analysis_crew, crew_product_launch_architecture_product_launch_crew, crew_startup_simulator_architecture_startup_team_simulator [INFERRED 0.95]
- **Structured Output Contracts** — crew_hiring_system_tasks_json_schemas, crew_product_launch_tasks_structured_strategy_schemas, crew_startup_simulator_architecture_peer_review_round [INFERRED 0.85]
- **Traceable AI Workflows** — genai_browser_agent_architecture_browser_memory, genai_code_copilot_architecture_traceable_chunk_metadata, genai_clinical_assistant_tasks_clinical_guideline_retrieval [INFERRED 0.75]
- **Financial Analysis Pipeline** — genai_financial_analyst_architecture_data_loader, genai_financial_analyst_architecture_metrics_engine, genai_financial_analyst_architecture_analyzer, genai_financial_analyst_architecture_reporter [EXTRACTED 1.00]
- **Personal Knowledge OS Processing Pipeline** — genai_knowledge_os_architecture_ingestion_pipeline, genai_knowledge_os_architecture_vector_store, genai_knowledge_os_architecture_retriever, genai_knowledge_os_architecture_summarizer, genai_knowledge_os_architecture_insight_engine [EXTRACTED 1.00]
- **NL2SQL Safe Query Pipeline** — genai_nl2sql_agent_architecture_schema_loader, genai_nl2sql_agent_architecture_sql_generator, genai_nl2sql_agent_architecture_sql_validator, genai_nl2sql_agent_architecture_query_executor, genai_nl2sql_agent_architecture_result_summarizer [EXTRACTED 1.00]
- **Research Revision Workflow** — genai_research_system_architecture_planner, genai_research_system_architecture_researcher, genai_research_system_architecture_critic, genai_research_system_architecture_writer [EXTRACTED 1.00]
- **Compose Persistence and Queue Services** — docker_compose_production_stack, docker_compose_postgresql, docker_compose_redis_rq_worker [EXTRACTED 1.00]

## Communities (212 total, 55 thin omitted)

### Community 0 - "LLM Provider Runtime"
Cohesion: 0.06
Nodes (104): GenerateContentConfig, GenerateContentResponse, ProviderId, get_effective_api_key(), get_effective_model(), get_request_provider(), Return the request-scoped provider override, if present., Return the per-request BYOK key from the ``x-api-key`` header. Raises… (+96 more)

### Community 1 - "Startup Simulator Crew"
Cohesion: 0.07
Nodes (52): build_ceo(), build_cto(), build_engineer(), build_product_manager(), Agent, Agent definitions for the Startup Team Simulator., build_crew(), Crew (+44 more)

### Community 2 - "Playground State Utilities"
Cohesion: 0.08
Nodes (55): ErrorDisplay(), PlaygroundConversationPanel(), PlaygroundConversationPanelProps, PlaygroundGraphPanel(), PlaygroundGraphPanelProps, ChevronIcon(), AnyObj, assistantCardTone() (+47 more)

### Community 3 - "Shared API Schemas"
Cohesion: 0.07
Nodes (60): create_app(), Create a pre-configured FastAPI instance. Projects create their own ``FastAPI``…, _resolve_allowed_origins(), AuthConfigResponse, AuthRequest, AuthResponse, AuthUserResponse, BaseRequest (+52 more)

### Community 4 - "Persistence Models"
Cohesion: 0.08
Nodes (39): BaseHTTPMiddleware, DeclarativeBase, listens_for, BYOKMiddleware, ErrorHandlingMiddleware, InputValidationMiddleware, _MetricsStore, Request (+31 more)

### Community 5 - "Data Agent Workflow"
Cohesion: 0.08
Nodes (47): get_metadata(), load_data(), _load_sample(), DataFrame, Load a dataset from file or return built-in sample data., Return column names, dtypes, shape, and a small sample (max 3 rows)., build_graph(), LangGraph workflow: planner → executor → analyzer → evaluator (with retry loop). (+39 more)

### Community 6 - "Model Instrumentation Dependencies"
Cohesion: 0.07
Nodes (39): field_validator, build_graph(), Run the research graph agent and return structured output., run(), critic_node(), ResearchState, planner_node(), ResearchState (+31 more)

### Community 7 - "BYOK Project Entrypoints"
Cohesion: 0.07
Nodes (37): Execution entry point for the Content Creation Pipeline., Run the content creation pipeline and return structured output., run(), _parse_json(), Execution entry point for the Hiring Decision Crew., Run candidate evaluation on resume text and return structured output., run(), _parse_json() (+29 more)

### Community 8 - "API Response Models"
Cohesion: 0.07
Nodes (46): datetime, MemoryEntryPayload, MetricsResponse, Response, _append_execution_trace(), _append_fallback_memory_entries(), _append_fallback_timeline_entries(), _append_memory_entry() (+38 more)

### Community 9 - "Portfolio API Client"
Cohesion: 0.08
Nodes (40): models, PlaygroundHistoryDeps, usePlaygroundHistory(), ExecuteRunOverrides, loadMetrics(), ProjectRunBadge(), apiBaseCandidates(), apiFetch() (+32 more)

### Community 10 - "Shared API Tests"
Cohesion: 0.10
Nodes (43): TestClient, client(), _extract_done_event(), fixture, MonkeyPatch, parametrize, The SSE stream must not pretend to stream tokens. Earlier revisions sliced the…, Leaderboard feature was removed entirely — no dedicated route should exist. (+35 more)

### Community 11 - "Knowledge OS Storage"
Cohesion: 0.08
Nodes (23): chunk_text(), batch_embeddings(), _embed_batch(), generate_embedding(), Exception, _should_retry(), load_documents(), generate_insights() (+15 more)

### Community 12 - "Code Copilot Indexing"
Cohesion: 0.11
Nodes (38): AST, ParsedFile, Path, TypedDict, _read_text_file(), scan_directory(), _should_ignore_directory(), add_documents() (+30 more)

### Community 13 - "Playground Project UI"
Cohesion: 0.12
Nodes (31): PlaygroundClient(), ConfirmRequest, PlaygroundSidebar(), PlaygroundSidebarProps, sortedProjects(), useConfirmModal(), extractKeyMetrics(), extractSteps() (+23 more)

### Community 14 - "Frontend Package Dependencies"
Cohesion: 0.05
Nodes (39): eslint, eslint-config-next, next, next-themes, dependencies, next, next-themes, react (+31 more)

### Community 15 - "Auth Persistence Services"
Cohesion: 0.07
Nodes (38): HTTPAuthorizationCredentials, _allowed_jwt_algorithms(), authenticate_user(), _b64url_decode(), _b64url_encode(), create_user(), _deserialize_memory_entries(), _deserialize_timeline_entries() (+30 more)

### Community 16 - "Project Catalog Tests"
Cohesion: 0.10
Nodes (37): _discover_projects(), Return a list of runnable projects (folders containing app/main.py)., list_available(), _project_aliases(), Return projects that may be executed through the shared runner., Resolve canonical and legacy project names to a runnable project folder., Derive API-name → folder-slug mapping from the catalog plus legacy route…, resolve_project_name() (+29 more)

### Community 17 - "Support Agent Workflow"
Cohesion: 0.10
Nodes (30): build_graph(), _route_after_evaluator(), _build_index(), _cosine_similarity(), _get_embed_fn(), _get_index(), Force a rebuild of the index on the next search (useful after set_embed_fn)., Return the top-k articles most similar to *query*. If *intent* matches a known… (+22 more)

### Community 18 - "Interview Session Runtime"
Cohesion: 0.09
Nodes (23): adjust_difficulty(), Adjust interview difficulty based on candidate performance., evaluate_answer(), _get_rubric(), Evaluate candidate answers using Gemini., generate_feedback(), Generate candidate-facing feedback using Gemini., _get_answer_text() (+15 more)

### Community 19 - "Data Analyst Workflow"
Cohesion: 0.12
Nodes (28): plan_analysis(), Planner agent node — creates a structured, executable analysis plan. The…, Generate a structured analysis plan from the user query. Reads: ``user_query``,…, generate_report(), Reporter agent node — converts analysis results into insight-driven Markdown., Convert execution results into an insight-driven Markdown report. Reads…, _parse_verdict(), Validator agent node — checks execution results against the analysis plan. Uses… (+20 more)

### Community 20 - "Timeline Comparison UI"
Cohesion: 0.08
Nodes (26): comparisonRows, metadata, overviewCards, projectMap, repoExamples, DismissibleTip(), entryBadgeTone(), entryIconTone() (+18 more)

### Community 21 - "Evaluation Runtime"
Cohesion: 0.07
Nodes (28): Any, Project evaluation runner backed by shared benchmark datasets., Run the shared benchmark dataset for a project and return aggregate metrics., run_project_evaluation(), BenchmarkCase, BenchmarkResult, BenchmarkSuite, _contains_all() (+20 more)

### Community 22 - "Runtime Configuration Jobs"
Cohesion: 0.15
Nodes (28): call_api(), Promptfoo custom Python provider for genai-systems-lab project workflows., extract_primary_text(), normalize_provider(), parse_output_payload(), Any, request_overrides(), resolve_api_key() (+20 more)

### Community 23 - "Cross Project Documentation"
Cohesion: 0.06
Nodes (33): Delivery Evidence Gap, Harness Review, Hiring Decision Crew, Resume Screening, Structured Hiring Decision, Hiring Crew Implementation Checklist, Hiring Evaluation JSON Schemas, Investment Analysis Crew (+25 more)

### Community 24 - "Browser Agent Runtime"
Cohesion: 0.11
Nodes (11): execute(), run_agent(), BrowserController, BrowserMemory, _clean(), get_observation(), _get_text_observation(), _get_vision_observation() (+3 more)

### Community 25 - "Debugging Agent Workflow"
Cohesion: 0.12
Nodes (25): build_graph(), route_after_evaluator(), analyzer_node(), _build_prompt(), _build_prompt(), _extract_code(), test_generator_node(), evaluator_node() (+17 more)

### Community 26 - "UA Architecture Analysis"
Cohesion: 0.06
Nodes (28): allEdges, byId, cross, crossCategoryEdges, dataPipeline, dependencyDirection, directoryGroups, docCoverage (+20 more)

### Community 27 - "Structured Logging"
Cohesion: 0.11
Nodes (24): Formatter, LogRecord, Shared structured logging., _build_formatter(), _configure_root_logger(), _ContextFilter, get_logger(), _JSONFormatter (+16 more)

### Community 28 - "Hiring Crew Tasks"
Cohesion: 0.17
Nodes (27): build_behavioral_interviewer(), build_bias_auditor(), build_comparative_analyst(), build_hiring_manager(), build_resume_screener(), build_technical_interviewer(), Agent, Agent definitions for the Hiring Decision Crew. (+19 more)

### Community 29 - "TypeScript Configuration"
Cohesion: 0.07
Nodes (29): compilerOptions, allowJs, baseUrl, esModuleInterop, incremental, isolatedModules, jsx, lib (+21 more)

### Community 30 - "Document Intelligence Runtime"
Cohesion: 0.11
Nodes (20): Run codebase Q&A and return structured output. Input format:…, run(), attach_citations(), load_documents(), ingest(), VectorStore, query(), Run a document query and return structured output. (+12 more)

### Community 31 - "Portfolio App Shell"
Cohesion: 0.09
Nodes (18): manrope, metadata, plexMono, metadata, ThemeProvider(), HelpReset(), SUPPRESS_KEYS, allLinks (+10 more)

### Community 32 - "Metrics Dashboard"
Cohesion: 0.11
Nodes (25): average(), bucketLabels(), buildChartSeries(), buildTrendSummary(), ChartPoint, describeLatencyDelta(), describePointDelta(), downloadBlob() (+17 more)

### Community 33 - "Financial Analyst Runtime"
Cohesion: 0.12
Nodes (20): analyze_metrics(), DataFrame, load_data(), DataFrame, forecast(), DataFrame, Run financial analysis and return structured output. Input format:…, run() (+12 more)

### Community 34 - "Frontend Authentication"
Cohesion: 0.15
Nodes (20): AuthClient(), Mode, metadata, isRunMemoryEntry(), isRunTimelineEntry(), usePlaygroundAccount(), clearRunSession(), fetchAuthConfig() (+12 more)

### Community 35 - "Shared Cache Layer"
Cohesion: 0.12
Nodes (16): Cache, cached_embedding(), cached_llm_call(), get_embedding_cache(), get_llm_cache(), _hash_key(), Any, In-memory prompt-keyed cache for LLM responses and embeddings. (+8 more)

### Community 36 - "Research System Graph"
Cohesion: 0.13
Nodes (18): build_graph(), _instrument_node(), ResearchState, StateGraph, route_after_critic(), route_after_editor(), route_after_originality(), _build_prompt() (+10 more)

### Community 37 - "Project Catalog UI"
Cohesion: 0.11
Nodes (17): groups, metadata, categoryAccent, categoryDiagramAccent, formatJson(), generateMetadata(), ProjectDetailPage(), Props (+9 more)

### Community 38 - "Workflow Agent Graph"
Cohesion: 0.17
Nodes (17): build_graph(), _route_after_checkpoint(), checkpoint_node(), load_checkpoint(), Load a previously saved state from disk. Returns ``None`` if the file does not…, Persist current state to disk and advance to the next step. If validation…, _build_prompt(), executor_node() (+9 more)

### Community 39 - "Shared Project Runner"
Cohesion: 0.10
Nodes (24): ModuleNotFoundError, _clear_project_imports(), _ensure_import_paths(), _fire_and_forget_langfuse_flush(), _is_dev_mode(), _langfuse_flush_worker(), _optional_dependency_error(), StepEmitter (+16 more)

### Community 40 - "JWT Authentication Tests"
Cohesion: 0.16
Nodes (23): AuthError, create_access_token(), decode_access_token(), Exception, Create a signed JWT for the authenticated user. Uses PyJWT with a hardcoded…, Validate and decode a signed JWT. Delegates verification to PyJWT with an…, Raised when authentication fails., fixture (+15 more)

### Community 41 - "Dataframe Core Tests"
Cohesion: 0.15
Nodes (11): get_basic_info(), get_summary_stats(), profile_dataset(), DataFrame, DataFrame loading and profiling utilities. Supports CSV and Excel files.…, Generate a text profile of *df* (legacy helper). Combines…, Return basic metadata about a DataFrame. Returns: A dict with keys ``rows``,…, Return summary statistics for a DataFrame. Returns: A dict with keys… (+3 more)

### Community 42 - "Code Execution Tests"
Cohesion: 0.15
Nodes (8): _check_dangerous(), CodeResult, execute_code(), Sandboxed Python code execution for data analysis tasks. Executes user-supplied…, Outcome of a sandboxed code execution., Return a rejection reason if *code* contains a blocked pattern., Execute *code* in a subprocess sandbox. Args: code: Python source code to…, TestExecuteCode

### Community 43 - "Graph Visualization UI"
Cohesion: 0.16
Nodes (20): AnimatedGraph(), AnimatedGraphProps, edgeAnchor(), layoutNodes(), nodeCenter(), PALETTES, PositionedNode, statusLabel() (+12 more)

### Community 44 - "Langfuse Observability"
Cohesion: 0.23
Nodes (20): _score_langfuse_confidence(), Shared observability layer for production LLM monitoring. Currently integrates…, _base_url(), create_trace(), _credentials_present(), _ensure_client(), flush(), get_client() (+12 more)

### Community 45 - "Investment Crew"
Cohesion: 0.23
Nodes (18): build_financial_analyst(), build_market_analyst(), build_risk_analyst(), build_strategist(), Agent, Agent definitions for the Investment Analysis Crew., build_crew(), Crew (+10 more)

### Community 46 - "Content Pipeline Crew"
Cohesion: 0.23
Nodes (17): build_editor(), build_researcher(), build_seo_expert(), build_writer(), Agent, Agent definitions for the Content Creation Pipeline., build_crew(), Crew (+9 more)

### Community 47 - "Product Launch Crew"
Cohesion: 0.23
Nodes (17): build_customer_analyst(), build_market_researcher(), build_marketing_strategist(), build_product_strategist(), Agent, Agent definitions for the Product Launch Strategy Crew., build_crew(), Crew (+9 more)

### Community 48 - "Runner Cache Tests"
Cohesion: 0.15
Nodes (19): _load_main(), Import ``<project>/app/main.py`` and return the module, or *None*. Results are…, fixture, MonkeyPatch, Regression tests for ``shared.api.runner._MODULE_CACHE``. The audit flagged…, Prod mode must never reload once a project has been imported., The cross-thread mutation guards must be actual locks, not no-ops., Concurrent ``_load_main`` calls must not raise and must leave a stable cache.… (+11 more)

### Community 49 - "OpenTelemetry Instrumentation"
Cohesion: 0.15
Nodes (15): get_tracer(), _NoopSpan, _NoopTracer, Any, BaseException, Optional OpenTelemetry bootstrap for the platform. Activate by calling…, Return an OTel ``Tracer`` (or a no-op stub)., Start a traced span. Falls back to a no-op context when OTel is absent. Usage::… (+7 more)

### Community 50 - "CI Security Tests"
Cohesion: 0.11
Nodes (10): ci_text(), dependabot_cfg(), fixture, Regression tests for the CI security / dependency contract. The audit flagged…, ``langgraph-data-analyst/`` has its own requirements.txt — Dependabot must pick…, ``pip-audit`` must not be annotated with ``continue-on-error: true``., Trivy image scan must have ``exit-code: \"1\"`` so CVEs fail the job., test_ci_blocks_on_pip_audit_findings() (+2 more)

### Community 51 - "Promptfoo RAG Providers"
Cohesion: 0.22
Nodes (17): call_api(), _ensure_indexed(), _index_state(), _normalize_chunks(), Any, call_api(), _ensure_indexed(), _index_state() (+9 more)

### Community 52 - "NL2SQL Execution"
Cohesion: 0.15
Nodes (15): execute_sql(), DataFrame, SQL execution module., _create_tables(), get_connection(), get_schema_description(), _initialize_database(), DuckDBPyConnection (+7 more)

### Community 53 - "Research Orchestration"
Cohesion: 0.18
Nodes (12): Shared memory for the multi-agent research workflow., ResearchMemory, _build_context(), _needs_improvement(), _process_task(), End-to-end orchestration for the multi-agent research workflow., run_research(), run_research_async() (+4 more)

### Community 54 - "UI Builder Runtime"
Cohesion: 0.15
Nodes (15): fix_code(), Fix generated React code based on an error message., Return a corrected version of the React code based on the error message., build(), Execution entry point for the Generative UI Builder., Run the full pipeline: generate spec, validate, generate code, fix if needed., Run the UI generation pipeline and return structured output., run() (+7 more)

### Community 55 - "Evaluation Metrics"
Cohesion: 0.18
Nodes (14): Shared evaluation framework for LLM-powered projects., latency_stats(), Reusable scoring metrics for evaluation and benchmarking., Return ``1.0`` if ``pred`` matches a regex or literal structure. If *pattern*…, Compute min / max / mean / p95 from a list of latencies in ms., structural_match(), Any, Asyncio-based stress testing for throughput and error-rate analysis. (+6 more)

### Community 56 - "Interview Voice IO"
Cohesion: 0.16
Nodes (17): _extract_audio_bytes(), _frames_to_wav(), listen(), _play_wav_bytes(), Voice I/O for the AI Interviewer using Gemini TTS/STT. Requires optional…, Record from microphone until silence, then transcribe with Gemini., Record audio chunks until sustained silence is detected., Convert recorded numpy frames to WAV bytes. (+9 more)

### Community 57 - "UI Code Generation"
Cohesion: 0.18
Nodes (16): _camel_to_kebab(), _collect_component_names(), generate_files(), generate_react_code(), Generate React component code from a validated UI spec., Convert a validated UI spec into a dict of {filename: content} pairs. Always…, Render top-level shared styles as a CSS stylesheet string., Convert a validated UI spec into a single React component string. Kept for… (+8 more)

### Community 58 - "Session Memory"
Cohesion: 0.24
Nodes (13): Any, _serialize_session_payload(), _build_interaction_entry(), build_session_prompt(), _dedupe_key(), deserialize_session_memory_entries(), _normalize_whitespace(), preview_session_memory_entries() (+5 more)

### Community 59 - "LLM Telemetry Tests"
Cohesion: 0.30
Nodes (13): begin_llm_run(), consume_llm_call_metadata(), consume_llm_run_usage(), Any, record_llm_call_metadata(), record_llm_run_call(), bind_token_emitter(), Token (+5 more)

### Community 60 - "Clinical Planning"
Cohesion: 0.18
Nodes (12): extract_patient_info(), Extract structured patient information from free-text input., analyze_conditions(), _format_conditions(), _format_patient(), Analyze candidate conditions against patient info using LLM reasoning., extract_key_information(), extract() (+4 more)

### Community 61 - "Clinical Assistant Runtime"
Cohesion: 0.19
Nodes (13): _format_condition_block(), format_output(), Format analyzed conditions into a human-readable clinical summary., _merge_reasoning_and_confidence(), Application entry point for the clinical decision support pipeline., Combine reasoning from the LLM with confidence from the deterministic scorer., Run the clinical decision support pipeline and return structured output., run() (+5 more)

### Community 62 - "Document Retrieval"
Cohesion: 0.18
Nodes (8): _keyword_score(), _parse_rerank_score(), _rerank_score(), retrieve(), _tokenize(), _cosine_similarity(), ndarray, VectorStore

### Community 63 - "Research Evaluation"
Cohesion: 0.20
Nodes (14): aggregate_quality_metrics(), collect_research_metrics(), Any, _contains_keywords(), Any, Project-local evaluation runner for genai-research-system. This module uses the…, Run the project evaluation with an explicitly bound API key., Run the flagship research workflow and return the structured response. (+6 more)

### Community 64 - "Plan Parsing Tests"
Cohesion: 0.22
Nodes (4): _parse_plan(), Extract a list of step strings from the LLM response. Falls back to a safe…, Tests _parse_plan directly — no LLM calls needed., TestParsePlan

### Community 65 - "Confidence Scoring"
Cohesion: 0.28
Nodes (15): _clamp01(), _collect_evaluator_candidates(), _compute_evaluator_score(), compute_run_confidence(), _extract_output_retries(), _extract_timeline_retries(), _has_meaningful_value(), _infer_retry_count() (+7 more)

### Community 66 - "Shared Utilities"
Cohesion: 0.15
Nodes (11): chunk_text(), Any, BaseException, Generic helper functions reusable across all projects., Split *text* into overlapping chunks of up to *max_chars* characters. Tries to…, Decorator that retries a function with exponential backoff. Usage::…, Context-manager for timing blocks of code. Usage:: with Timer() as t: do_work()…, retry() (+3 more)

### Community 67 - "Docker Security Tests"
Cohesion: 0.16
Nodes (13): _active_lines(), dockerfile_text(), dockerignore_text(), fixture, Regression tests for Dockerfile secret-handling and project-copy correctness.…, Every runnable project must land under ``/app/<slug>/``, not ``/app``., Strip comments and blank lines — we only care about live directives., Historical bug: ``COPY crew-*/ ./`` merges every project's files into /app. The… (+5 more)

### Community 68 - "UI Preview Server"
Cohesion: 0.16
Nodes (12): build_preview_html(), _css_to_style_block(), _PreviewHandler, Local preview server for generated React components. Uses Python's built-in…, Serves the preview HTML on GET /., Start a local HTTP server to preview the generated UI., Remove import/export statements for inline use., Indent CSS for embedding inside a <style> tag. (+4 more)

### Community 69 - "Run Detail UI"
Cohesion: 0.18
Nodes (10): formatTimestamp(), SharedRunPage(), clampConfidence(), ConfidenceIndicator(), ConfidenceIndicatorProps, confidenceTone(), fetchSharedRun(), RunMemoryEntry (+2 more)

### Community 70 - "Data Visualization"
Cohesion: 0.20
Nodes (13): apply_default_style(), _check_plot_code(), generate_plot(), generate_summary_charts(), DataFrame, Path, Visualization utilities for chart generation and figure management. Provides…, Persist every currently open *matplotlib* figure to disk. Args: output_dir:… (+5 more)

### Community 71 - "Agent Graph UI"
Cohesion: 0.16
Nodes (13): AgentGraph(), AgentGraphProps, AgentGraphStep, agentGraphSteps, EDGE_STYLES, EDGES, EdgeVisualState, getEdgeVisualState() (+5 more)

### Community 72 - "Code Embeddings"
Cohesion: 0.26
Nodes (12): EmbedContentResponse, _embed_batch(), EmbeddingGenerationError, _extract_embedding_values(), generate_embedding(), generate_embeddings_batch(), _normalize_text(), Exception (+4 more)

### Community 73 - "Clinical Retrieval"
Cohesion: 0.23
Nodes (11): get_all_conditions(), Return all conditions in the knowledge base., _build_embedding_index(), _cosine_similarity(), _embed_texts(), Embed a list of texts in a single API call., Embed patient symptoms and all condition symptoms in one batch API call., Score a condition by averaging the best similarity each patient symptom… (+3 more)

### Community 74 - "NL2SQL Agent Runtime"
Cohesion: 0.19
Nodes (10): _build_summary_prompt(), Any, DataFrame, Agent orchestration module., Run the NL-to-SQL pipeline, emitting real step events as each stage executes.…, run_agent(), _load_run_agent(), Application entry point. Step events (``emit_step``) are now emitted from… (+2 more)

### Community 75 - "Research Service API"
Cohesion: 0.29
Nodes (11): health(), BaseModel, post, ResearchRunRequest, ResearchRunResponse, run_research(), normalize_formats(), normalize_tone() (+3 more)

### Community 76 - "Project Contract Tests"
Cohesion: 0.22
Nodes (12): ModuleType, _all_projects(), _load_main_module(), parametrize, Contract-level smoke tests for every runnable project. Every project under the…, ``run(input, api_key=..., [step_emitter=...], **)`` — exact runner contract.…, Contract: ``run`` should annotate a ``dict``/``dict[...]`` return type when…, All project directories whose ``app/main.py`` file exists. (+4 more)

### Community 77 - "Portfolio Marketing Pages"
Cohesion: 0.19
Nodes (8): metadata, skills, capabilities, highlights, stats, Card(), CardProps, joinClasses()

### Community 78 - "UA Batch Analysis"
Cohesion: 0.21
Nodes (9): batches, complexity(), fnSummary(), idFor(), nodeForClass(), nodeForFunction(), root, typeFor() (+1 more)

### Community 79 - "Architecture Documentation"
Cohesion: 0.18
Nodes (12): Evaluation-First Design, LLM Wrapper, Shared Layer, System Architecture, Dependency Update Automation, Continuous Integration, Promptfoo Evaluations, FastAPI Backend (+4 more)

### Community 80 - "Knowledge Retrieval"
Cohesion: 0.17
Nodes (12): Ingestion Pipeline, Insight Engine, Memory System, Retriever, Summarizer, Vector Store, Metadata Quality, Retrieval Quality (+4 more)

### Community 81 - "Analyst Executor Agent"
Cohesion: 0.20
Nodes (11): execute_plan(), _extract_code(), Executor agent node — converts the analysis plan into runnable code and…, Strip markdown fences if present and return clean Python code., Convert the analysis plan into Python code, execute it, and capture results.…, _client(), _generate(), generate_fast() (+3 more)

### Community 82 - "Dataframe Loading Tests"
Cohesion: 0.24
Nodes (5): load_dataframe(), Path, Load a CSV or Excel file into a DataFrame. Args: path: File path. Supported…, fixture, TestLoadDataframe

### Community 83 - "Run Explanation"
Cohesion: 0.32
Nodes (11): build_run_explanation(), _format_input(), _format_memory(), _format_output(), _format_timeline(), Any, Helpers for generating explainability summaries for saved runs., Generate a concise structured explanation for one saved run. User-controlled… (+3 more)

### Community 84 - "SQLite Pragma Tests"
Cohesion: 0.35
Nodes (11): _make_file_engine(), Path, Regression tests for SQLite connection-level pragmas. The audit flagged missing…, Create a fresh file-backed SQLite engine wired to the same listener., End-to-end sanity: with FK enforcement ON, an invalid insert fails., test_busy_timeout_is_at_least_five_seconds(), test_foreign_key_violation_is_rejected(), test_foreign_keys_are_enforced() (+3 more)

### Community 85 - "Analyst FastAPI"
Cohesion: 0.25
Nodes (10): FastAPI, analyze(), AnalyzeRequest, AnalyzeResponse, BaseModel, post, FastAPI application for the LangGraph Data Analyst service., Run the LangGraph analysis workflow and return the final report. (+2 more)

### Community 87 - "Auth Hardening Tests"
Cohesion: 0.38
Nodes (10): LogCaptureFixture, _load_jwt_secret(), MonkeyPatch, Tests for auth secret hardening — minimum length, prod enforcement, ephemeral…, test_minimum_length_jwt_secret_is_accepted(), test_missing_secret_in_dev_logs_ephemeral_warning(), test_missing_secret_in_dev_returns_ephemeral(), test_missing_secret_in_prod_raises() (+2 more)

### Community 88 - "UA Assigned Analysis"
Cohesion: 0.22
Nodes (7): all, batches, classNode(), complexity(), functionNode(), root, ua

### Community 89 - "Research Clients"
Cohesion: 0.29
Nodes (8): _build_prompt(), critique(), Critique utilities for reviewing research outputs., _build_prompt(), Research execution utilities., research_task(), _get_client(), Any

### Community 90 - "Observability Performance Tests"
Cohesion: 0.27
Nodes (7): _Client, _Observation, Any, MonkeyPatch, Performance contracts for shared observability., Trace completion must leave network delivery to the runner worker., test_trace_context_does_not_flush_synchronously()

### Community 91 - "UA Layer Assignment"
Cohesion: 0.20
Nodes (8): byLayer, fileTypes, fs, graph, [graphPath, outputPath], ids, layers, result

### Community 92 - "Analyst Settings"
Cohesion: 0.22
Nodes (8): BaseSettings, ensure_directories(), Application configuration and structured logging setup. All settings are loaded…, Centralised application settings. Values are read from environment variables…, Configure application-wide logging with a structured formatter. Idempotent —…, Create the upload and output directories if they don't yet exist., Settings, setup_logging()

### Community 93 - "Workflow Analysis Tool"
Cohesion: 0.61
Nodes (8): _average(), _group_by(), _min_max(), _numeric_values(), _parse_csv(), run(), _summarize(), _trends()

### Community 94 - "Parallel Critic Node"
Cohesion: 0.39
Nodes (7): _build_prompt(), critic_node(), _critique_single(), parallel_critic_node(), ResearchState, Critique one finding. Returns *(task, approved, critique_text)*., Review all findings concurrently using threads.

### Community 95 - "Parallel Researcher Node"
Cohesion: 0.39
Nodes (7): _build_prompt(), parallel_researcher_node(), ResearchState, Research a single task. Returns *(task, finding)*., Research all pending tasks concurrently using threads., _research_single(), researcher_node()

### Community 96 - "UI Builder Documentation"
Cohesion: 0.29
Nodes (8): Fixer Loop, JSON UI Spec, Structured UI Generation Pipeline, Generative UI Builder, Generative UI Builder Implementation Tasks, LangGraph Data Analyst, Validation Retry Loop, LangGraph Data Analyst Dependencies

### Community 97 - "Portfolio Architecture UI"
Cohesion: 0.39
Nodes (5): ArchitectureDiagram(), DiagramStep, stepIndex(), STEPS, metadata

### Community 98 - "UA Batch Complexity"
Cohesion: 0.39
Nodes (7): batches, complexity(), nodeFor(), summaryFor(), tagsFor(), typeFor(), ua

### Community 99 - "NL2SQL Documentation"
Cohesion: 0.29
Nodes (7): NL2SQL Security Boundary, Query Executor, Result Summarizer, Schema Loader, SQL Generator, SQL Validator, NL2SQL Agent

### Community 100 - "Benchmark Datasets"
Cohesion: 0.29
Nodes (7): Model Comparison Evaluation, Code Generation Prompt, Research Report Prompt, Summarization Prompt, Code Test Cases, Research Test Cases, Summarization Test Cases

### Community 101 - "Content Crew Documentation"
Cohesion: 0.29
Nodes (7): Editor Agent, Researcher Agent, SEO Expert Agent, Sequential Crew, Writer Agent, Content Pipeline, Implementation Plan

### Community 102 - "Document Corpus Samples"
Cohesion: 0.29
Nodes (7): April Invoice INV-2026-0417, Meridian Retail Group, MSA-MRG-ODS-2026, Orion Data Systems, Master Services Agreement, Service Level Agreement, SOC 2 Type II Certification

### Community 103 - "Evaluation Runner"
Cohesion: 0.48
Nodes (6): _prepare_case(), Any, Shared evaluation helpers for task-level execution metrics., Run *task_fn* across a dataset and return structured metrics. The dataset may…, _run_case(), run_evaluation()

### Community 104 - "NL2SQL Security Tests"
Cohesion: 0.33
Nodes (4): parametrize, Security regression tests for the model-generated NL2SQL boundary., test_unsafe_queries_are_rejected_at_validator_and_sink(), test_valid_analytics_queries_remain_allowed()

### Community 105 - "Copilot Context Assembly"
Cohesion: 0.47
Nodes (5): build_context(), ContextChunk, _format_chunk(), _normalize_chunk_text(), TypedDict

### Community 106 - "Document Chunking"
Cohesion: 0.60
Nodes (5): chunk_document(), _chunk_sentences(), _is_heading(), _split_sections(), _split_sentences()

### Community 107 - "Document Embeddings"
Cohesion: 0.53
Nodes (5): batch_embeddings(), _embed_batch(), generate_embedding(), Exception, _should_retry()

### Community 108 - "Data Agent Charts"
Cohesion: 0.47
Nodes (5): generate_chart(), _infer_chart_type(), DataFrame, Matplotlib chart generation from execution results., Generate a chart from execution_result and save to output_path. Returns the…

### Community 109 - "Database Initialization"
Cohesion: 0.33
Nodes (6): _ensure_run_column(), _ensure_run_json_column(), init_db(), Add a JSON-backed text column to ``runs`` for existing SQLite databases., Add a column to ``runs`` if it does not already exist., Create database tables on startup.

### Community 110 - "Production Stack Security"
Cohesion: 0.40
Nodes (5): PostgreSQL, Production Compose Stack, Redis RQ Worker, Bring Your Own Key, BYOK Handling

### Community 111 - "Financial Analysis Docs"
Cohesion: 0.50
Nodes (5): Financial Analyzer, Data Loader, Forecaster, Metrics Engine, Financial Reporter

### Community 112 - "Research Writer Node"
Cohesion: 0.60
Nodes (4): _build_prompt(), ResearchState, _scenario_prompt(), writer_node()

### Community 113 - "Research Planner"
Cohesion: 0.60
Nodes (4): _build_prompt(), create_plan(), _parse_tasks(), Planning utilities for research task generation.

### Community 114 - "Research Revision Docs"
Cohesion: 0.40
Nodes (5): Bounded Revision Loop, Critic Node, Planner Node, Researcher Node, Writer Node

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
Nodes (3): Path, Return a writable directory for the SQLite database. On read-only filesystems…, _resolve_data_dir()

## Knowledge Gaps
- **279 isolated node(s):** `root`, `ua`, `all`, `batches`, `root` (+274 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `set_byok_api_key()` connect `BYOK Project Entrypoints` to `Financial Analyst Runtime`, `Model Instrumentation Dependencies`, `API Response Models`, `NL2SQL Agent Runtime`, `Knowledge OS Storage`, `Runtime Configuration Jobs`, `UI Builder Runtime`, `Clinical Assistant Runtime`, `Document Intelligence Runtime`, `Research Evaluation`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `reset_byok_api_key()` connect `BYOK Project Entrypoints` to `Financial Analyst Runtime`, `Model Instrumentation Dependencies`, `API Response Models`, `NL2SQL Agent Runtime`, `Knowledge OS Storage`, `Runtime Configuration Jobs`, `UI Builder Runtime`, `Clinical Assistant Runtime`, `Document Intelligence Runtime`, `Research Evaluation`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `index_codebase()` connect `Code Copilot Indexing` to `Code Embeddings`, `Document Intelligence Runtime`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `root`, `ua`, `all` to the rest of the system?**
  _279 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LLM Provider Runtime` be split into smaller, more focused modules?**
  _Cohesion score 0.0575997515913678 - nodes in this community are weakly interconnected._
- **Should `Startup Simulator Crew` be split into smaller, more focused modules?**
  _Cohesion score 0.06832298136645963 - nodes in this community are weakly interconnected._
- **Should `Playground State Utilities` be split into smaller, more focused modules?**
  _Cohesion score 0.07738095238095238 - nodes in this community are weakly interconnected._