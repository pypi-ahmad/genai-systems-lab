# GenAI Systems Lab — Product Improvement Roadmap

> Planning document only. No code changes. Grounded entirely in the current codebase.

---

## 1. Objective

### What we are trying to improve

Transform the portfolio from a technically impressive demo environment into an app that a non-technical hiring manager, investor, or business stakeholder can navigate, understand, and operate without needing to read source code or understand agentic AI terminology.

### Target users

| User | What they need |
| --- | --- |
| **Non-technical evaluator** (recruiter, hiring manager) | Quick understanding of what the 20 systems do, confidence that the work is real, ability to try a demo without getting stuck |
| **Technical evaluator** (engineering lead, architect) | Depth on architecture, clean execution flow, and the ability to dig into advanced features when they want to |
| **Business stakeholder** (investor, product lead) | Professional polish, clear value narrative, trust signals, and a sense of product maturity |

### What "business-friendly" and "non-technical-user-friendly" mean here

- A first-time visitor can go from landing page to a successful demo run in under 2 minutes without outside help
- Every label, message, and button makes sense to someone who has never used an API key before
- The app communicates competence and care — no raw error codes, no unexplained jargon, no dead ends
- Advanced features (replay, sessions, explanations) are discoverable but never in the way

---

## 2. Current-State Summary

### The app today

A Next.js 16 portfolio and live execution environment for 20 AI systems across three paradigms (GenAI, LangGraph, CrewAI). Users supply their own API key, select a project, send input, and watch real-time streaming output with animated execution graphs, memory traces, timeline replay, and AI-generated run explanations. Authentication is optional and enables run history and multi-turn sessions.

### Biggest UX / business-readiness gaps

| Gap | Detail |
| --- | --- |
| **No onboarding** | First-time visitors land on a hero page with two CTAs ("Browse Projects" / "Open Playground") but no guidance on what to expect, what an API key is, or how to get one before arriving at the playground |
| **Jargon throughout** | Labels like "Stream", "Session context", "thought / action / observation", "Confidence", and "Platform mix" assume familiarity with agentic AI patterns |
| **Technical error messages** | Users see raw HTTP status text ("401 Unauthorized: Invalid credentials"), environment variable names (`NEXT_PUBLIC_API_BASE_URL`), and internal URL lists in error messages |
| **Validation gaps** | JSON input validates only on submit with a generic message ("Input is not valid JSON") — no inline help, no line-level feedback; password requires minLength=8 but the requirement is invisible until the form fails |
| **Missing guidance in the playground** | No explanation of what "confidence" means, no estimated run time, no help text on the input field format, no hint about what "session context" does for new users |
| **Accessibility gaps** | No `aria-live` regions for async status changes, timeline progress bar is a custom `<div>` rather than a native range input, no `prefers-reduced-motion` support, potential contrast issues with muted text in dark mode |
| **Navigation label ambiguity** | "Comparison" doesn't say what is being compared; 8 nav links with no visual grouping or active-state indicator beyond color |

### Biggest first-time-user problems

1. Arriving at the playground with no API key and seeing "Invalid or expired API key" immediately — feels like an error, not an expected first step
2. Not knowing which project to pick from 20 options with no search, no difficulty indicator, and no "try this first" suggestion
3. Seeing a JSON textarea with example input but no explanation of what it does or what to change
4. Getting a failed run and seeing a raw error message with no recovery guidance
5. Advanced panels (memory trace, timeline, explanation) appearing without context — what are these panels and why should I care?

---

## 3. Guiding Principles

