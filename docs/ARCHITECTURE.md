# Architecture — Nyaya Sathi

## 1. High-Level Flow

```
                         ┌─────────────────────┐
                         │   Frontend (Chat)    │
                         │  frontend/index.html │
                         └──────────┬───────────┘
                                    │ POST /api/chat
                                    ▼
                         ┌─────────────────────┐
                         │   Flask App          │
                         │   backend/app.py      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Orchestrator        │
                         │ (intent classifier)  │
                         └───┬───┬───┬───┬───────┘
             ┌───────────────┘   │   │   └───────────────┐
             ▼                   ▼   ▼                   ▼
     ┌───────────────┐  ┌─────────────┐  ┌─────────────┐ ┌──────────────┐
     │ RTI Drafting   │  │  Rights     │  │ Eligibility │ │ Form Filler  │
     │ Agent          │  │  Navigator  │  │ Reader      │ │ Agent        │
     └───────┬────────┘  └──────┬──────┘  └──────┬──────┘ └──────┬───────┘
             │                  │                │               │
             ▼                  ▼                ▼               ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │              Local Knowledge Base (backend/data/*.json)         │
     │   rti_departments.json | rights_faq.json | schemes.json         │
     └─────────────────────────────────────────────────────────────────┘
             │                  │                │               │
             └──────────────────┴────────┬───────┴───────────────┘
                                          ▼
                              ┌───────────────────────┐
                              │  Claude API wrapper     │
                              │ backend/utils/claude_client.py │
                              └───────────────────────┘
```

## 2. Components

### Orchestrator (`backend/app.py :: classify_intent`)
A lightweight keyword + Claude-assisted classifier that maps a free-text message to one
of `rti | rights | eligibility | form | unknown`. On `unknown`, the system asks one
clarifying question instead of guessing.

### Agents (`backend/agents/*.py`)
Each agent:
1. Pulls relevant records from its local JSON knowledge base (department directory,
   scheme rules, FAQ entries).
2. Builds a constrained prompt (system prompt + retrieved context + user message).
3. Calls Claude via `claude_client.py` to produce the citizen-facing draft.
4. Returns structured JSON (`{draft, citations, next_steps, confidence}`) so the
   frontend can render consistently across agents.

### Knowledge Base (`backend/data/*.json`)
Intentionally simple JSON files for the hackathon demo — designed so that swapping in a
real RAG pipeline (embedding + vector search over official PDFs/portals) only requires
replacing the `lookup_*` functions in each agent, not the agent interfaces.

### LLM Client (`backend/utils/llm_client.py`)
Single wrapper that every agent calls through `ask_claude()` / `ask_llm()`. Auto-detects
and routes to whichever provider is available, in priority order:
1. **Anthropic Claude** (`ANTHROPIC_API_KEY`) — paid, highest quality.
2. **Google Gemini** (`GEMINI_API_KEY`) — free tier via Google AI Studio; recommended
   for this hackathon since OOSC 4.0 is GDG-organized and encourages the Google stack.
3. **Groq** (`GROQ_API_KEY`) — free tier, OpenAI-compatible endpoint, fast Llama models.
4. **Ollama** (local server on `OLLAMA_HOST`) — free, fully offline, no API key at all.
5. **Mock mode** (nothing configured) — deterministic templated responses so judges can
   run the full demo offline / without any provider set up.

Any provider error (expired key, rate limit, network failure) is caught and the client
falls back to mock mode rather than crashing the demo mid-presentation. See
`README.md` → "LLM Provider Options" for setup steps for each.

### Frontend (`frontend/`)
Framework-free chat UI: message list + input box + "Download as PDF/Text" button for
the final RTI application / form. Kept intentionally simple so the demo focuses on
agent quality, not UI polish.

## 3. Data Flow Example — RTI Drafting

1. User: *"My ration card application has been pending for 3 months, how do I ask the
   government why?"*
2. Orchestrator classifies → `rti`.
3. RTI Agent looks up `rti_departments.json` → finds "Food, Civil Supplies & Consumer
   Affairs Department" contact + PIO details for the user's state.
4. RTI Agent prompts Claude with: user's issue + department template + RTI Act Section 6
   format rules.
5. Claude returns a formatted RTI application (addressee, subject, body, fee note).
6. Response returned to frontend with `citations: ["RTI Act 2005, Section 6(1)"]` and
   `next_steps: ["Pay ₹10 fee via IPO/court fee stamp", "Submit to PIO listed above"]`.

## 4. Safety & Groundedness Choices

- Agents are instructed (system prompt) to **only** assert facts present in the
  retrieved knowledge base context; anything else is flagged as "please verify with a
  legal aid clinic."
- No agent auto-submits anything — output is always a **draft for the citizen to
  review and file themselves** (or hand to a legal aid volunteer).
- Every response separates **what we're confident about** (grounded facts) from
  **general guidance** (best-effort), shown to the user as a `confidence` field.

## 5. Scalability Notes (Post-Hackathon)

- Replace JSON files with a vector DB (e.g. pgvector) indexed over scraped/official
  RTI directories, state tenancy acts, and scheme portals, refreshed on a schedule.
- Add a caching layer for repeated eligibility questions per scheme.
- Add async job queue for form-filling sessions that span multiple conversation turns
  over days (citizens rarely finish in one sitting).
