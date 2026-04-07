# GenAI Systems Lab — Improvement Backlog

> Execution-ready backlog. Planning only — no code, no file changes.
> Every item is grounded in the actual app review and codebase audit.

---

## Full Backlog

| # | Item Title | Problem It Solves | User Type | Current Issue | Recommended Improvement | Expected Impact | Priority | Effort | Risk | Dependency | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B01 | Fix API key empty-state messaging | First-time users see an error before they have done anything | First-time, non-technical | On initial playground load with no key entered, the field shows a red ring and "Invalid or expired API key" — looks like something is broken | Show neutral placeholder "Paste your API key to get started". Only show the error after the user has attempted a run or blurred an empty field | Eliminates the #1 first-impression problem. Users feel welcomed, not reprimanded | P0 | Small | Low | None | Change is in playground-sidebar.tsx; conditional on whether the field has been touched |
| B02 | Humanize error messages | Raw HTTP status codes and env var names destroy trust | All users | Users see "401 Unauthorized: Invalid credentials", "500 Internal Server Error", and strings containing `NEXT_PUBLIC_API_BASE_URL` and `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | Map status codes to plain messages: 401 → "API key not accepted. Double-check and retry." / 429 → "Rate limit reached. Wait a moment." / 500 → "Server error. Try again shortly." / Network → "Cannot reach the backend." Keep raw details in `console.error` and behind a "Show details" toggle | Failed runs feel recoverable instead of catastrophic | P0 | Medium | Medium | None | Touches api.ts error handling chain. Must test all failure paths: bad key, expired key, rate limit, server down, CORS, empty stream |
| B03 | Add 3-step inline guide to playground | Playground offers no guidance on what to do first | First-time, non-technical | User lands on the playground and sees a sidebar with 20 projects, a JSON textarea, and a model dropdown — no instructions anywhere | Add a dismissible 3-step banner above the project list: "① Pick a project → ② Enter your API key → ③ Press Send". Remember dismissal in localStorage | First-time users have a clear path. Eliminates "what do I do?" moment | P0 | Small | Low | None | Keep it visually lightweight — inline hint, not a modal. Should not push project list below the fold |
| B04 | Recommend a starter project | 20 projects with no hierarchy causes decision paralysis | First-time, non-technical | Project list shows all 20 systems alphabetically by category. No indication which is simplest, fastest, or best for a first run | Pin one project (e.g., "Multi-Agent Research System") at the top with a "Recommended first run" badge. Pre-select it on first visit | Users start with a known-good project instead of picking randomly. Faster time-to-first-success | P0 | Small | Low | None | Choose the project with highest success rate and shortest median latency from metrics data |
| B05 | Move API key help text above the input | Users see the input field before knowing their key is safe | Non-technical, business | Privacy notice "Your key is kept only in memory for this browser session" currently appears below the API key field. "Get API key →" link also below | Move both the privacy notice and the "Get API key →" link above the input field so users read them before pasting | Users feel reassured before entering sensitive data. Small trust improvement | P0 | Small | Low | None | Pure DOM reorder in playground-sidebar.tsx |
| B06 | Rename "Comparison" nav link | Nav label doesn't say what is being compared | All users | Nav shows "Comparison" — could mean anything. User has to click to find out it's LangGraph vs CrewAI | Rename to "LangGraph vs CrewAI" | Immediate clarity. Users self-select if they're interested | P0 | Small | Low | None | Text change in layout.tsx. Update USAGE.md simultaneously |
| B07 | Rename "Stream" checkbox to "Live streaming" | "Stream" is vague technical jargon | Non-technical | Checkbox labeled "Stream" with no explanation of what it toggles | Rename to "Live streaming" with a subtitle: "See output as it generates" | Users understand what they're opting into | P0 | Small | Low | None | playground-sidebar.tsx, text change only |
| B08 | Rename memory panel entry types | "thought / action / observation" is agent jargon | Non-technical, business | Memory panel entries show type badges "thought", "action", "observation" — meaningful only to LLM developers | "thought" → "Reasoning" / "action" → "Action taken" / "observation" → "Result received" | Non-technical users can follow the agent's execution trace | P0 | Small | Low | None | memory-panel.tsx, label mapping only |
| B09 | Show password requirements upfront | Users fail auth form and don't know why | First-time | Password field has `minLength={8}` validated only on submit. No visible hint about requirements | Add help text "At least 8 characters" below the password field. Show inline check/cross as user types | Eliminates the most common auth form failure | P0 | Small | Low | None | auth-client.tsx, additive only |
| B10 | Add nav active-state indicator | Users can't tell which page they're on | All users | Active nav link has no underline, background, or weight change — only a subtle color difference that may not be perceptible | Add an underline or background-highlight to the current nav link using pathname matching | Immediate orientation improvement on every page | P0 | Small | Low | None | layout.tsx, CSS-only change using `usePathname()` already available in Next.js |
| B11 | Add inline JSON validation | Invalid JSON fails silently until submit | All users | User enters malformed JSON, presses Send, and gets "Input is not valid JSON" with no line reference | Validate on blur and on 500ms debounce. Show cleaned-up `JSON.parse` error with approximate line: "Syntax error near line 3: unexpected comma". Warn, don't block — allow submit regardless | Users fix input errors before hitting the server. Fewer wasted round trips | P1 | Medium | Low-Med | None | playground-sidebar.tsx. Debounce carefully to avoid lag on large payloads. Never block submission — the server is the authority |
| B12 | Add project search to playground sidebar | 20 projects in a scroll list with no filtering | Returning, technical | Project list shows all 20 in a 420px-max-height scrollable area (~5 visible at a time). No search or type-ahead | Add a text input above the project list that filters by name and category as user types | Returning users find projects instantly. Especially useful after initial exploration | P1 | Small | Low | None | playground-sidebar.tsx, client-side filter only |
| B13 | Add contextual tooltips for advanced features | Memory panel, timeline replay, and explanation panel are undiscoverable | First-time, non-technical | Advanced panels render after a run completes with no introduction. Non-technical users don't know what "memory trace" or "timeline replay" means | On first appearance of each panel, show a one-line tooltip: "This shows the agent's reasoning step by step" / "Scrub through the execution timeline" / "AI-generated summary of what happened". Dismissible, persisted in localStorage | Users engage with advanced features instead of ignoring them | P1 | Medium | Low | B03 (inline guide first) | Keep tooltips subtle — floating label, not a modal. Don't show all three at once |
| B14 | Clarify session terminology | Session labels use internal vocabulary | Non-technical | "Session active" / "Session idle" / "Last few interactions are ready for reuse" / "Clear session" — none of these are self-explanatory | "Session active" → "Conversation active — previous messages will be included" / "Session idle" → "No active conversation" / "Last few interactions are ready for reuse" → "Previous messages in this conversation (showing last 5)" / "Clear session" → "Start new conversation" | Session behavior becomes intuitive without reading docs | P1 | Small | Low | None | playground-sidebar.tsx, text changes only |
| B15 | Add `aria-live` regions for async status | Screen readers miss all status transitions | Accessibility | Streaming status badge, debug panel updates, and explanation loading state are all visually rendered but not announced to assistive tech | Add `aria-live="polite"` to the status badge container, explanation loading message, and debug panel log area | Screen reader users can follow run progress. Baseline accessibility compliance | P1 | Small | Low | None | Additive attribute changes. No visual or behavioral impact |
| B16 | Convert timeline scrubber to native range input | Custom div scrubber is inaccessible | Accessibility | Timeline progress bar is a `<div>` with a click handler. Not keyboard navigable. Not announced to screen readers | Replace with `<input type="range">`. Style with CSS to match current visual. Preserve click-to-seek behavior | Keyboard and screen reader users can operate timeline replay | P1 | Medium | Medium | None | Cross-browser styling of range inputs varies. Test on Chrome, Firefox, Safari, Edge. Build behind feature flag |
| B17 | Add `prefers-reduced-motion` support | Users with vestibular disorders are affected by animations | Accessibility | CSS animations (blink, fade, card lift, grid background) play unconditionally | Wrap all animation/transition declarations in `@media (prefers-reduced-motion: no-preference)` | Users who request reduced motion get a static experience. WCAG 2.1 AA compliance | P1 | Small | Low | None | globals.css only. Add the media query wrapper around existing `@keyframes` and `transition` rules |
| B18 | Add confirmation for destructive actions | "Re-run" and "Clear session" silently discard data | Returning users | "Re-run" from saved runs overwrites current output without warning. "Clear session" erases conversation context immediately | Show a confirmation: "This will replace your current output. Continue?" for Re-run. "Start a new conversation? Current context will be cleared." for Clear session. Add "Don't ask again" checkbox persisted in localStorage | Prevents accidental data loss for users with active work | P1 | Medium | Low-Med | None | Must not add friction for power users — the "Don't ask again" option is essential |
| B19 | Explain "confidence" metric | "Confidence: 87%" means nothing to non-technical users | Non-technical, business | Confidence score appears after runs as a percentage with a colored dot (green/yellow/red) but no explanation | Add a small ⓘ icon next to the score. On hover/click, show: "Confidence reflects the system's self-assessed certainty in its output. Higher is better." | Users understand a metric they currently ignore | P1 | Small | Low | None | confidence-indicator.tsx, additive tooltip only |
| B20 | Dark mode contrast audit | Muted text may fail WCAG AA contrast | Accessibility, all users | `--muted` color `#98a4b3` on dark backgrounds is borderline for WCAG AA (4.5:1 for normal text). Error red `#fca5a5` may also fail | Audit every usage of `--muted`, error, and warning color tokens against their actual backgrounds. Adjust values to meet 4.5:1 minimum | Dark mode is readable and accessible. Prevents WCAG audit failures | P1 | Medium | Medium | None | Changing color tokens affects every surface. Screenshot all pages in both themes before and after. |
| B21 | Add loading duration estimate for explanations | Users don't know how long the explanation generation takes | All users | Explanation panel shows "Generating a concise explanation from the saved run artifacts" with a spinner but no time estimate. Could be 15–60 seconds | Add: "This usually takes 15–30 seconds." below the loading message | Users wait patiently instead of assuming it's stuck | P1 | Small | Low | None | RunExplanation.tsx, text addition only |
| B22 | Add "quick preview" to project cards | Users must open each project detail page to understand it | First-time, business | Project cards on /projects show name, category badge, and 2-line description. No way to preview without navigating | On hover, show a popover with: 1-line summary, expected run time, and a "Try it" button that opens the playground pre-configured for that project | Users can browse 20 projects much faster. More likely to try a demo | P2 | Medium | Low | None | projects/page.tsx. Data already in project-catalog.json |
| B23 | Add run count / success badges to project cards | No social proof or trust signals on project cards | Business | Project cards show no indication of usage or reliability. Could be untested demos | Show "142 runs · 94% success" on each card. Data sourced from the existing metrics API | Builds trust. Shows the systems have been actually used and work reliably | P2 | Medium | Low | Metrics API must be reliable | Only show badges when data is available. Fall back to no badge, not "0 runs" |
| B24 | Add CSV/JSON export to metrics dashboard | Metrics data is locked in the UI | Business | Metrics dashboard shows charts for latency, confidence, and success rate, but there's no way to extract the underlying data | Add an "Export" button on the metrics page. Offer CSV and JSON download of the current chart data | Stakeholders can include metrics in reports and presentations | P2 | Medium | Low | None | Client-side only — serialize the chart data array to CSV/JSON and trigger a download |
| B25 | Add copy buttons to code blocks | Example code is not easily copyable | Technical, first-time | Project detail pages show example input/output in `<pre>` blocks with no copy affordance | Add a copy button (top-right corner of each code block) that copies contents to clipboard with a "Copied ✓" confirmation | Small convenience that signals professional polish | P2 | Small | Low | None | Reusable component. Applies to project detail pages and playground examples |
| B26 | Add breadcrumbs to project detail pages | Users lose spatial orientation on detail pages | All users | Navigating from /projects to /projects/genai-research-system shows no breadcrumb trail. No easy back-navigation | Add "Projects → Project Name" breadcrumb at the top of detail pages | Better orientation, especially for direct-link visitors | P2 | Small | Low | None | projects/[slug]/page.tsx, additive only |
| B27 | Architecture diagram zoom/pan controls | Architecture diagram is static and dense | Technical, business | Interactive architecture page renders boxes with hover highlighting but no zoom/pan. Dense on small screens | Add zoom in/out buttons and drag-to-pan. Show a detail side panel on component click with purpose and links to related projects | Architecture page becomes genuinely useful for understanding the system | P2 | Large | Low | None | Significant interaction work. Consider a library like react-zoom-pan-pinch |
| B28 | Home page trust signals | Landing page lacks credibility markers | Business | Home page shows stats (20 systems, 3 paradigms) and 4 capability cards but no links to source code, no tech stack badges, no aggregate run stats | Add a "Built with" section (tech stack with version badges), a GitHub repo link, and aggregate stats (total runs executed, average confidence) if available from metrics API | Visitors perceive the project as real and well-maintained, not a template | P2 | Medium | Low | Metrics API for run stats | If metrics aren't available, show tech stack and GitHub link only — don't fabricate numbers |
| B29 | Onboarding modal for first-time visitors | First-time visitors have no context before the playground | First-time | Visitor lands on the home page or playground with no introduction to the app, what BYOK means, or what they can do | A lightweight 3-step dismissible modal: "Welcome → Here's what you can do → Get your API key". Shown once, remembered in localStorage | Gentle introduction. Lower priority because the inline playground guide (B03) handles most of this | P2 | Medium | Low | B03 (inline guide first) | Only pursue if B03 alone proves insufficient. Don't stack onboarding layers |