1. **Do not break working features** — every change must preserve current functionality; no rewrites of stable flows
2. **Simplify before adding** — reduce what is on screen before introducing new elements
3. **Reduce jargon** — replace technical terms with plain language; keep technical labels available as secondary detail
4. **Use better defaults** — pre-select the easiest project, auto-fill example input, default to stream mode, don't show "Invalid API key" before the user has had a chance to enter one
5. **Progressive disclosure** — keep advanced features (timeline replay, session context, run explanation, debug panel) available but secondary; don't overwhelm first-time users
6. **Make user intent clear** — every button, label, and message should answer "what will happen if I click this?"
7. **Improve trust and clarity first** — polish error handling, microcopy, and visual consistency before adding new features
8. **Respect accessibility** — semantic HTML, ARIA attributes, keyboard navigation, and motion preferences are baseline requirements, not extras

---

## 4. Prioritized Roadmap

### Phase 1 — Must-Do Now

**Goal:** Remove the biggest first-time-user blockers and the most visible UX gaps. After this phase, a non-technical user should be able to complete a demo run without confusion.

**Problems being solved:**
- Users see error-styled messages before they have done anything wrong
- No guidance on what to do first
- Jargon in the most visible labels
- Raw technical errors break trust
- Missing form validation feedback

**Specific changes recommended:**

| # | Change | Detail |
| --- | --- | --- |
| 1.1 | **Fix API key first-impression** | Do not show "Invalid or expired API key" on initial load when the field is simply empty. Show neutral placeholder text instead: "Paste your API key to get started". Show the error only after the user has attempted a run or blurred an empty field. |
| 1.2 | **Add "Get started" guidance to playground** | Above the project list, add a short 3-step inline guide: ① Pick a project → ② Enter your API key → ③ Press Send. Dismissible, remembers dismissal in localStorage. |
| 1.3 | **Recommend a starter project** | Pin one project (e.g., "Multi-Agent Research System") at the top of the list with a "Recommended for first run" badge. This eliminates the 20-option paralysis. |
| 1.4 | **Humanize error messages** | Replace raw HTTP error text with mapped messages: 401 → "Your API key was not accepted. Double-check it and try again." / 429 → "Rate limit reached. Wait a moment and try again." / 500 → "Something went wrong on the server. Try again in a few seconds." / Network error → "Cannot reach the backend. Make sure the server is running." Remove environment variable names from user-facing messages entirely. |
| 1.5 | **Move API key help text before the input** | Currently "Your key is kept only in memory for this browser session" appears below the input. Move it above, alongside the "Get API key →" link, so users see privacy assurance before they paste anything. |
| 1.6 | **Add inline JSON validation** | Validate JSON on blur or on a 500ms debounce while typing. Show a specific error: "Invalid JSON on line 3: unexpected comma". Use the browser's built-in `JSON.parse` error message, cleaned up. |
| 1.7 | **Rename confusing labels** | "Stream" checkbox → "Live streaming" (with subtitle: "See output as it generates") / "Comparison" nav link → "LangGraph vs CrewAI" / Memory entry types: "thought" → "Reasoning", "action" → "Action taken", "observation" → "Result received" |
| 1.8 | **Show password requirements upfront** | On the auth form, add help text below the password field: "At least 8 characters". Show inline validation as the user types. |
| 1.9 | **Add nav active-state indicator** | Currently the active page has no visual differentiation beyond subtle color. Add an underline or background highlight to the current nav link. |

**Expected user impact:** First-time users can reach a successful run without encountering a single confusing message. The playground feels guided rather than empty.

**Business impact:** High. The playground is the core demo surface. Every evaluator who tries the app hits these exact friction points.

**Implementation risk:** Low. All changes are copy, validation, and conditional rendering. No backend changes. No architectural changes.

**Dependencies:** None.

---

### Phase 2 — Should-Do Next

**Goal:** Polish the experience for returning users, improve discoverability of advanced features, and bring accessibility to baseline compliance. After this phase, the app should feel like a well-maintained product, not a portfolio project.

**Problems being solved:**
- Advanced features (replay, explanation, sharing) are invisible until a user stumbles on them
- Session and history UX uses internal terminology
- Accessibility gaps exclude users with disabilities and fail automated audits
- 20 projects with no search or filtering in the sidebar

