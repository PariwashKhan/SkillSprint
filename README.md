# SkillSprint AI – Generative AI Powered Personalized Onboarding Platform

**Theme:** OnboardVerse  
**Category:** Generative AI PowerPlay  
**Competition:** TechWiz 7 / Aptech

## Overview

SkillSprint AI is a dual-pipeline Generative AI application that:

1. **Pipeline 1 (GenAI)**: Generates personalized onboarding plans, modules, checklists, tasks, quizzes and assessments from company documents.
2. **Pipeline 2 (Pure Python)**: Independently validates the GenAI output against a Role Requirement Matrix for coverage, traceability, contradictions, hallucinations, role relevance and duplicates.

No free-form GenAI text is accepted as final output. Everything is structured JSON + deterministic Python verification.

## Unique Company Pack

**Company Name:** NexusFintech Pvt. Ltd.  
**Industry:** Digital Banking & Fintech  
**Tagline:** Secure. Smart. Seamless.

We created a completely original set of 20+ documents, 10 job roles, 150+ requirements, conflicts, version changes and adversarial cases.

## Tech Stack

- Frontend: Streamlit (premium UI)
- Backend logic: Pure Python
- Document Processing: pdfplumber + python-docx
- GenAI: Google Gemini / OpenAI (configurable)
- Validation: Pydantic + custom Python rule engine
- Database: SQLite (easy upgrade to PostgreSQL)
- Charts: Plotly

## Quick Start

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY or OPENAI_API_KEY

streamlit run src/app.py
```

## Evaluator Login

- Admin: admin / admin123
- Reviewer: reviewer / review123
- Employee: emp001 / emp123

## Key Features Implemented

- PDF + DOCX upload, validation, parsing, chunking with full source traceability
- Document version control
- Role Requirement Matrix (ground truth)
- Structured GenAI JSON generation with schema validation + retry
- Independent Python validation pipeline (coverage, traceability, hallucination, contradiction, duplicate, role-relevance)
- GenAI vs Python comparison engine
- Verification statuses exactly as SRS
- Prompt injection protection
- Manual review workflow + audit trail
- Admin + Employee dashboards
- Policy update impact analysis + selective regeneration
- Reports export (CSV / Excel / PDF)
- Consistency score

## Project Structure

See the folders under `src/` – they map 1:1 to SRS requirements.

## AI Usage Declaration

See `AI_USAGE.md`

## Important Notes for Evaluators

- No hard-coded onboarding plans or scores.
- All generated content is source-grounded.
- Pipeline 2 never uses GenAI.
- Hidden evaluation documents can be uploaded without code changes.

---

Built for TechWiz 7 – Generative AI PowerPlay
