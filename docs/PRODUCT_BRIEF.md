# LineFlex — Initial Product Brief

**Document status:** Draft  
**Project stage:** Research and product definition  
**Last updated:** November 2026

## 1. Product hypothesis

A manufacturing team may know that other suppliers or factories exist but still lack a clear, evidence-based view of whether a specific production requirement could be transferred, what information is missing, and which approvals remain outstanding.

LineFlex will explore a structured workflow to record manufacturing capabilities, model simple capacity scenarios, and track second-source readiness.

This is a product hypothesis. It must be tested against existing software and real workflows before claiming a market gap.

## 2. Target workflow

1. A user records a part or production requirement.
2. The user records relevant process, material, equipment, quality, and capacity requirements.
3. The user adds candidate factories or suppliers using verified or clearly labelled sample information.
4. LineFlex compares recorded fields and highlights missing information or mismatches.
5. The user records qualification tasks, evidence, owners, and approval status.
6. The team uses a checklist to coordinate next steps.

The system should distinguish between:
- **Matched:** recorded information appears to meet a stated field requirement.
- **Mismatch:** recorded information conflicts with a stated requirement.
- **Unknown:** evidence has not been entered or verified.
- **Pending approval:** a responsible customer or quality authority has not approved the change.

A field match must never be presented as proof of engineering compatibility.

## 3. Initial MVP scope

The first prototype should focus on three connected workflows.

### A. Capability registry
- Create and edit factory records.
- Record processes, machines, materials, certifications, and capacity.
- Identify the source and date of each data point.
- Mark information as sample, self-reported, or verified.

### B. Requirement comparison
- Create a simple production requirement.
- Compare it with factory capability records.
- Show matched, mismatched, and unknown fields.
- Explain why each field received its status.

### C. Second-source readiness tracker
- Add candidate suppliers against a requirement.
- Track required documents and qualification tasks.
- Assign an owner and due date.
- Show readiness as a checklist, not as an automated approval.

## 4. Explicitly out of scope for the first MVP

- Automated supplier certification or approval
- Guaranteed production compatibility
- Live ERP/MES integrations
- Automated purchasing or supplier contracting
- Real-time factory telemetry
- AI-generated engineering decisions
- A public supplier marketplace

These may be considered only after the basic workflow is useful and validated.

## 5. Core data entities

| Entity | Example fields |
|---|---|
| Factory | Name, location, contact reference, data status |
| Capability | Process, machine, material, tolerance field, evidence reference |
| Requirement | Part/process requirement, quantity, target date, constraints |
| Candidate | Factory, requirement, comparison status |
| Qualification task | Task, owner, due date, status, evidence |
| Evidence | Document name, type, issue date, expiry date, verification status |
| Scenario | Demand quantity, available capacity, assumptions, calculated result |

Sensitive customer drawings, proprietary specifications, and personal contact details should not be used in the public demo dataset.

## 6. Product principles

- Make unknown information visible instead of guessing.
- Keep assumptions and data sources traceable.
- Separate a data match from an actual technical approval.
- Use sample data for public demonstrations.
- Keep the first version small enough to test locally.
- Do not claim customer adoption, savings, or market validation without evidence.

## 7. Open questions

- Which manufacturing segment has the most repeatable version of this workflow?
- Which data fields are essential for a meaningful first comparison?
- How do customer-specific qualification rules differ?
- What do existing ERP, supplier-management, and sourcing tools already cover?
- Who would own the budget for this workflow?
- Would teams use a separate tool, or would integration into an existing system be necessary?
