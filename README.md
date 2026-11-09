# LineFlex

### Manufacturing Flexibility & Second-Source Readiness

LineFlex is an early-stage project exploring how manufacturers can prepare for production changes and supplier disruption through structured capability information, scenario planning, and second-source qualification tracking.

> **Project status:** Early local prototype. The first Factory Capability Registry is implemented with Streamlit and SQLite. The wider manufacturing-readiness workflow, market differentiation, and demand remain under research.

## What works today

The first prototype provides a local **Factory Capability Registry**:

- Register a factory with its name and location.
- Record stated monthly production capacity and its unit.
- Record machines, processes, supported materials, and certifications.
- View registered factories and their capability details.
- Search factory records by name, city, or state.
- View simple dashboard counts for registered factories, combined stated capacity, and unique processes.

Factory records are stored in a local SQLite database. The current application creates records and displays/searches them; editing and deletion are not implemented yet.

### Run locally

Requirements: Python 3.11 or a compatible Python version supported by the pinned packages.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

### Run the tests

```powershell
python -m pytest tests -v
```

The initial database test suite currently contains four tests covering factory creation/retrieval, city search, empty-name validation, and zero-capacity validation. The local run recorded for this milestone passed all four tests.

## The problem being explored

Manufacturers may need to respond to sudden demand changes, production constraints, or the loss of a critical supplier. Responding can be difficult when factory capabilities, available capacity, alternative suppliers, and qualification records are spread across different systems or documents.

LineFlex explores whether these activities can be brought into one practical workflow.

## Proposed solution

The longer-term concept is a workspace for organizing manufacturing readiness information and planning response actions.

### Planned modules

| Module | Purpose | Status |
|---|---|---|
| Factory Capability Passport | Record machines, processes, materials, certifications, and stated capacity | Initial registry prototype available |
| Production Flexibility Planner | Model basic capacity and production-change scenarios using user-provided data | Planned |
| Second-Source Readiness | Track alternative suppliers and outstanding qualification steps | Planned |
| Qualification Workspace | Organize certificates, inspection records, and approval status | Planned |
| Activation Workflow | Record owners, tasks, and decisions when a change is being considered | Planned |

## What makes the concept worth exploring?

The project will investigate the workflow gap between:
- knowing that an alternative factory or supplier exists;
- understanding whether it can meet a particular part or process requirement; and
- tracking the evidence and customer approvals needed before a production switch.

LineFlex will not assume that a supplier is interchangeable simply because it has similar equipment or spare capacity. Technical compatibility and customer-specific approval remain human-controlled decisions.

## Intended users

- Manufacturing operations and production-planning teams
- Procurement and supplier-development teams
- Component manufacturers and their customers
- Business-continuity and supply-chain risk teams

## Technology

- Python 3.11 for application logic
- Streamlit for the initial user interface
- SQLite for local prototype storage
- Pandas for tabular display
- Pytest for automated tests

FastAPI and PostgreSQL remain possible later options; they are not part of the current prototype.

The prototype is designed to run locally on a standard laptop. No GPU or paid cloud service is required for the current feature.

## Current limitations

- Capacity is user-entered information; the application does not validate actual available or free capacity.
- The prototype does not verify machines, processes, materials, certificates, or supplier claims.
- No engineering compatibility assessment, supplier approval, audit, or customer qualification is performed.
- Editing and deleting factory records are not implemented.
- Authentication, user roles, multi-user access, and deployment are not implemented.
- The prototype uses sample/demo information only. Do not enter confidential factory or customer data.

## Development roadmap

See [ROADMAP.md](docs/ROADMAP.md) for completed and remaining milestones.

## Responsible use

LineFlex is a planning and record-keeping concept. It is not a certification authority, engineering approval system, or guarantee of supplier suitability. Any real production transfer would require the relevant technical checks, audits, contractual decisions, and customer approvals.

Market demand, differentiation, and willingness to pay have not yet been validated with customers.

## Repository structure

```text
LineFlex/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
├── docs/
│   ├── PRODUCT_BRIEF.md
│   ├── RESEARCH_PLAN.md
│   └── ROADMAP.md
└── tests/
    └── test_database.py
```

## Contributing

This is currently an individual research and development project. Issues and constructive feedback are welcome.

## License

No license has been selected yet. Until a license is added, normal copyright restrictions apply; reuse is not automatically permitted.