---

## Ranked Lists

### Top 10 Most Important Backlog Items

| Rank | Item | Why |
|------|------|-----|
| 1 | **B01** — Fix API key empty-state messaging | Single most jarring first-impression issue. Every new user hits this. Easiest to fix. |
| 2 | **B02** — Humanize error messages | Every failed run currently shows raw HTTP text. Damages trust with every failure. |
| 3 | **B03** — Add 3-step inline guide to playground | Transforms the playground from "figure it out" to "follow these steps" for first-time users. |
| 4 | **B04** — Recommend a starter project | Eliminates 20-project paralysis. Directly improves time-to-first-success. |
| 5 | **B08** — Rename memory panel entry types | Memory panel is one of the most unique features but its labels are opaque to non-developers. |
| 6 | **B05** — Move API key help text above input | Privacy assurance before key entry builds trust at a critical moment. |
| 7 | **B11** — Add inline JSON validation | Prevents the most common payload error. Saves round trips and user frustration. |
| 8 | **B14** — Clarify session terminology | Session is a key differentiator (multi-turn context) but its labels currently confuse rather than explain. |
| 9 | **B15** — Add `aria-live` regions | Baseline accessibility. Without this, screen reader users cannot follow execution at all. |
| 10 | **B10** — Add nav active-state indicator | Affects every page visit. Small effort, universal benefit. |

