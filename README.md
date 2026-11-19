# LineFlex

### Manufacturing Flexibility & Second-Source Readiness

LineFlex is an early-stage project exploring how manufacturers can prepare for production changes and supplier disruption through structured capability information, scenario planning, and second-source qualification tracking.

> **Current status:** Working local Factory Capability Registry with a FastAPI backend, factory data-review metadata, and an initial Production Requirements & Capability Matching workflow.

## What works today

- Register, search, view, edit, and delete factory records.
- Record stated monthly capacity, machines, processes, supported materials, and certifications.
- Track user-entered data source, review status, evidence reference, and reviewer label for a factory.
- Create, search, and edit production requirements with a part number, monthly demand, and required capability labels.
- Keep a version history of requirement edits, including full snapshots and change notes.
- Shortlist alternative factories for each requirement and record human decisions with rationale and history.
- Compare required machine, process, material, and certification labels against factory records.
- See preliminary outcomes such as potential match, needs more data, capability gap, below stated capacity, and capacity-unit mismatch.
- Use a Streamlit interface and FastAPI endpoints backed by SQLite.

## Technology

- Python 3.11
- Streamlit
- FastAPI
- SQLite
- Pandas
- Pytest
- Uvicorn

## Run locally

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the Streamlit application:

```powershell
python -m streamlit run app.py
```

Start the API in a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload
```

Open:
- Streamlit: http://localhost:8501
- API documentation: http://127.0.0.1:8000/docs

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/factories` | Create factory |
| GET | `/factories` | List and search factories |
| GET | `/factories/{factory_id}` | Read factory |
| PUT | `/factories/{factory_id}` | Update factory |
| DELETE | `/factories/{factory_id}` | Delete factory |
| GET | `/factories/{factory_id}/review` | Read source and review metadata |
| PUT | `/factories/{factory_id}/review` | Save source, review status, evidence reference, and reviewer label |
| POST | `/requirements` | Create production requirement |
| GET | `/requirements` | List or search requirements |
| GET | `/requirements/{requirement_id}` | Read one production requirement |
| PUT | `/requirements/{requirement_id}` | Edit a requirement and create a version |
| GET | `/requirements/{requirement_id}/versions` | Read requirement version history |
| DELETE | `/requirements/{requirement_id}` | Delete one production requirement |
| GET | `/requirements/{requirement_id}/matches` | Compare requirement with registered factories |
| POST | `/requirements/{requirement_id}/candidates` | Add a factory to a requirement shortlist |
| GET | `/requirements/{requirement_id}/candidates` | List shortlisted factories for a requirement |
| GET | `/candidates/{candidate_id}` | Read a candidate and its decision history |
| PATCH | `/candidates/{candidate_id}/decision` | Record a human shortlist decision |
| GET | `/candidates/{candidate_id}/decisions` | Read candidate decision history |
| DELETE | `/candidates/{candidate_id}` | Remove a candidate from a shortlist |

## Production requirement and capability matching

A requirement can record a name, part/reference number, monthly demand and unit, notes, and required machine, process, material, and certification labels. The first comparison uses exact, case-insensitive text matching against recorded factory capability labels.

Possible outcomes:

- `potential_match`: all entered labels are present and the factory's stated monthly capacity is at least the requested demand in the same unit.
- `needs_more_data`: at least one required capability category has no factory values recorded.
- `capability_gap`: one or more required labels are missing from categories that do have recorded values.
- `below_stated_capacity`: the factory's stated monthly capacity is less than the requested demand.
- `capacity_unit_mismatch`: factory capacity and requirement demand use different units.

A comparison includes category-level matched, missing, and unrecorded details. It is a preliminary screening aid only. It does not calculate free capacity or prove technical equivalence, tolerance compatibility, quality, certification validity, delivery performance, or customer approval. A `potential_match` is not a supplier approval.

## Factory data review metadata

Factory review labels are user-entered: Unverified, Self-declared, Evidence attached, and Reviewed. Evidence references are text references only. The prototype does not upload, inspect, authenticate, or independently verify documents. A Reviewed label records a user's declaration, not LineFlex certification.

## Tests

Run:

```powershell
python -m pytest tests -v
```

The automated suite covers factory CRUD, data-review metadata, requirement storage and search, matching outcomes, missing data, capacity comparisons, input validation, and API behavior. Run it locally before treating a milestone as complete.

## Planned modules

- Notifications and reminders for qualification reviews
- Role-based approval permissions and authenticated reviewer identity
- Reusable qualification checklist templates
- More complete production flexibility scenario planning

## Current limitations

- Factory capacity and capabilities are user-entered and unverified.
- Capability matching uses exact labels; synonyms and engineering equivalence are not inferred.
- Stated monthly capacity is not free or available capacity.
- No automatic engineering, quality, certification, or supplier approval assessment is performed.
- No authentication, roles, multi-user access, or production deployment.
- Editing a requirement does not automatically reopen a linked second-source qualification; review prior decisions before relying on them.
- Market demand and willingness to pay remain unvalidated.

LineFlex is a planning and record-keeping prototype, not a certification or engineering approval system. Any real production transfer requires appropriate engineering checks, supplier-quality review, contractual decisions, and customer approvals.

See [docs/ROADMAP.md](docs/ROADMAP.md) for project progress, [docs/PRODUCTION_REQUIREMENTS.md](docs/PRODUCTION_REQUIREMENTS.md) for the comparison workflow, [docs/REQUIREMENT_VERSION_HISTORY.md](docs/REQUIREMENT_VERSION_HISTORY.md) for requirement editing and snapshots, and [docs/CANDIDATE_SHORTLIST.md](docs/CANDIDATE_SHORTLIST.md) for shortlist decisions.

## Second-source qualification workflow

- Start a qualification by linking one production requirement to one alternative factory.
- Track seven review checks for engineering specifications, process capability, materials, quality/certifications, capacity/lead time, sample inspection, and customer approval.
- Record check status, owner, due date, evidence reference, and review notes.
- Move a fully completed checklist to `Ready for review`; this is not automatic approval.
- Record a named human decision (`Approved`, `Rejected`, or `On hold`) with its rationale and retain decision history. Approval is blocked until every check is `Passed` or `Not applicable`.

The checklist and decisions are user-entered workflow records. Evidence references are not inspected or authenticated, and a recorded approval is not LineFlex certification or proof of technical suitability. See [docs/SECOND_SOURCE_QUALIFICATION.md](docs/SECOND_SOURCE_QUALIFICATION.md).
