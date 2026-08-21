# Problem Statement 3 — AI for Civic and Legal Empowerment

*Theme: Civic Tech, Legal Access and Government Transparency*

## Original Brief

**Problem Context**
Citizens often have legitimate rights and entitlements — consumer protections, tenant
rights, RTI access, welfare eligibility — that go unused because navigating bureaucratic
and legal language is intimidating and time-consuming. Relevant information is scattered
across PDFs, notices and portals that are not designed to solve a specific personal
problem quickly.

**Challenge Statement**
Build an AI system that helps a citizen understand and act on their civic or legal
rights, translating bureaucratic complexity into a clear, guided path.

**Illustrative Directions**
1. **RTI Drafting Agent** — converts a plain-language question into a properly formatted
   application to the right department.
2. **Rights Navigator** — explains, in simple terms, what a person can do about a
   specific tenant, consumer or workplace dispute.
3. **Scheme Eligibility Reader** — reads government portals and answers eligibility
   questions in plain language.
4. **Conversational Form-Filler** — interviews the user and auto-populates the official
   form.
5. Open reinterpretation of bureaucracy translation is welcome.

## Our Interpretation

We treat this as **one product surface with four specialized agents** behind it, because
in real life a citizen's problem rarely announces which "category" it falls into — they
just say "my landlord won't return my deposit" or "can I get this scholarship." An
orchestration layer classifies intent and hands off to the right specialist agent, then
the specialist grounds its answer in a small, auditable knowledge base (statutes, scheme
rules, department contact directory) before calling Claude to draft the citizen-facing
output.

We chose **groundedness over generality**: every agent response cites which rule/scheme/
department it used, rather than free-generating legal advice, because incorrect
"confident" answers are especially harmful in this domain.

## Success Criteria We Designed Against

- A non-technical user can go from "I have a problem" to "I have a filed-ready
  document" in under 5 conversational turns.
- Every RTI/form output is department-correct and includes the right legal citation
  (Section 6 of the RTI Act, relevant tenancy act, etc.).
- The system clearly says "I don't know, consult a lawyer/legal aid clinic" when a
  question falls outside its grounded knowledge base, instead of hallucinating.
- Works reasonably even for low digital-literacy users (short prompts, plain language,
  no jargon, regional-language ready).
