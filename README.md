# Nyaya Sathi — AI for Civic and Legal Empowerment

**Hackathon:** OOSC 4.0
**Problem Statement 3:** AI for Civic and Legal Empowerment
**Theme:** Civic Tech, Legal Access and Government Transparency

> "Nyaya" (न्याय) = Justice, "Sathi" (साथी) = Companion — an AI companion that turns
> bureaucratic and legal complexity into a clear, guided path for every citizen.

---

## 1. Problem

Citizens often have legitimate rights and entitlements — consumer protections, tenant
rights, RTI access, welfare eligibility — that go unused because navigating bureaucratic
and legal language is intimidating and time-consuming. Relevant information is scattered
across PDFs, notices, and portals that aren't designed to solve one person's specific
problem quickly.

## 2. What We Built

Nyaya Sathi is a conversational AI platform with four cooperating agents, all reachable
through one chat interface and one API:

| Agent | Illustrative Direction Covered | What it does |
|---|---|---|
| **RTI Drafting Agent** | RTI Drafting Agent | Turns a plain-language question into a properly formatted RTI application addressed to the correct department |
| **Rights Navigator** | Rights Navigator | Explains, in simple terms, what a person can do about a specific tenant, consumer, or workplace dispute, with cited legal basis |
| **Scheme Eligibility Reader** | Scheme Eligibility Reader | Answers "Am I eligible?" questions for welfare/government schemes in plain language |
| **Conversational Form-Filler** | Conversational Form-Filler | Interviews the user turn-by-turn and auto-populates an official form (JSON + human-readable draft) |

A lightweight **Orchestrator** classifies incoming user intent and routes it to the right
agent, so the citizen never has to know which "tool" solves their problem — they just ask.

## 3. Why This Matters

- Millions of RTI applications, tenancy disputes, and scheme applications fail or are
  never filed simply because the *process*, not the *right*, is the barrier.
- We deliberately ground every agent response in a **local knowledge base** (statutes,
  scheme rules, department directories) rather than open-ended generation, so answers are
  traceable and safer for high-stakes civic use.
- Designed for **low digital literacy**: short chat turns, plain language, regional
  language toggle hook, and a downloadable/printable final document.

## 4. Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full diagram and data flow.

```
User (chat/web) ─▶ Orchestrator ─▶ [ RTI Agent | Rights Navigator | Eligibility Reader | Form Filler ]
                                          │
                                          ▼
                          Local Knowledge Base (schemes.json, rti_departments.json,
                                                  rights_faq.json)
                                          │
                                          ▼
                              Claude (Anthropic API) — reasoning + drafting
```

## 5. Tech Stack

- **Backend:** Python, Flask, multi-provider LLM client (Anthropic Claude, **Google Gemini**, Groq, or local Ollama — auto-detected)
- **Frontend:** Vanilla HTML/CSS/JS chat widget (framework-agnostic, easy to demo)
- **Data:** JSON knowledge base (swap-in ready for a real vector DB / RTI directory API)
- **Tests:** `pytest` unit tests for agent routing and prompt construction

## 6. Project Structure

```
civic-legal-empowerment-ai/
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── docs/
│   ├── PROBLEM_STATEMENT.md      # verbatim brief + our interpretation
│   ├── ARCHITECTURE.md           # system design, data flow, diagram
│   ├── PITCH.md                  # 3-min pitch script / demo flow
│   └── API_DOCS.md               # REST endpoint reference
├── backend/
│   ├── app.py                    # Flask app, routes, orchestrator
│   ├── agents/
│   │   ├── rti_agent.py
│   │   ├── rights_navigator_agent.py
│   │   ├── eligibility_agent.py
│   │   └── form_filler_agent.py
│   ├── utils/
│   │   ├── claude_client.py      # Anthropic API wrapper
│   │   └── language_utils.py     # plain-language + i18n helpers
│   ├── data/
│   │   ├── schemes.json
│   │   ├── rti_departments.json
│   │   └── rights_faq.json
│   └── tests/
│       └── test_agents.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── scripts/
    ├── setup.sh
    └── run.sh
```

## 7. Quick Start

```bash
git clone <this-repo>
cd civic-legal-empowerment-ai
cp .env.example .env          # see section 8 below for LLM options — all optional
bash scripts/setup.sh         # creates venv + installs deps
bash scripts/run.sh           # starts Flask backend on :5000
# open frontend/index.html in a browser (or serve it with any static server)
```

The app **works with zero configuration** — with no `.env` values set at all, every
agent runs in a deterministic mock mode so the demo still runs end-to-end offline (see
`backend/utils/llm_client.py`).