**Specific changes recommended:**

| # | Change | Detail |
| --- | --- | --- |
| 2.1 | **Add project search to sidebar** | Add a search/filter field above the 20-project list. Match against project name and category. Reduces scroll and lets users find systems by keyword. |
| 2.2 | **Add contextual tooltips to advanced features** | First time the memory panel, timeline replay, or explanation appears, show a subtle one-line tooltip: "This shows the agent's internal reasoning step by step" / "Scrub through the execution timeline" / "AI-generated summary of what happened". Dismissible, remembers dismissal. |
| 2.3 | **Clarify session terminology** | "Session active" → "Conversation active — previous messages will be included" / "Session idle" → "No active conversation" / "Last few interactions are ready for reuse" → "Previous messages in this conversation (showing last 5)" / "Clear session" → "Start new conversation" |
| 2.4 | **Add `aria-live` regions** | Mark the streaming status badge, debug panel, and explanation loading state as `aria-live="polite"` so screen readers announce state changes. |
| 2.5 | **Convert timeline scrubber to native range input** | Replace the custom `<div>` click handler with `<input type="range">` for keyboard accessibility and screen reader support. Style with CSS to match the current visual. |
| 2.6 | **Add `prefers-reduced-motion` support** | Wrap all CSS animations (blink, fade, card lift, grid animation) in a `@media (prefers-reduced-motion: no-preference)` block. Disable transitions for users who have requested reduced motion. |
| 2.7 | **Add confirmation for destructive actions** | "Re-run" from a saved run should confirm: "This will replace your current output. Continue?" / "Clear session" already shows "Clearing..." but should confirm first if there are unsaved results. |
| 2.8 | **Explain "confidence" to users** | Add a small info icon next to the confidence percentage. On hover/click, show: "Confidence reflects the system's self-assessed certainty in its output. Higher is better." |
| 2.9 | **Dark mode contrast audit** | Verify all `--muted` text and error colors meet WCAG AA (4.5:1 for normal text) against their backgrounds. Adjust tokens as needed. The current `#98a4b3` on dark backgrounds is borderline. |
| 2.10 | **Add loading duration estimate for explanations** | The explanation panel shows "Generating..." with no time context. Add: "This usually takes 15–30 seconds." |

**Expected user impact:** Returning users discover features they missed on first visit. Accessibility-dependent users can operate the full app. Session behavior is no longer confusing.

**Business impact:** Medium-high. Accessibility compliance is increasingly a hard requirement for enterprise evaluations. Session clarity removes a recurring confusion point.

**Implementation risk:** Low-medium. Accessibility changes require careful testing. Confirmation dialogs need to not break the run flow. Tooltip dismissal state needs localStorage management.

**Dependencies:** Phase 1 should be complete first so the baseline experience is solid before adding discoverability layers.

---

### Phase 3 — Nice-to-Have Later

**Goal:** Elevate the app from "well-polished portfolio" to "could be a real product". These are enhancements that add business value but are not blocking any current user flow.

**Problems being solved:**
- No way to quickly understand what a project does without reading its detail page
- No social proof or trust signals
- Metrics page is useful but not actionable
- Architecture page is passive

**Specific changes recommended:**

