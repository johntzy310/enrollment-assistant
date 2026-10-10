# Sprint Plan: Bayanihan College Enrollment Assistant

## User Stories
1. **As an incoming freshman**, I want to know the exact admission requirements so I don't miss any documents.
   - Acceptance Criteria 1: Assistant lists all required credentials clearly.
   - Acceptance Criteria 2: Assistant responds in under 3 seconds.
2. **As a parent**, I want to know the tuition payment schedule and options so I can budget accordingly.
   - Acceptance Criteria 1: Assistant provides installment breakdown.
   - Acceptance Criteria 2: Assistant indicates accepted payment methods.
3. **As registrar staff**, I want the assistant to admit when it does not know an answer rather than hallucinating policies.
   - Acceptance Criteria 1: Out-of-bounds questions return a fallback statement.
   - Acceptance Criteria 2: FAQ source IDs are returned with every response.

## Task Backlog
- [x] Part A: Sprint Planning (Done)
- [x] Part B: Knowledge base (`faq.json`) (Done)
- [x] Part C: Grounded Chat API (`app.py`) (Done)
- [x] Part D: Intent Classifier (`intents.csv`, `train.py`) (Done)
- [x] Part E: Front-end UI and Stats (`/admin`) (Done)
- [x] Part F: Guardrails & Evaluation (`EVAL.md`) (Done)
- [x] Part G: Cloud Deployment (Render) (Done)
- [x] Part H: Ethics & Reflection (`REFLECTION.md`) (Done)