---

### Top 5 Safest Quick Wins

Items that deliver immediate improvement with near-zero risk to existing functionality.

| Rank | Item | Effort | Why Safe |
|------|------|--------|----------|
| 1 | **B06** — Rename "Comparison" → "LangGraph vs CrewAI" | Small | Single text change in layout.tsx. No logic affected. |
| 2 | **B07** — Rename "Stream" → "Live streaming" | Small | Text and subtitle change. Checkbox behavior unchanged. |
| 3 | **B21** — Add duration estimate for explanation loading | Small | One line of text added to RunExplanation.tsx. No logic. |
| 4 | **B09** — Show password requirements upfront | Small | Help text addition. Existing validation untouched. |
| 5 | **B05** — Move API key help text above input | Small | DOM reorder. No logic or state changes. |

---

### Top 5 Highest Business-Value Improvements

Items that most improve the perception of the app as a mature, professional product.

| Rank | Item | Why High Business Value |
|------|------|----------------------|
| 1 | **B02** — Humanize error messages | Error quality is the single strongest proxy for product maturity. Raw HTTP codes signal "student project". Friendly recovery messages signal "production software". |
| 2 | **B01** — Fix API key empty-state messaging | The playground is the demo surface. The first 5 seconds determine whether an evaluator stays. A red error on load says "broken". |
| 3 | **B23** — Add run count / success badges | Social proof. "142 runs · 94% success" tells a business evaluator the systems are tested and working, not theoretical. |
| 4 | **B28** — Home page trust signals | Tech stack badges, GitHub link, and aggregate stats are credibility markers that business visitors expect. |
| 5 | **B03** — Add 3-step inline guide | A guided first experience converts "I'll check this later" into "I just ran a live AI demo in 60 seconds". |