| # | Change | Detail |
| --- | --- | --- |
| 3.1 | **Add "quick preview" to project cards** | On hover or on a secondary click, show a popover with: 1-line description, expected run time, difficulty level, and a "Try it" button that opens the playground pre-configured. |
| 3.2 | **Add run count / success badges to project cards** | Show "142 runs · 94% success" on each project card. Data already exists in the metrics backend. Builds social proof and trust. |
| 3.3 | **Add CSV/JSON export to metrics** | "Export" button on the metrics dashboard to download chart data. Useful for stakeholders who want to include metrics in reports. |
| 3.4 | **Add copy buttons to code blocks** | On the project detail page, add a copy button to example input/output code blocks. Small convenience, high polish signal. |
| 3.5 | **Add breadcrumbs to detail pages** | Projects → genai-research-system. Helps with spatial orientation, especially on direct-link visits. |
| 3.6 | **Architecture diagram interaction improvements** | Add zoom/pan controls. On click, show a detail panel with the component's purpose and links to the relevant project pages. |
| 3.7 | **Home page trust signals** | Add a "Built with" section showing the tech stack with version badges. Add links to the GitHub repo. Show aggregate stats: total runs executed, average confidence, uptime (if available). |
| 3.8 | **Onboarding modal for first-time visitors** | A lightweight 3-step modal: "Welcome → Here's what you can do → Get your API key". Shown once, dismissed permanently. Lower priority because the inline playground guide (1.2) should handle most of this. |

**Expected user impact:** The app feels mature and trustworthy. Visitors understand the scope of work faster. Metrics become shareable.

**Business impact:** Medium. These are differentiation features, not blockers.

**Implementation risk:** Low. All additive. No existing flows are modified.

**Dependencies:** Phase 1 and 2 should be complete. Run count badges (3.2) depend on the metrics API being reliable.

---

## 5. Workstream Breakdown

### WS-1: UX / Navigation

**Why it matters:** Navigation is the skeleton of the app. Unclear nav labels and missing active states make users feel lost.

**Top improvements:**
- Add active-state indicator to current nav link (1.9)
- Rename "Comparison" → "LangGraph vs CrewAI" (1.7)
- Add breadcrumbs to detail pages (3.5)
- Add project search in playground sidebar (2.1)

**Priority:** High (Phase 1–2)
**Risk:** Low

---

### WS-2: Forms / Validation

**Why it matters:** The playground input and auth forms are the two most critical interaction points. Validation gaps cause silent failures and confusion.

**Top improvements:**
- Inline JSON validation with line-level errors (1.6)
- Password requirements shown upfront (1.8)
- Fix API key empty-state messaging (1.1)
- Confirmation for destructive actions (2.7)

**Priority:** High (Phase 1)
**Risk:** Low — validation is additive, does not change submission logic

---

### WS-3: Copy / Labels / Microcopy

**Why it matters:** Every label and message is a conversation with the user. Technical jargon and raw error codes break trust instantly.

**Top improvements:**
- Humanize error messages (1.4)
- Rename "Stream" → "Live streaming", memory entry types, session labels (1.7, 2.3)
- Move API key help text above input (1.5)
- Add confidence explanation tooltip (2.8)
- Add duration estimate for explanation generation (2.10)

**Priority:** High (Phase 1–2)
**Risk:** Very low — copy changes only

---

### WS-4: Onboarding / Guidance

**Why it matters:** The gap between "land on the page" and "complete a successful run" is too large for non-technical users.

**Top improvements:**
- 3-step inline guide in the playground (1.2)
- Recommended starter project (1.3)
- Contextual tooltips for advanced features (2.2)
- Onboarding modal for first-time visitors (3.8)

**Priority:** High (Phase 1), Medium (Phase 2–3)
**Risk:** Low — all dismissible, localStorage-persisted

---

### WS-5: Settings / Configuration Simplification

**Why it matters:** Environment variable names and internal URLs should never appear in user-facing messages.

**Top improvements:**
- Remove `NEXT_PUBLIC_API_BASE_URL` and `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` from all user-facing error messages (1.4)
- Simplify model selection: default to the most common model, collapse provider details behind an "Advanced" toggle

**Priority:** High (Phase 1)
**Risk:** Low

---

### WS-6: Trust / Professionalism / Polish

**Why it matters:** Small polish details (active nav states, copy buttons, trust signals) compound into a perception of product maturity.

**Top improvements:**
- Nav active state (1.9)
- Run count badges on project cards (3.2)
- Copy buttons on code blocks (3.4)
- Home page trust signals (3.7)

**Priority:** Medium (Phase 2–3)
**Risk:** Very low

