# API Reference

Base URL (local): `http://localhost:5000`

All endpoints return JSON. All POST endpoints accept `Content-Type: application/json`.

---

## `POST /api/chat`
Main entry point. Routes to the correct agent automatically.

**Request**
```json
{
  "message": "My landlord is not returning my security deposit",
  "session_id": "demo-1",
  "language": "en"
}
```

**Response**
```json
{
  "agent": "rights_navigator",
  "draft": "...",
  "citations": ["Model Tenancy Act 2021, Section 16"],
  "next_steps": ["Send a written demand letter", "Approach Rent Authority if unresolved"],
  "confidence": "grounded"
}
```

---

## `POST /api/rti`
Directly invoke the RTI Drafting Agent.

**Request**
```json
{
  "issue": "My passport renewal has been pending for 2 months",
  "state": "Karnataka"
}
```

**Response**
```json
{
  "department": "Ministry of External Affairs, Regional Passport Office",
  "pio_contact": "...",
  "application_text": "To,\nThe Public Information Officer, ...",
  "fee_note": "₹10 via IPO / court fee stamp / online payment",
  "citations": ["RTI Act 2005, Section 6(1)"]
}
```

---

## `POST /api/rights`
Directly invoke the Rights Navigator.

**Request**
```json
{ "dispute_type": "tenant", "description": "Landlord withholding deposit after move-out" }
```

**Response**
```json
{
  "explanation": "...",
  "legal_basis": ["Model Tenancy Act 2021, Section 16"],
  "next_steps": ["...", "..."],
  "escalation_path": "Rent Authority / Rent Court"
}
```

---

## `POST /api/eligibility`
Directly invoke the Scheme Eligibility Reader.

**Request**
```json
{ "scheme": "PM-KISAN", "profile": {"land_acres": 1.5, "occupation": "farmer"} }
```

**Response**
```json
{
  "eligible": true,
  "reasoning": "...",
  "required_documents": ["Aadhaar", "Land records", "Bank account details"],
  "apply_link": "https://pmkisan.gov.in"
}
```

---

## `POST /api/form-filler`
Stateful, multi-turn conversational form filling.

**Request**
```json
{
  "session_id": "demo-1",
  "form_type": "rti_application",
  "answer": "Karnataka"
}
```

**Response**
```json
{
  "next_question": "What is the name of the department you want to ask?",
  "form_state": {"state": "Karnataka"},
  "complete": false
}
```

When `complete: true`, `form_state` contains the full populated form and a
`rendered_document` field with the final text.

---

## `GET /api/health`
Simple health check.

```json
{ "status": "ok", "mode": "mock" }
```