---

### Top 5 Improvements for First-Time Non-Technical Users

Items that reduce the most friction for someone who has never used an API, LLM, or agentic system.

| Rank | Item | Why It Helps This User |
|------|------|----------------------|
| 1 | **B01** — Fix API key empty-state messaging | "Invalid or expired API key" on a blank field feels like a broken app to someone unfamiliar with APIs. A neutral prompt feels like guidance. |
| 2 | **B03** — Add 3-step inline guide | This user does not know the workflow. "Pick a project → Enter key → Press Send" is the minimum viable instruction. |
| 3 | **B04** — Recommend a starter project | This user cannot evaluate 20 AI systems to choose one. "Start here" eliminates the choice entirely. |
| 4 | **B08** — Rename memory panel entry types | "thought / action / observation" is meaningless to this user. "Reasoning / Action taken / Result received" is immediately understandable. |
| 5 | **B19** — Explain "confidence" metric | "Confidence: 87%" with a green dot means nothing without context. The tooltip makes the metric informative instead of decorative. |

---

### Recommended Sprint Order

Sprints are sized to be independently shippable. Each preserves all existing functionality.

---

**Sprint 1 — Zero-Risk Label & Copy Fixes**
*Goal: Immediate clarity gains with no logic changes.*

| Item | Description |
|------|-------------|
| B06 | Rename "Comparison" → "LangGraph vs CrewAI" |
| B07 | Rename "Stream" → "Live streaming" with subtitle |
| B08 | Rename memory entry types: thought → Reasoning, action → Action taken, observation → Result received |
| B14 | Clarify session terminology (4 label renames) |
| B05 | Move API key help text above the input field |
| B09 | Show password requirements ("At least 8 characters") below field |
| B21 | Add "This usually takes 15–30 seconds" to explanation loading |