---

### WS-7: Accessibility / Readability

**Why it matters:** Accessibility is both an ethical baseline and increasingly a hard requirement for enterprise evaluations. Current gaps would fail an automated WCAG audit.

**Top improvements:**
- `aria-live` regions for async status (2.4)
- Native range input for timeline scrubber (2.5)
- `prefers-reduced-motion` support (2.6)
- Dark mode contrast audit (2.9)

**Priority:** Medium-high (Phase 2)
**Risk:** Medium — contrast changes could affect the visual design; test thoroughly

---

## 6. Quick Wins

Highest impact, lowest risk. Can be done independently, in any order.

| # | Change | Effort | Impact |
| --- | --- | --- | --- |
| 1.1 | Fix API key empty-state from error to neutral prompt | ~30 min | Eliminates the #1 first-impression problem |
| 1.5 | Move API key help text above the input field | ~15 min | Increases trust before key entry |
| 1.7 | Rename "Comparison" nav link → "LangGraph vs CrewAI" | ~5 min | Removes ambiguity from the most confusing nav label |
| 1.7 | Rename "Stream" checkbox → "Live streaming" with subtitle | ~10 min | Clarifies what the toggle does |
| 1.9 | Add nav active-state indicator | ~20 min | Helps orientation on every page |
| 1.8 | Show "At least 8 characters" below password field | ~10 min | Prevents the most common auth form failure |
| 2.10 | Add "Usually takes 15–30 seconds" to explanation loading | ~5 min | Sets expectations during a long wait |
| 2.3 | Rename "Clear session" → "Start new conversation" | ~5 min | Makes session management intuitive |

---

## 7. Risky or Sensitive Areas

| Area | Risk | Why | Safe approach |
| --- | --- | --- | --- |
| **Error message rewriting (1.4)** | Medium | The current api.ts error handling has fallback chains (local URLs, CORS hints). Rewriting messages without testing every failure path could hide real diagnostic information needed during development. | Keep the current detailed messages in the debug console (`console.error`). Show the simplified message in the UI. Add a "Show details" toggle for power users. |
| **JSON validation (1.6)** | Low-medium | Real-time validation on every keystroke could cause performance issues with large payloads. Debounce aggressively (500ms+). The validation should never prevent submission — it should warn, not block. | Validate on blur and on a 500ms debounce. Show warnings, not errors. Allow submission regardless — the server will catch true errors. |
| **Timeline scrubber replacement (2.5)** | Medium | The current custom div implementation has specific click-to-seek behavior. A native range input behaves differently (continuous drag, keyboard arrows). Visual styling of native range inputs varies across browsers. | Build the replacement behind a feature flag. Test on Chrome, Firefox, Safari, and Edge. Match the current visual as closely as possible with CSS. |
| **Dark mode contrast changes (2.9)** | Medium | Changing `--muted` and error color tokens affects every surface in the app. A value that fixes contrast in one context may look wrong in another. | Audit every usage of the affected tokens before changing values. Create a visual diff (screenshots) of all pages in both themes before and after. |
| **Confirmation dialogs (2.7)** | Low-medium | Adding a confirmation to "Re-run" introduces friction for power users who re-run frequently. | Make the confirmation skippable with a "Don't ask again" checkbox, persisted in localStorage. |
| **Renaming labels (1.7, 2.3)** | Low | If any external documentation, blog posts, or shared links reference the old labels, renaming could cause confusion. | Check if any public documentation uses the old terms. Update USAGE.md simultaneously. |

---

## 8. Suggested Rollout Order

The safest implementation sequence, minimizing risk of breaking existing functionality:

