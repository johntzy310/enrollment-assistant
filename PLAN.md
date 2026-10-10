# Sprint Plan - Enrollment Helpdesk Assistant

## User Stories
1. **Incoming Freshman**: As an incoming freshman, I want to ask about enrollment requirements and deadlines so that I can submit my documents on time.
   - *Acceptance Criteria 1*: App provides the required document list for fresh graduates.
   - *Acceptance Criteria 2*: App provides exact deadline dates.
2. **Parent**: As a parent, I want to inquire about tuition installment options so that I can plan our finances.
   - *Acceptance Criteria 1*: App states down payment and installment schedules clearly.
   - *Acceptance Criteria 2*: App returns accepted payment channels (cash, online, banks).
3. **Registrar Staff**: As a registrar staff member, I want to view common incoming query statistics on an admin dashboard so that we can address frequent issues proactively.
   - *Acceptance Criteria 1*: Admin dashboard shows category query breakdown.
   - *Acceptance Criteria 2*: Admin dashboard shows user satisfaction percentage.

## Backlog
- [x] Setup repository and environment
- [ ] Write `faq.json` knowledge base
- [ ] Build `/api/chat` RAG endpoint
- [ ] Train ML intent classifier (`train.py`)
- [ ] Build chat web interface & admin stats
- [ ] Perform guardrails testing (`EVAL.md`)
- [ ] Deploy to Render
- [ ] Complete reflection (`REFLECTION.md`)