## 8. LLM Provider Options (what to do when your API credits run out)

`backend/utils/llm_client.py` auto-detects which provider to use, in this order, so you
never have to touch agent code — just change `.env`:

| Priority | Provider | Cost | Setup |
|---|---|---|---|
| 1 | **Anthropic Claude** | Paid (free trial credits) | Set `ANTHROPIC_API_KEY` in `.env` |
| 2 | **Google Gemini** | **Free tier**, no credit card | Set `GEMINI_API_KEY` in `.env` — recommended for this hackathon (OOSC 4.0 is GDG-organized and encourages the Google stack) |
| 3 | **Groq** | **Free tier**, no credit card | Set `GROQ_API_KEY` in `.env` |
| 4 | **Ollama** | **Free, fully local**, no internet needed | Install Ollama, no key needed |
| 5 | **Mock mode** | Free, no LLM at all | Do nothing — this is the default |

### Recommended for this hackathon → Google Gemini (free, matches OOSC 4.0's Google focus)

1. Go to https://aistudio.google.com/apikey and sign in with a Google account (no credit card required).
2. Create an API key.
3. In `.env`, set:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Leave `ANTHROPIC_API_KEY` blank so Gemini takes priority.
5. Restart the backend (`bash scripts/run.sh` or the Windows equivalent). No code changes needed.

### If your Anthropic trial credits run out → switch to Groq (2 minutes, also free)

1. Go to https://console.groq.com/keys and sign up (no credit card required).
2. Create an API key.
3. In `.env`, set:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
4. Leave `ANTHROPIC_API_KEY` blank (or the app will try Anthropic first and fail over
   to mock instead of Groq — an empty Anthropic key is what lets Groq take priority).
5. Restart the backend (`bash scripts/run.sh`). No code changes needed.

Groq's free tier is generous and fast — a solid choice for a hackathon demo.

### Or run a model entirely locally with Ollama (no signup, no internet after setup)

1. Install Ollama: https://ollama.com (macOS/Windows/Linux).
2. Pull a model once:
   ```bash
   ollama pull llama3.1
   ```
3. Make sure Ollama is running (it usually auto-starts; otherwise `ollama serve`).
4. Leave `ANTHROPIC_API_KEY` and `GROQ_API_KEY` blank in `.env` — the app will detect
   the local Ollama server automatically and use it.
5. Restart the backend.

This is the best option if you want a demo that works with **no internet connection at
all** — useful for a hackathon venue with unreliable Wi-Fi.

### Forcing a specific provider

Set `LLM_PROVIDER=gemini` (or `anthropic` / `groq` / `ollama` / `mock`) in `.env` to
override auto-detection entirely.

### Checking which provider is active

- Visit `GET /api/health` — returns `{"status": "ok", "mode": "groq"}` (or whichever
  provider is live).
- The frontend footer also shows the active mode at the bottom of the chat window.

## 9. Publishing to GitHub

This folder is already a self-contained project with a `.gitignore` (excludes `.env`,
`__pycache__`, virtual envs) and an MIT `LICENSE`. To push it:

```bash
cd civic-legal-empowerment-ai
git init
git add .
git commit -m "Initial commit — Nyaya Sathi, AI for Civic and Legal Empowerment"

# Create a new empty repo on GitHub first (github.com/new), then:
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

**Before you push, double-check:**
- `.env` is NOT committed (it's in `.gitignore` — only `.env.example` should be tracked).
- If you ever accidentally committed a real API key, rotate/revoke it immediately in
  the provider's console and remove it from git history before making the repo public.
- Add your team name / hackathon track to the top of this README if the submission
  form asks for it.

Once pushed, your submission link is simply:
`https://github.com/<your-username>/<your-repo-name>`

## 10. Roadmap (Post-Hackathon)

- Swap JSON knowledge base for a proper RAG pipeline over official government PDFs/portals
- WhatsApp / IVR channel for low-connectivity users
- Multi-language support (Hindi, Kannada, Tamil, Marathi, Bengali to start)
- Human-in-the-loop review before final RTI/form submission
- Partnership with legal-aid NGOs for escalation of unresolved disputes

## 11. Team & Judging Notes

- All four illustrative directions from Problem Statement 3 are implemented as real,
  callable agents (not just mocked UI).
- Code is intentionally modular so judges can test each agent independently via
  `docs/API_DOCS.md`.
- See `docs/PITCH.md` for the exact demo script we'll walk through.

## License

MIT — see [`LICENSE`](LICENSE).
