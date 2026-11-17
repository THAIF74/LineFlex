# Second-Source Qualification Workflow

## Purpose

This workflow tracks the human review needed when a factory is being considered as an alternative source for a production requirement. It links one existing production requirement to one registered factory and creates a standard checklist.

## Qualification checklist

Each qualification starts with these seven checks:

1. Engineering drawing and specification review
2. Process capability review
3. Material and traceability review
4. Quality system and certification review
5. Capacity and lead-time review
6. Sample or first-article inspection
7. Customer approval and change-control review

Each item records a status (`Not started`, `In progress`, `Passed`, `Gap`, or `Not applicable`), an owner, due date, evidence reference, and notes. Due dates use `YYYY-MM-DD`.

When all items are `Passed` or `Not applicable`, the qualification moves to `Ready for review`. This is not an automatic approval.

## Human decisions

A named decision maker records a decision of `Approved`, `Rejected`, or `On hold`, together with a rationale. An `Approved` decision is blocked until every checklist item is `Passed` or `Not applicable`. Final `Approved` and `Rejected` records are locked against further checklist edits; a new qualification should be started for a later reassessment. Decision changes are stored in a history table.

## API

- `POST /qualifications` — start a qualification using `requirement_id` and `factory_id`.
- `GET /qualifications` — list qualifications; optionally filter by `requirement_id`.
- `GET /qualifications/{qualification_id}` — read a qualification and its checklist/history.
- `PATCH /qualifications/{qualification_id}/checks/{check_id}` — update one checklist item.
- `POST /qualifications/{qualification_id}/decision` — record a human decision.
- `GET /qualifications/{qualification_id}/decisions` — read decision history.
- `DELETE /qualifications/{qualification_id}` — delete the qualification and its child records.

## Interpretation and limits

The checklist is configurable evidence-tracking scaffolding, not a universal manufacturing standard. A status, owner, due date, evidence reference, or decision is user-entered. The application does not inspect referenced documents, authenticate reviewers, validate engineering data, audit suppliers, confirm free capacity, or independently verify certifications. `Approved` means a named user recorded that decision in this prototype; it is not LineFlex certification or automatic authority to transfer production. Real supplier changes require the relevant engineering, quality, procurement, contractual, and customer approvals.

The current version uses local SQLite storage and does not include authentication, access control, file uploads, notifications, or multi-user concurrency controls.
