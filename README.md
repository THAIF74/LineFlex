# LineFlex

### Manufacturing Flexibility & Second-Source Readiness

LineFlex is an early-stage project exploring how manufacturers can prepare for production changes and supplier disruption through structured capability information, scenario planning, and second-source qualification tracking.

> **Project status:** Research and product definition. The MVP has not been implemented yet.

## The problem being explored

Manufacturers may need to respond to sudden demand changes, production constraints, or the loss of a critical supplier. Responding can be difficult when factory capabilities, available capacity, alternative suppliers, and qualification records are spread across different systems or documents.

LineFlex explores whether these activities can be brought into one practical workflow.

## Proposed solution

The initial concept is a workspace for organizing manufacturing readiness information and planning response actions.

### Planned modules

| Module | Purpose |
|---|---|
| Factory Capability Passport | Record machines, processes, materials, certifications, and stated capacity |
| Production Flexibility Planner | Model basic capacity and production-change scenarios using user-provided data |
| Second-Source Readiness | Track alternative suppliers and outstanding qualification steps |
| Qualification Workspace | Organize certificates, inspection records, and approval status |
| Activation Workflow | Record owners, tasks, and decisions when a change is being considered |

These are proposed capabilities, not features available in a working product today.

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

## Proposed technology

The implementation stack will be selected and tested during the architecture phase. The current proposal is:

- Python for application logic
- FastAPI for a backend API
- Streamlit for an initial user interface
- SQLite for the first local prototype, with PostgreSQL as a later option
- Pandas for structured data handling

The first MVP is intended to run on a standard laptop and use sample data. No GPU or paid cloud service should be required for the initial prototype.

## Development roadmap

- [x] Create the project repository and initial documentation
- [ ] Complete competitor and workflow research
- [ ] Define the MVP scope and data model
- [ ] Build a sample-data capability registry
- [ ] Implement a basic capacity scenario planner
- [ ] Implement second-source qualification tracking
- [ ] Add tests and documentation
- [ ] Evaluate deployment options

See [ROADMAP.md](docs/ROADMAP.md) for the planned milestones.

## Responsible use and limitations

LineFlex is a planning and record-keeping concept. It is not a certification authority, engineering approval system, or guarantee of supplier suitability. Any real production transfer would require the relevant technical checks, audits, contractual decisions, and customer approvals.

The project is in its research stage. Market demand, differentiation, and willingness to pay have not yet been validated with customers.

## Repository structure

```text
LineFlex/
├── README.md
├── .gitignore
└── docs/
    ├── PRODUCT_BRIEF.md
    ├── RESEARCH_PLAN.md
    └── ROADMAP.md
```

## Contributing

This is currently an individual research and development project. Issues and constructive feedback are welcome.

## License

No license has been selected yet. Until a license is added, normal copyright restrictions apply; reuse is not automatically permitted.
