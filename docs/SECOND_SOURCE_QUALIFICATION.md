# Second-Source Qualification Workflow

## Purpose

This workflow tracks the human review needed when a factory is being considered as an alternative source for a production requirement. It links one existing production requirement to one registered factory and creates a checklist from a saved template. A standard seven-check template is supplied by default; custom templates can be created for different part types or review workflows.

## Reusable checklist templates

Templates have a name, description, and an ordered list of checklist items. Each item has a unique key and a title. Create custom templates for different part types or review workflows, then select one when starting a qualification. The standard template is protected from editing and deletion.

A qualification copies its selected template into its own checklist records when it starts. Later edits or deletion of a custom template do not change existing qualifications or their decision history.

## Standard qualification checklist

The default template starts with these seven checks:

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

- `GET /qualification-templates` — list saved checklist templates.
- `POST /qualification-templates` — create a template with `name`, optional `description`, and `items` (`check_key`, `title`).
- `GET /qualification-templates/{template_id}` — read a template.
- `PUT /qualification-templates/{template_id}` — update a custom template; the standard template is protected.
- `DELETE /qualification-templates/{template_id}` — delete a custom template; existing qualifications retain their copied checklist items.
- `POST /qualifications` — start a qualification using `requirement_id`, `factory_id`, and an optional `template_id`. Omitting `template_id` selects the standard template.
- `GET /qualifications` — list qualifications; optionally filter by `requirement_id`.
- `GET /qualifications/{qualification_id}` — read a qualification and its checklist/history.
- `PATCH /qualifications/{qualification_id}/checks/{check_id}` — update one checklist item.
- `POST /qualifications/{qualification_id}/decision` — record a human decision.
- `GET /qualifications/{qualification_id}/decisions` — read decision history.
- `DELETE /qualifications/{qualification_id}` — delete the qualification and its child records.

## Interpretation and limits

The checklist is configurable evidence-tracking scaffolding, not a universal manufacturing standard. A status, owner, due date, evidence reference, or decision is user-entered. The application does not inspect referenced documents, authenticate reviewers, validate engineering data, audit suppliers, confirm free capacity, or independently verify certifications. `Approved` means a named user recorded that decision in this prototype; it is not LineFlex certification or automatic authority to transfer production. Real supplier changes require the relevant engineering, quality, procurement, contractual, and customer approvals.

The current version uses local SQLite storage and does not include authentication, access control, file uploads, notifications, or multi-user concurrency controls.
