# Candidate Shortlist and Human Decision Capture

## Purpose

The shortlist links one production requirement to registered factories being considered as alternatives. It helps a user compare the existing capability-screen result and record a traceable human shortlist decision.

## Workflow

1. Select a saved production requirement.
2. Add registered factories to its shortlist. A factory can appear only once per requirement.
3. Review the existing capability-screen result alongside each candidate. The comparison still uses exact, case-insensitive labels and user-entered stated monthly capacity.
4. Record a named decision and rationale: `Under review`, `On hold`, `Selected`, or `Rejected`.
5. Read the decision history, including the previous status, new status, decision maker, rationale, and timestamp.

`Selected` and `Rejected` are final shortlist outcomes and lock further decisions on that record. `On hold` can return to `Under review` when new information is available.

## API

- `POST /requirements/{requirement_id}/candidates` — add a factory to a requirement shortlist.
- `GET /requirements/{requirement_id}/candidates` — list the requirement's candidates.
- `GET /candidates/{candidate_id}` — read one candidate and its decision history.
- `PATCH /candidates/{candidate_id}/decision` — record a named human decision and rationale.
- `GET /candidates/{candidate_id}/decisions` — read decision history.
- `DELETE /candidates/{candidate_id}` — delete a candidate and its child history.

## Interpretation and limits

A `Selected` status means only that a user selected the factory for further review. It is not supplier qualification, technical suitability, verified capacity, certification, customer approval, or authorization to transfer production. The comparison is a preliminary screen based on user-entered data. Decisions and rationales are user-entered records; this version does not authenticate reviewer identity or implement role-based permissions.