**Verification:** Visual inspection only. All changes are text/DOM order. No behavior changes.

---

**Sprint 2 — First-Impression Fixes**
*Goal: A non-technical user can reach a successful run on first visit.*

| Item | Description |
|------|-------------|
| B01 | Fix API key empty-state from error to neutral prompt |
| B03 | Add 3-step inline guide to playground (dismissible, localStorage) |
| B04 | Add recommended starter project badge + pre-selection |
| B10 | Add nav active-state indicator |

**Verification:** Open playground in a clean browser (no localStorage). Confirm neutral API key state, visible guide, pre-selected project, and active nav highlight.

---

**Sprint 3 — Error Handling & Validation**
*Goal: Failures feel recoverable. Input errors are caught early.*

| Item | Description |
|------|-------------|
| B02 | Humanize all user-facing error messages (with console fallback + "Show details") |
| B11 | Add inline JSON validation (debounced, warn-only) |

**Verification:** Test every failure path: invalid key, expired key, rate limit, server down, CORS error, network timeout, empty stream, malformed JSON (missing bracket, trailing comma, wrong type). Confirm no env var names or HTTP codes in UI. Confirm raw errors still in console.

---

**Sprint 4 — Discoverability & Progressive Disclosure**
*Goal: Advanced features become self-explanatory. Destructive actions are safe.*

| Item | Description |
|------|-------------|
| B13 | Add contextual tooltips for memory panel, timeline, and explanation |
| B19 | Add confidence explanation tooltip (ⓘ icon) |
| B18 | Add confirmation for Re-run and Clear session (with "Don't ask again") |
| B12 | Add project search/filter to playground sidebar |

**Verification:** Run a project and confirm tooltips appear once, dismiss correctly, and persist dismissal. Test Re-run confirmation preserves active output. Test search against all 20 project names and categories.

---

**Sprint 5 — Accessibility Baseline**
*Goal: Pass a WCAG AA automated audit with zero critical violations.*

| Item | Description |
|------|-------------|
| B15 | Add `aria-live` regions to status badge, debug panel, explanation loading |
| B16 | Convert timeline scrubber to native `<input type="range">` |
| B17 | Add `prefers-reduced-motion` media query wrappers |
| B20 | Dark mode contrast audit and token adjustments |

**Verification:** Run axe-core or Lighthouse accessibility audit on playground, project detail, and metrics pages. Confirm zero critical/serious violations. Test timeline scrubber with keyboard (arrow keys). Test with `prefers-reduced-motion: reduce` enabled in OS settings.

---

**Sprint 6 — Polish & Trust Signals**
*Goal: The app feels like a maintained product, not a portfolio project.*

| Item | Description |
|------|-------------|
| B25 | Add copy buttons to code blocks on project detail pages |
| B26 | Add breadcrumbs to project detail pages |
| B23 | Add run count / success badges to project cards (metrics API dependent) |
| B28 | Home page trust signals (tech stack badges, GitHub link, aggregate stats) |

**Verification:** Confirm copy buttons work across browsers. Confirm breadcrumbs render correctly for all 20 project slugs. Confirm badges fall back gracefully when metrics API is unavailable.

---

**Sprint 7 — Enhancement Layer**
*Goal: Differentiation features that elevate beyond expectations.*

| Item | Description |
|------|-------------|
| B22 | Quick preview popover on project cards |
| B24 | CSV/JSON export on metrics dashboard |
| B27 | Architecture diagram zoom/pan controls |
| B29 | Onboarding modal (only if B03 proves insufficient) |

**Verification:** User testing with non-technical participants. Measure time-to-first-successful-run before and after B29.

---

## Success Criteria

The backlog is complete when:

1. A first-time non-technical user can go from landing page to a successful demo run following only on-screen guidance, with zero confusion points
2. No user-facing message contains an HTTP status code, environment variable name, or internal URL
3. Every interactive element has a visible label that a non-developer can understand
4. The app passes an axe-core accessibility audit with zero critical or serious violations
5. Every form shows its validation requirements before the user makes a mistake
6. Advanced features (timeline, explanation, session) each have a one-line explanation visible on first encounter
7. The playground loads without any error-styled elements before the user has taken an action
