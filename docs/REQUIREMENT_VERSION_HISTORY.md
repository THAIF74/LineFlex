# Production Requirement Editing and Version History

## Purpose

This milestone allows a saved production requirement to be updated without deleting and recreating it. Each successful edit stores a complete snapshot so users can inspect earlier values.

## What is recorded

- Requirement name and part/reference number
- Monthly demand and capacity unit
- Notes
- Required machine, process, material, and certification labels
- Version number, save timestamp, and a user-entered change note

Existing requirements receive a baseline **Version 1** snapshot the first time the version-history feature initializes. Each successful update creates the next version. Invalid updates do not create a version. Deleting a requirement also deletes its version history through SQLite foreign-key cascading.

## API

- `PUT /requirements/{requirement_id}` â€” update the requirement and create a version. The request uses the same fields as requirement creation plus a required `change_note`.
- `GET /requirements/{requirement_id}/versions` â€” list snapshots, newest version first.

The update response includes `current_version`. Each history item contains `version_number`, `change_note`, `changed_at`, and the full `snapshot`.

## Limits

Version history records the data entered into LineFlex. It does not authenticate the person making a change, verify the reason, validate engineering suitability, or establish supplier approval. Editing a requirement does not automatically reopen or invalidate a second-source qualification already linked to that requirement; reviewers must reassess prior decisions before relying on them. Authentication and role-based access remain separate future work.