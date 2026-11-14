# Production Requirements & Capability Matching

## Purpose

This first workflow records what a part or production job requires and compares those requirements with factory capability information already stored in LineFlex.

## Requirement fields

- Requirement name
- Part number or reference (optional)
- Monthly demand and capacity unit
- Required machines
- Required processes
- Required materials
- Required certifications
- Notes (optional)

## Matching behavior

The comparison checks required labels against the factory's recorded labels using exact, case-insensitive text comparison. It does not assume synonyms are equivalent.

For each required category, the result is one of:

- `match`: every required label is present in the factory record.
- `partial`: some labels are present and some are missing.
- `no_match`: the category has recorded values, but none of the required labels are present.
- `not_recorded`: the factory has no values recorded for a required category.
- `not_required`: the requirement has no entries for that category.

The capacity check compares monthly demand with the factory's user-entered stated monthly capacity only when the units match. It returns `meets_stated_capacity`, `below_stated_capacity`, or `capacity_unit_mismatch`.

Overall outcomes are `potential_match`, `needs_more_data`, `capability_gap`, `below_stated_capacity`, and `capacity_unit_mismatch`.

## API

- `POST /requirements`
- `GET /requirements`
- `GET /requirements/{requirement_id}`
- `DELETE /requirements/{requirement_id}`
- `GET /requirements/{requirement_id}/matches`

## Safety and interpretation

A `potential_match` is only a shortlist signal. The system does not know whether stated capacity is free, whether the exact part can be manufactured to drawing/tolerance requirements, whether process parameters are equivalent, or whether certificates and supplier claims are valid. Human engineering, supplier-quality, procurement, and customer review is required before any production transfer.

The initial implementation uses synthetic/demo data and local SQLite storage. It does not implement multi-user access, requirement versioning, or final approval workflow.