```
Week 1 — Copy & Labels (zero-risk, immediate clarity gains)
├── 1.7  Rename confusing nav/UI labels
├── 1.5  Move API key help text above input
├── 1.8  Show password requirements upfront
├── 2.10 Add duration estimate to explanation loading
└── 2.3  Rename session terminology

Week 2 — First-Impression Fixes (low-risk, high-impact)
├── 1.1  Fix API key empty-state messaging
├── 1.2  Add 3-step inline guide to playground
├── 1.3  Add recommended starter project badge
└── 1.9  Add nav active-state indicator

Week 3 — Error Handling & Validation (medium-risk, essential)
├── 1.4  Humanize error messages (with console fallback)
└── 1.6  Add inline JSON validation (debounced, warn-only)

Week 4 — Discoverability & Progressive Disclosure
├── 2.1  Add project search to sidebar
├── 2.2  Add contextual tooltips for advanced features
├── 2.7  Add confirmation for destructive actions
└── 2.8  Add confidence explanation tooltip

Week 5 — Accessibility Baseline
├── 2.4  Add aria-live regions
├── 2.5  Convert timeline scrubber to native range input
├── 2.6  Add prefers-reduced-motion support
└── 2.9  Dark mode contrast audit and fixes

Week 6+ — Polish & Enhancements (Phase 3)
├── 3.1  Quick preview on project cards
├── 3.2  Run count badges
├── 3.4  Copy buttons on code blocks
├── 3.5  Breadcrumbs
├── 3.7  Home page trust signals
└── 3.8  Onboarding modal
```

Each week is independently shippable. If any week's changes cause issues, they can be reverted without affecting other weeks.

---

## 9. Success Criteria

### Quantitative (measurable after implementation)

| Metric | Current state | Target |
| --- | --- | --- |
| Steps from landing page to first successful run | ~6 steps, with 2–3 confusion points | ≤ 4 steps, zero confusion points |
| User-facing error messages containing env var names or HTTP codes | Multiple (NEXT_PUBLIC_API_BASE_URL, 401, 500) | Zero |
| Technical jargon visible on initial playground load | 5+ terms (Stream, Session, thought/action/observation) | Zero without user action |
| WCAG AA contrast violations in dark mode | Unknown but likely 2–5 | Zero |
| `aria-live` regions for async state changes | Zero | All status changes announced |
| Form fields with invisible validation requirements | 2 (password, JSON input) | Zero |

### Qualitative

- A non-technical user can complete their first run by following only the on-screen guidance, without external documentation
- Error messages answer "what went wrong" and "what should I do" — never "what HTTP status code was returned"
- Advanced features (timeline, explanation, session) feel like discoverable bonuses, not mandatory complexity
- The app passes a WCAG AA automated audit with no critical violations
- A hiring manager reviewing the portfolio perceives it as a mature, well-maintained product

---

## 10. Final Recommendation

### Top 5 Actions

| Priority | Action | Rationale |
| --- | --- | --- |
| **1** | Fix API key empty-state messaging (1.1) | Eliminates the single most jarring first-impression problem — seeing an error before doing anything |
| **2** | Humanize all user-facing error messages (1.4) | Every failed run currently damages trust; friendly errors turn failures into guided recovery |
| **3** | Add 3-step inline guide + starter project recommendation (1.2 + 1.3) | Transforms the playground from "figure it out" to "follow along" for first-time users |
| **4** | Rename jargon labels across nav and playground (1.7 + 2.3) | Removes the constant low-grade confusion that makes non-technical users feel excluded |
| **5** | Add accessibility baseline: aria-live, native range input, reduced-motion (2.4–2.6) | Meets the minimum standard expected of a professional web application |

### Safest first step

**Week 1: Copy & label changes.** Renaming labels and moving help text are pure text changes with zero risk to functionality. They can be verified by visual inspection alone. They deliver immediate clarity gains.

### Highest business impact step

**Fix 1.1 + 1.2 + 1.3 together (the first-run experience).** When an evaluator opens the playground for the first time, the difference between "red error on an empty field + 20 unlabeled projects + no guidance" and "friendly prompt + recommended project + clear 3-step instructions" is the difference between "closed the tab" and "completed a demo and was impressed."
